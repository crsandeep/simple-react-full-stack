# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Utilities for running Daisy builds on Google Container Builder."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import time

from apitools.base.py import encoding
from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.api_lib.cloudbuild import logs as cb_logs
from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.api_lib.compute import instance_utils
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.api_lib.services import enable_api as services_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.cloudbuild import execution
from googlecloudsdk.command_lib.compute.sole_tenancy import util as sole_tenancy_util
from googlecloudsdk.command_lib.projects import util as projects_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io
import six

_IMAGE_IMPORT_BUILDER = 'gcr.io/compute-image-tools/gce_vm_image_import:{}'
_IMAGE_EXPORT_BUILDER = 'gcr.io/compute-image-tools/gce_vm_image_export:{}'
_OVF_IMPORT_BUILDER = 'gcr.io/compute-image-tools/gce_ovf_import:{}'

_DEFAULT_BUILDER_VERSION = 'release'

ROLE_COMPUTE_STORAGE_ADMIN = 'roles/compute.storageAdmin'
ROLE_STORAGE_OBJECT_VIEWER = 'roles/storage.objectViewer'
ROLE_STORAGE_OBJECT_ADMIN = 'roles/storage.objectAdmin'
ROLE_COMPUTE_ADMIN = 'roles/compute.admin'
ROLE_IAM_SERVICE_ACCOUNT_USER = 'roles/iam.serviceAccountUser'
ROLE_IAM_SERVICE_ACCOUNT_TOKEN_CREATOR = 'roles/iam.serviceAccountTokenCreator'
ROLE_EDITOR = 'roles/editor'

IMPORT_ROLES_FOR_COMPUTE_SERVICE_ACCOUNT = frozenset({
    ROLE_COMPUTE_STORAGE_ADMIN,
    ROLE_STORAGE_OBJECT_VIEWER,
})

EXPORT_ROLES_FOR_COMPUTE_SERVICE_ACCOUNT = frozenset({
    ROLE_COMPUTE_STORAGE_ADMIN,
    ROLE_STORAGE_OBJECT_ADMIN,
})

IMPORT_ROLES_FOR_CLOUDBUILD_SERVICE_ACCOUNT = frozenset({
    ROLE_COMPUTE_ADMIN,
    ROLE_IAM_SERVICE_ACCOUNT_TOKEN_CREATOR,
    ROLE_IAM_SERVICE_ACCOUNT_USER,
})

EXPORT_ROLES_FOR_CLOUDBUILD_SERVICE_ACCOUNT = frozenset({
    ROLE_COMPUTE_ADMIN,
    ROLE_IAM_SERVICE_ACCOUNT_TOKEN_CREATOR,
    ROLE_IAM_SERVICE_ACCOUNT_USER,
})


class FilteredLogTailer(cb_logs.LogTailer):
  """Subclass of LogTailer that allows for filtering."""

  def _PrintLogLine(self, text):
    """Override PrintLogLine method to use self.filter."""
    if self.filter:
      output_lines = text.splitlines()
      for line in output_lines:
        for match in self.filter:
          if line.startswith(match):
            self.out.Print(line)
            break
    else:
      self.out.Print(text)


class CloudBuildClientWithFiltering(cb_logs.CloudBuildClient):
  """Subclass of CloudBuildClient that allows filtering."""

  def StreamWithFilter(self, build_ref, backoff, output_filter=None):
    """Stream the logs for a build using whitelist filter.

    Args:
      build_ref: Build reference, The build whose logs shall be streamed.
      backoff: A function that takes the current elapsed time
        and returns the next sleep length. Both are in seconds.
      output_filter: List of strings, The output will only be shown if the line
        starts with one of the strings in the list.

    Raises:
      NoLogsBucketException: If the build does not specify a logsBucket.

    Returns:
      Build message, The completed or terminated build as read for the final
      poll.
    """
    build = self.GetBuild(build_ref)
    log_tailer = FilteredLogTailer.FromBuild(build)
    log_tailer.filter = output_filter

    statuses = self.messages.Build.StatusValueValuesEnum
    working_statuses = [
        statuses.QUEUED,
        statuses.WORKING,
    ]

    seconds_between_poll = backoff(0)
    seconds_elapsed = 0

    while build.status in working_statuses:
      log_tailer.Poll()
      time.sleep(seconds_between_poll)
      build = self.GetBuild(build_ref)
      seconds_elapsed += seconds_between_poll
      seconds_between_poll = backoff(seconds_elapsed)

    # Poll the logs one final time to ensure we have everything. We know this
    # final poll will get the full log contents because GCS is strongly
    # consistent and Container Builder waits for logs to finish pushing before
    # marking the build complete.
    log_tailer.Poll(is_last=True)

    return build


class FailedBuildException(exceptions.Error):
  """Exception for builds that did not succeed."""

  def __init__(self, build):
    super(FailedBuildException,
          self).__init__('build {id} completed with status "{status}"'.format(
              id=build.id, status=build.status))


class SubnetException(exceptions.Error):
  """Exception for subnet related errors."""


class ImageOperation(object):
  """Enum representing image operation."""
  IMPORT = 'import'
  EXPORT = 'export'


def AddCommonDaisyArgs(parser, add_log_location=True, operation='a build'):
  """Common arguments for Daisy builds."""

  if add_log_location:
    parser.add_argument(
        '--log-location',
        help='Directory in Cloud Storage to hold build logs. If not '
        'set, ```gs://<project num>.cloudbuild-logs.googleusercontent.com/``` '
        'is created and used.',
    )

  parser.add_argument(
      '--timeout',
      type=arg_parsers.Duration(),
      default='2h',
      help=("""\
          Maximum time {} can last before it fails as "TIMEOUT".
          For example, specifying `2h` fails the process after 2 hours.
          See $ gcloud topic datetimes for information about duration formats.
          """).format(operation))
  base.ASYNC_FLAG.AddToParser(parser)


def AddExtraCommonDaisyArgs(parser):
  """Extra common arguments for Daisy builds."""

  parser.add_argument(
      '--docker-image-tag',
      default=_DEFAULT_BUILDER_VERSION,
      hidden=True,
      help="""\
          Specify which docker image tag (of tools from compute-image-tools)
          should be used for this command. By default it's "release", while
          "latest" is supported as well. There may be more versions supported in
          the future.
          """
  )


def AddOVFSourceUriArg(parser):
  """Adds OVF Source URI arg."""
  parser.add_argument(
      '--source-uri',
      required=True,
      help=('Cloud Storage path to one of:\n  OVF descriptor\n  '
            'OVA file\n  Directory with OVF package'))


def AddGuestEnvironmentArg(parser, resource='instance'):
  """Adds Google Guest environment arg."""
  parser.add_argument(
      '--guest-environment',
      action='store_true',
      default=True,
      help='The guest environment will be installed on the {}.'.format(
          resource)
  )


def _CheckIamPermissions(project_id, cloudbuild_service_account_roles,
                         compute_service_account_roles):
  """Check for needed IAM permissions and prompt to add if missing.

  Args:
    project_id: A string with the id of the project.
    cloudbuild_service_account_roles: A set of roles required for cloudbuild
      service account.
    compute_service_account_roles: A set of roles required for compute service
      account.
  """
  project = projects_api.Get(project_id)
  # If the user's project doesn't have cloudbuild enabled yet, then the service
  # account won't even exist. If so, then ask to enable it before continuing.
  # Also prompt them to enable Stackdriver Logging if they haven't yet.
  expected_services = ['cloudbuild.googleapis.com', 'logging.googleapis.com',
                       'compute.googleapis.com']
  for service_name in expected_services:
    if not services_api.IsServiceEnabled(project.projectId, service_name):
      # TODO(b/112757283): Split this out into a separate library.
      prompt_message = (
          'The "{0}" service is not enabled for this project. '
          'It is required for this operation.\n').format(service_name)
      console_io.PromptContinue(
          prompt_message,
          'Would you like to enable this service?',
          throw_if_unattended=True,
          cancel_on_no=True)
      services_api.EnableService(project.projectId, service_name)

  build_account = 'serviceAccount:{0}@cloudbuild.gserviceaccount.com'.format(
      project.projectNumber)
  # https://cloud.google.com/compute/docs/access/service-accounts#default_service_account
  compute_account = (
      'serviceAccount:{0}-compute@developer.gserviceaccount.com'.format(
          project.projectNumber))

  # Now that we're sure the service account exists, actually check permissions.
  try:
    policy = projects_api.GetIamPolicy(project_id)
  except apitools_exceptions.HttpForbiddenError:
    log.warning(
        'Your account does not have permission to check roles for the '
        'service account {0}. If import fails, '
        'ensure "{0}" has the roles "{1}" and "{2}" has the roles "{3}" before '
        'retrying.'.format(build_account, cloudbuild_service_account_roles,
                           compute_account, compute_service_account_roles))
    return

  _VerifyRolesAndPromptIfMissing(project_id, build_account,
                                 _CurrentRolesForAccount(policy, build_account),
                                 cloudbuild_service_account_roles)

  current_compute_account_roles = _CurrentRolesForAccount(
      policy, compute_account)

  # By default, the Compute Engine service account has the role `roles/editor`
  # applied to it, which is sufficient for import and export. If that's not
  # present, then request the minimal number of permissions.
  if ROLE_EDITOR not in current_compute_account_roles:
    _VerifyRolesAndPromptIfMissing(
        project_id, compute_account, current_compute_account_roles,
        compute_service_account_roles)


def _VerifyRolesAndPromptIfMissing(project_id, account, applied_roles,
                                   required_roles):
  """Check for IAM permissions for an account and prompt to add if missing.

  Args:
    project_id: A string with the id of the project.
    account: A string with the identifier of an account.
    applied_roles: A set of strings containing the current roles for the
      account.
    required_roles: A set of strings containing the required roles for the
      account. If a role isn't found, then the user is prompted to add the role.
  """
  # If there were unsatisfied roles, then prompt the user to add them.
  try:
    missing_roles = _FindMissingRoles(applied_roles, required_roles)
  except apitools_exceptions.HttpForbiddenError:
    missing_roles = required_roles - applied_roles

  if missing_roles:
    ep_table = ['{0} {1}'.format(role, account) for role in missing_roles]
    prompt_message = (
        'The following IAM permissions are needed for this operation:\n'
        '[{0}]\n'.format('\n'.join(ep_table)))
    console_io.PromptContinue(
        message=prompt_message,
        prompt_string='Would you like to add the permissions',
        throw_if_unattended=True,
        cancel_on_no=False)

    for role in sorted(missing_roles):
      log.info('Adding [{0}] to [{1}]'.format(account, role))
      try:
        projects_api.AddIamPolicyBinding(project_id, account, role)
      except apitools_exceptions.HttpForbiddenError:
        log.warning(
            'Your account does not have permission to add roles to the '
            'service account {0}. If import fails, '
            'ensure "{0}" has the roles "{1}" before retrying.'.format(
                account, required_roles))
        return


def _FindMissingRoles(applied_roles, required_roles):
  """Check which required roles were not covered by given roles.

  Args:
    applied_roles: A set of strings containing the current roles for the
      account.
    required_roles: A set of strings containing the required roles for the
      account.

  Returns:
    A set of missing roles that is not covered.
  """
  # A quick check without checking detailed permissions by IAM API.
  if required_roles.issubset(applied_roles):
    return None

  iam_messages = apis.GetMessagesModule('iam', 'v1')
  required_role_permissions = {}
  required_permissions = set()
  applied_permissions = set()
  unsatisfied_roles = set()
  for role in sorted(required_roles):
    request = iam_messages.IamRolesGetRequest(name=role)
    role_permissions = set(apis.GetClientInstance(
        'iam', 'v1').roles.Get(request).includedPermissions)
    required_role_permissions[role] = role_permissions
    required_permissions = required_permissions.union(role_permissions)

  for applied_role in sorted(applied_roles):
    request = iam_messages.IamRolesGetRequest(name=applied_role)
    applied_role_permissions = set(apis.GetClientInstance(
        'iam', 'v1').roles.Get(request).includedPermissions)
    applied_permissions = applied_permissions.union(
        applied_role_permissions)

  unsatisfied_permissions = required_permissions - applied_permissions
  for role in required_roles:
    if unsatisfied_permissions.intersection(required_role_permissions[role]):
      unsatisfied_roles.add(role)

  return unsatisfied_roles


def _CurrentRolesForAccount(project_iam_policy, account):
  """Returns a set containing the roles for `account`.

  Args:
    project_iam_policy: The response from GetIamPolicy.
    account: A string with the identifier of an account.
  """
  return set(binding.role
             for binding in project_iam_policy.bindings
             if account in binding.members)


def _CreateCloudBuild(build_config, client, messages):
  """Create a build in cloud build.

  Args:
    build_config: A cloud build Build message.
    client: The cloud build api client.
    messages: The cloud build api messages module.

  Returns:
    Tuple containing a cloud build build object and the resource reference
    for that build.
  """
  log.debug('submitting build: {0}'.format(repr(build_config)))
  op = client.projects_builds.Create(
      messages.CloudbuildProjectsBuildsCreateRequest(
          build=build_config, projectId=properties.VALUES.core.project.Get()))
  json = encoding.MessageToJson(op.metadata)
  build = encoding.JsonToMessage(messages.BuildOperationMetadata, json).build

  build_ref = resources.REGISTRY.Create(
      collection='cloudbuild.projects.builds',
      projectId=build.projectId,
      id=build.id)

  log.CreatedResource(build_ref)

  if build.logUrl:
    log.status.Print('Logs are available at [{0}].'.format(build.logUrl))
  else:
    log.status.Print('Logs are available in the Cloud Console.')

  return build, build_ref


def GetDaisyBucketName(bucket_location=None):
  """Determine bucket name for daisy.

  Args:
    bucket_location: str, specified bucket location.

  Returns:
    str, bucket name for daisy.
  """
  project = properties.VALUES.core.project.GetOrFail()
  safe_project = project.replace(':', '-')
  safe_project = safe_project.replace('.', '-')
  bucket_name = '{0}-daisy-bkt'.format(safe_project)
  if bucket_location:
    bucket_name = '{0}-{1}'.format(bucket_name, bucket_location).lower()
  safe_bucket_name = _GetSafeBucketName(bucket_name)
  # TODO (b/117668144): Make Daisy scratch bucket ACLs same as
  # source/destination bucket
  return safe_bucket_name


def _GetSafeBucketName(bucket_name):
  # Rules are from https://cloud.google.com/storage/docs/naming.

  # Bucket name can't contain "google".
  bucket_name = bucket_name.replace('google', 'go-ogle')

  # Bucket name can't start with "goog". Workaround for b/128691621
  bucket_name = bucket_name[:4].replace('goog', 'go-og') + bucket_name[4:]

  return bucket_name


def GetSubnetRegion():
  """Gets region from global properties/args that should be used for subnet arg.

  Returns:
    str, region
  Raises:
    SubnetException: if region couldn't be inferred.
  """
  if properties.VALUES.compute.zone.Get():
    return utils.ZoneNameToRegionName(properties.VALUES.compute.zone.Get())
  elif properties.VALUES.compute.region.Get():
    return properties.VALUES.compute.region.Get()

  raise SubnetException('Region or zone should be specified.')


def AppendNetworkAndSubnetArgs(args, builder_args):
  """Extracts network/subnet out of CLI args and append for importer.

  Args:
    args: list of str, CLI args that might contain network/subnet args.
    builder_args: list of str, args for builder.
  """
  if args.subnet:
    AppendArg(builder_args, 'subnet', args.subnet.lower())

  if args.network:
    AppendArg(builder_args, 'network', args.network.lower())


def RunImageImport(args,
                   import_args,
                   tags,
                   output_filter,
                   docker_image_tag=_DEFAULT_BUILDER_VERSION):
  """Run a build over gce_vm_image_import on Google Cloud Builder.

  Args:
    args: An argparse namespace. All the arguments that were provided to this
      command invocation.
    import_args: A list of key-value pairs to pass to importer.
    tags: A list of strings for adding tags to the Argo build.
    output_filter: A list of strings indicating what lines from the log should
      be output. Only lines that start with one of the strings in output_filter
      will be displayed.
    docker_image_tag: Specified docker image tag.

  Returns:
    A build object that either streams the output or is displayed as a
    link to the build.

  Raises:
    FailedBuildException: If the build is completed and not 'SUCCESS'.
  """
  builder = _IMAGE_IMPORT_BUILDER.format(docker_image_tag)
  return RunImageCloudBuild(args, builder, import_args, tags, output_filter,
                            IMPORT_ROLES_FOR_CLOUDBUILD_SERVICE_ACCOUNT,
                            IMPORT_ROLES_FOR_COMPUTE_SERVICE_ACCOUNT)


def RunImageExport(args,
                   export_args,
                   tags,
                   output_filter,
                   docker_image_tag=_DEFAULT_BUILDER_VERSION):
  """Run a build over gce_vm_image_export on Google Cloud Builder.

  Args:
    args: An argparse namespace. All the arguments that were provided to this
      command invocation.
    export_args: A list of key-value pairs to pass to exporter.
    tags: A list of strings for adding tags to the Argo build.
    output_filter: A list of strings indicating what lines from the log should
      be output. Only lines that start with one of the strings in output_filter
      will be displayed.
    docker_image_tag: Specified docker image tag.

  Returns:
    A build object that either streams the output or is displayed as a
    link to the build.

  Raises:
    FailedBuildException: If the build is completed and not 'SUCCESS'.
  """
  builder = _IMAGE_EXPORT_BUILDER.format(docker_image_tag)
  return RunImageCloudBuild(args, builder, export_args, tags, output_filter,
                            EXPORT_ROLES_FOR_CLOUDBUILD_SERVICE_ACCOUNT,
                            EXPORT_ROLES_FOR_COMPUTE_SERVICE_ACCOUNT)


def RunImageCloudBuild(args, builder, builder_args, tags, output_filter,
                       cloudbuild_service_account_roles,
                       compute_service_account_roles):
  """Run a build related to image on Google Cloud Builder.

  Args:
    args: An argparse namespace. All the arguments that were provided to this
      command invocation.
    builder: Path to builder image.
    builder_args: A list of key-value pairs to pass to builder.
    tags: A list of strings for adding tags to the Argo build.
    output_filter: A list of strings indicating what lines from the log should
      be output. Only lines that start with one of the strings in output_filter
      will be displayed.
    cloudbuild_service_account_roles: roles required for cloudbuild service
      account.
    compute_service_account_roles: roles required for compute service account.

  Returns:
    A build object that either streams the output or is displayed as a
    link to the build.

  Raises:
    FailedBuildException: If the build is completed and not 'SUCCESS'.
  """
  project_id = projects_util.ParseProject(
      properties.VALUES.core.project.GetOrFail())

  _CheckIamPermissions(project_id, cloudbuild_service_account_roles,
                       compute_service_account_roles)

  return _RunCloudBuild(args, builder, builder_args,
                        ['gce-daisy'] + tags, output_filter, args.log_location)


def GetDaisyTimeout(args):
  # Make Daisy time out before gcloud by shaving off 2% from the timeout time,
  # up to a max of 5m (300s).
  two_percent = int(args.timeout * 0.02)
  daisy_timeout = args.timeout - min(two_percent, 300)
  return daisy_timeout


def _RunCloudBuild(args,
                   builder,
                   build_args,
                   build_tags=None,
                   output_filter=None,
                   log_location=None,
                   backoff=lambda elapsed: 1):
  """Run a build with a specific builder on Google Cloud Builder.

  Args:
    args: an argparse namespace. All the arguments that were provided to this
      command invocation.
    builder: path to builder image
    build_args: args to be sent to builder
    build_tags: tags to be attached to the build
    output_filter: A list of strings indicating what lines from the log should
      be output. Only lines that start with one of the strings in output_filter
      will be displayed.
    log_location: GCS path to directory where logs will be stored.
    backoff: A function that takes the current elapsed time and returns
      the next sleep length. Both are in seconds.

  Returns:
    A build object that either streams the output or is displayed as a
    link to the build.

  Raises:
    FailedBuildException: If the build is completed and not 'SUCCESS'.
  """
  client = cloudbuild_util.GetClientInstance()
  messages = cloudbuild_util.GetMessagesModule()

  # Create the build request.
  build_config = messages.Build(
      steps=[
          messages.BuildStep(
              name=builder,
              args=build_args,
          ),
      ],
      tags=build_tags,
      timeout='{0}s'.format(args.timeout),
  )
  if log_location:
    gcs_log_dir = resources.REGISTRY.Parse(
        args.log_location, collection='storage.objects')

    build_config.logsBucket = ('gs://{0}/{1}'.format(gcs_log_dir.bucket,
                                                     gcs_log_dir.object))

  # Start the build.
  build, build_ref = _CreateCloudBuild(build_config, client, messages)

  # If the command is run --async, we just print out a reference to the build.
  if args.async_:
    return build

  mash_handler = execution.MashHandler(
      execution.GetCancelBuildHandler(client, messages, build_ref))

  # Otherwise, logs are streamed from GCS.
  with execution_utils.CtrlCSection(mash_handler):
    build = CloudBuildClientWithFiltering(client, messages).StreamWithFilter(
        build_ref, backoff, output_filter=output_filter)

  if build.status == messages.Build.StatusValueValuesEnum.TIMEOUT:
    log.status.Print(
        'Your build timed out. Use the [--timeout=DURATION] flag to change '
        'the timeout threshold.')

  if build.status != messages.Build.StatusValueValuesEnum.SUCCESS:
    raise FailedBuildException(build)

  return build


def RunOVFImportBuild(args, compute_client, instance_name, source_uri,
                      no_guest_environment, can_ip_forward, deletion_protection,
                      description, labels, machine_type, network, network_tier,
                      subnet, private_network_ip, no_restart_on_failure, os,
                      tags, zone, project, output_filter,
                      compute_release_track, hostname):
  """Run a OVF into VM instance import build on Google Cloud Build.

  Args:
    args: an argparse namespace. All the arguments that were provided to this
      command invocation.
    compute_client: Google Compute Engine client.
    instance_name: Name of the instance to be imported.
    source_uri: A GCS path to OVA or OVF package.
    no_guest_environment: If set to True, Google Guest Environment won't be
      installed on the boot disk of the VM.
    can_ip_forward: If set to True, allows the instances to send and receive
      packets with non-matching destination or source IP addresses.
    deletion_protection: Enables deletion protection for the instance.
    description: Specifies a textual description of the instances.
    labels: List of label KEY=VALUE pairs to add to the instance.
    machine_type: Specifies the machine type used for the instances.
    network: Specifies the network that the instances will be part of.
    network_tier: Specifies the network tier of the interface. NETWORK_TIER must
      be one of: PREMIUM, STANDARD.
    subnet: Specifies the subnet that the instances will be part of.
    private_network_ip: Specifies the RFC1918 IP to assign to the instance.
    no_restart_on_failure: The instances will NOT be restarted if they are
      terminated by Compute Engine.
    os: Specifies the OS of the boot disk being imported.
    tags: A list of strings for adding tags to the Argo build.
    zone: The GCP zone to tell Daisy to do work in. If unspecified, defaults to
      wherever the Argo runner happens to be.
    project: The Google Cloud Platform project name to use for OVF import.
    output_filter: A list of strings indicating what lines from the log should
      be output. Only lines that start with one of the strings in output_filter
      will be displayed.
    compute_release_track: release track to be used for Compute API calls. One
      of - "alpha", "beta" or ""
    hostname: hostname of the instance to be imported

  Returns:
    A build object that either streams the output or is displayed as a
    link to the build.

  Raises:
    FailedBuildException: If the build is completed and not 'SUCCESS'.
  """
  project_id = projects_util.ParseProject(
      properties.VALUES.core.project.GetOrFail())

  _CheckIamPermissions(project_id, IMPORT_ROLES_FOR_CLOUDBUILD_SERVICE_ACCOUNT,
                       IMPORT_ROLES_FOR_COMPUTE_SERVICE_ACCOUNT)

  # Make OVF import time-out before gcloud by shaving off 2% from the timeout
  # time, up to a max of 5m (300s).
  two_percent = int(args.timeout * 0.02)
  ovf_import_timeout = args.timeout - min(two_percent, 300)

  ovf_importer_args = []
  AppendArg(ovf_importer_args, 'instance-names', instance_name)
  AppendArg(ovf_importer_args, 'client-id', 'gcloud')
  AppendArg(ovf_importer_args, 'ovf-gcs-path', source_uri)
  AppendBoolArg(ovf_importer_args, 'no-guest-environment',
                no_guest_environment)
  AppendBoolArg(ovf_importer_args, 'can-ip-forward', can_ip_forward)
  AppendBoolArg(ovf_importer_args, 'deletion-protection', deletion_protection)
  AppendArg(ovf_importer_args, 'description', description)
  if labels:
    AppendArg(ovf_importer_args, 'labels',
              ','.join(['{}={}'.format(k, v) for k, v in labels.items()]))
  AppendArg(ovf_importer_args, 'machine-type', machine_type)
  AppendArg(ovf_importer_args, 'network', network)
  AppendArg(ovf_importer_args, 'network-tier', network_tier)
  AppendArg(ovf_importer_args, 'subnet', subnet)
  AppendArg(ovf_importer_args, 'private-network-ip', private_network_ip)
  AppendBoolArg(ovf_importer_args, 'no-restart-on-failure',
                no_restart_on_failure)
  AppendArg(ovf_importer_args, 'os', os)
  if tags:
    AppendArg(ovf_importer_args, 'tags', ','.join(tags))
  AppendArg(ovf_importer_args, 'zone', zone)
  AppendArg(ovf_importer_args, 'timeout', ovf_import_timeout, '-{0}={1}s')
  AppendArg(ovf_importer_args, 'project', project)
  _AppendNodeAffinityLabelArgs(ovf_importer_args, args, compute_client.messages)
  if compute_release_track:
    AppendArg(ovf_importer_args, 'release-track', compute_release_track)
  AppendArg(ovf_importer_args, 'hostname', hostname)

  build_tags = ['gce-ovf-import']

  backoff = lambda elapsed: 2 if elapsed < 30 else 15

  return _RunCloudBuild(args, _OVF_IMPORT_BUILDER.format(args.docker_image_tag),
                        ovf_importer_args, build_tags, output_filter,
                        backoff=backoff)


def RunMachineImageOVFImportBuild(args, output_filter, compute_release_track):
  """Run a OVF into VM instance import build on Google Cloud Builder.

  Args:
    args: an argparse namespace. All the arguments that were provided to this
      command invocation.
    output_filter: A list of strings indicating what lines from the log should
      be output. Only lines that start with one of the strings in output_filter
      will be displayed.
    compute_release_track: release track to be used for Compute API calls. One
      of - "alpha", "beta" or ""

  Returns:
    A build object that either streams the output or is displayed as a
    link to the build.

  Raises:
    FailedBuildException: If the build is completed and not 'SUCCESS'.
  """
  project_id = projects_util.ParseProject(
      properties.VALUES.core.project.GetOrFail())

  _CheckIamPermissions(project_id, IMPORT_ROLES_FOR_CLOUDBUILD_SERVICE_ACCOUNT,
                       IMPORT_ROLES_FOR_COMPUTE_SERVICE_ACCOUNT)

  # Make OVF import time-out before gcloud by shaving off 2% from the timeout
  # time, up to a max of 5m (300s).
  two_percent = int(args.timeout * 0.02)
  ovf_import_timeout = args.timeout - min(two_percent, 300)

  machine_type = None
  if args.machine_type or args.custom_cpu or args.custom_memory:
    machine_type = instance_utils.InterpretMachineType(
        machine_type=args.machine_type,
        custom_cpu=args.custom_cpu,
        custom_memory=args.custom_memory,
        ext=getattr(args, 'custom_extensions', None),
        vm_type=getattr(args, 'custom_vm_type', None))

  ovf_importer_args = []
  AppendArg(ovf_importer_args, 'machine-image-name', args.IMAGE)
  AppendArg(ovf_importer_args, 'machine-image-storage-location',
            args.storage_location)
  AppendArg(ovf_importer_args, 'client-id', 'gcloud')
  AppendArg(ovf_importer_args, 'ovf-gcs-path', args.source_uri)
  AppendBoolArg(ovf_importer_args, 'no-guest-environment',
                not args.guest_environment)
  AppendBoolArg(ovf_importer_args, 'can-ip-forward', args.can_ip_forward)
  AppendArg(ovf_importer_args, 'description', args.description)
  if args.labels:
    AppendArg(ovf_importer_args, 'labels',
              ','.join(['{}={}'.format(k, v) for k, v in args.labels.items()]))
  AppendArg(ovf_importer_args, 'machine-type', machine_type)
  AppendArg(ovf_importer_args, 'network', args.network)
  AppendArg(ovf_importer_args, 'network-tier', args.network_tier)
  AppendArg(ovf_importer_args, 'subnet', args.subnet)
  AppendBoolArg(ovf_importer_args, 'no-restart-on-failure',
                not args.restart_on_failure)
  AppendArg(ovf_importer_args, 'os', args.os)
  if args.tags:
    AppendArg(ovf_importer_args, 'tags', ','.join(args.tags))
  AppendArg(ovf_importer_args, 'zone', properties.VALUES.compute.zone.Get())
  AppendArg(ovf_importer_args, 'timeout', ovf_import_timeout, '-{0}={1}s')
  AppendArg(ovf_importer_args, 'project', args.project)
  if compute_release_track:
    AppendArg(ovf_importer_args, 'release-track', compute_release_track)

  build_tags = ['gce-ovf-machine-image-import']

  backoff = lambda elapsed: 2 if elapsed < 30 else 15

  return _RunCloudBuild(args, _OVF_IMPORT_BUILDER.format(args.docker_image_tag),
                        ovf_importer_args, build_tags, output_filter,
                        backoff=backoff)


def _AppendNodeAffinityLabelArgs(
    ovf_importer_args, args, compute_client_messages):
  node_affinities = sole_tenancy_util.GetSchedulingNodeAffinityListFromArgs(
      args, compute_client_messages)
  for node_affinity in node_affinities:
    AppendArg(ovf_importer_args, 'node-affinity-label',
              _BuildOvfImporterNodeAffinityFlagValue(node_affinity))


def _BuildOvfImporterNodeAffinityFlagValue(node_affinity):
  node_affinity_flag = node_affinity.key + ',' + six.text_type(
      node_affinity.operator)
  for value in node_affinity.values:
    node_affinity_flag += ',' + value
  return node_affinity_flag


def AppendArg(args, name, arg, format_pattern='-{0}={1}'):
  if arg:
    args.append(format_pattern.format(name, arg))


def AppendBoolArg(args, name, arg=True):
  AppendArg(args, name, arg, '-{0}')


def MakeGcsUri(uri):
  """Creates Google Cloud Storage URI for an object or a path.

  Args:
    uri: a string to a Google Cloud Storage object or a path. Can be a gs:// or
         an https:// variant.

  Returns:
    Google Cloud Storage URI for an object or a path.
  """
  obj_ref = resources.REGISTRY.Parse(uri)
  if hasattr(obj_ref, 'object'):
    return 'gs://{0}/{1}'.format(obj_ref.bucket, obj_ref.object)
  else:
    return 'gs://{0}/'.format(obj_ref.bucket)


def MakeGcsObjectUri(uri):
  """Creates Google Cloud Storage URI for an object.

  Raises storage_util.InvalidObjectNameError if a path contains only bucket
  name.

  Args:
    uri: a string to a Google Cloud Storage object. Can be a gs:// or
         an https:// variant.

  Returns:
    Google Cloud Storage URI for an object.
  """
  obj_ref = resources.REGISTRY.Parse(uri)
  if hasattr(obj_ref, 'object'):
    return 'gs://{0}/{1}'.format(obj_ref.bucket, obj_ref.object)
  else:
    raise storage_util.InvalidObjectNameError(uri, 'Missing object name')


def ValidateZone(args, compute_client):
  """Validate Compute Engine zone from args.zone.

  If not present in args, returns early.
  Args:
    args: CLI args dictionary
    compute_client: Compute Client

  Raises:
    InvalidArgumentException: when args.zone is an invalid GCE zone
  """
  if not args.zone:
    return

  requests = [(compute_client.apitools_client.zones, 'Get',
               compute_client.messages.ComputeZonesGetRequest(
                   project=properties.VALUES.core.project.GetOrFail(),
                   zone=args.zone))]
  try:
    compute_client.MakeRequests(requests)
  except calliope_exceptions.ToolException:
    raise calliope_exceptions.InvalidArgumentException('--zone', args.zone)
