# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Update cluster command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.container import api_adapter
from googlecloudsdk.api_lib.container import kubeconfig as kconfig
from googlecloudsdk.api_lib.container import util
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.container import container_command_util
from googlecloudsdk.command_lib.container import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.console import console_io
from six.moves import input  # pylint: disable=redefined-builtin


class InvalidAddonValueError(util.Error):
  """A class for invalid --update-addons input."""

  def __init__(self, value):
    message = ('invalid --update-addons value {0}; '
               'must be ENABLED or DISABLED.'.format(value))
    super(InvalidAddonValueError, self).__init__(message)


class InvalidPasswordError(util.Error):
  """A class for invalid password input."""

  def __init__(self, value, error):
    message = 'invalid password value "{0}"; {1}'.format(value, error)
    super(InvalidPasswordError, self).__init__(message)


def _ParseAddonDisabled(val):
  if val == 'ENABLED':
    return False
  if val == 'DISABLED':
    return True
  raise InvalidAddonValueError(val)


def _AddCommonArgs(parser):
  parser.add_argument(
      'name', metavar='NAME', help='The name of the cluster to update.')
  parser.add_argument('--node-pool', help='Node pool to be updated.')
  flags.AddAsyncFlag(parser)


def _AddMutuallyExclusiveArgs(mutex_group, release_track):
  """Add all arguments that need to be mutually exclusive from each other."""
  if release_track == base.ReleaseTrack.ALPHA:
    mutex_group.add_argument(
        '--update-addons',
        type=arg_parsers.ArgDict(
            spec={
                api_adapter.INGRESS: _ParseAddonDisabled,
                api_adapter.HPA: _ParseAddonDisabled,
                api_adapter.DASHBOARD: _ParseAddonDisabled,
                api_adapter.NETWORK_POLICY: _ParseAddonDisabled,
                api_adapter.ISTIO: _ParseAddonDisabled,
                api_adapter.CLOUDRUN: _ParseAddonDisabled,
                api_adapter.APPLICATIONMANAGER: _ParseAddonDisabled,
                api_adapter.CLOUDBUILD: _ParseAddonDisabled,
                api_adapter.NODELOCALDNS: _ParseAddonDisabled,
                api_adapter.GCEPDCSIDRIVER: _ParseAddonDisabled,
                api_adapter.CONFIGCONNECTOR: _ParseAddonDisabled,
            }),
        dest='disable_addons',
        metavar='ADDON=ENABLED|DISABLED',
        help="""Cluster addons to enable or disable. Options are
{hpa}=ENABLED|DISABLED
{ingress}=ENABLED|DISABLED
{dashboard}=ENABLED|DISABLED
{istio}=ENABLED|DISABLED
{application_manager}=ENABLED|DISABLED
{network_policy}=ENABLED|DISABLED
{cloudrun}=ENABLED|DISABLED
{cloudbuild}=ENABLED|DISABLED
{configconnector}=ENABLED|DISABLED
{nodelocaldns}=ENABLED|DISABLED
{gcepdcsidriver}=ENABLED|DISABLED""".format(
    hpa=api_adapter.HPA,
    ingress=api_adapter.INGRESS,
    dashboard=api_adapter.DASHBOARD,
    network_policy=api_adapter.NETWORK_POLICY,
    istio=api_adapter.ISTIO,
    application_manager=api_adapter.APPLICATIONMANAGER,
    cloudrun=api_adapter.CLOUDRUN,
    cloudbuild=api_adapter.CLOUDBUILD,
    configconnector=api_adapter.CONFIGCONNECTOR,
    nodelocaldns=api_adapter.NODELOCALDNS,
    gcepdcsidriver=api_adapter.GCEPDCSIDRIVER,
    ))

  elif release_track == base.ReleaseTrack.BETA:
    mutex_group.add_argument(
        '--update-addons',
        type=arg_parsers.ArgDict(
            spec={
                api_adapter.INGRESS: _ParseAddonDisabled,
                api_adapter.HPA: _ParseAddonDisabled,
                api_adapter.DASHBOARD: _ParseAddonDisabled,
                api_adapter.NETWORK_POLICY: _ParseAddonDisabled,
                api_adapter.ISTIO: _ParseAddonDisabled,
                api_adapter.CLOUDRUN: _ParseAddonDisabled,
                api_adapter.APPLICATIONMANAGER: _ParseAddonDisabled,
                api_adapter.NODELOCALDNS: _ParseAddonDisabled,
                api_adapter.GCEPDCSIDRIVER: _ParseAddonDisabled,
            }),
        dest='disable_addons',
        metavar='ADDON=ENABLED|DISABLED',
        help="""Cluster addons to enable or disable. Options are
{hpa}=ENABLED|DISABLED
{ingress}=ENABLED|DISABLED
{dashboard}=ENABLED|DISABLED
{istio}=ENABLED|DISABLED
{application_manager}=ENABLED|DISABLED
{network_policy}=ENABLED|DISABLED
{cloudrun}=ENABLED|DISABLED
{nodelocaldns}=ENABLED|DISABLED
{gcepdcsidriver}=ENABLED|DISABLED""".format(
    hpa=api_adapter.HPA,
    ingress=api_adapter.INGRESS,
    dashboard=api_adapter.DASHBOARD,
    network_policy=api_adapter.NETWORK_POLICY,
    istio=api_adapter.ISTIO,
    application_manager=api_adapter.APPLICATIONMANAGER,
    cloudrun=api_adapter.CLOUDRUN,
    nodelocaldns=api_adapter.NODELOCALDNS,
    gcepdcsidriver=api_adapter.GCEPDCSIDRIVER,
    ))

  else:
    mutex_group.add_argument(
        '--update-addons',
        type=arg_parsers.ArgDict(
            spec={
                api_adapter.INGRESS: _ParseAddonDisabled,
                api_adapter.HPA: _ParseAddonDisabled,
                api_adapter.DASHBOARD: _ParseAddonDisabled,
                api_adapter.NETWORK_POLICY: _ParseAddonDisabled,
                api_adapter.CLOUDRUN: _ParseAddonDisabled,
            }),
        dest='disable_addons',
        metavar='ADDON=ENABLED|DISABLED',
        help="""Cluster addons to enable or disable. Options are
{hpa}=ENABLED|DISABLED
{ingress}=ENABLED|DISABLED
{dashboard}=ENABLED|DISABLED
{network_policy}=ENABLED|DISABLED
{cloudrun}=ENABLED|DISABLED""".format(
    hpa=api_adapter.HPA,
    ingress=api_adapter.INGRESS,
    dashboard=api_adapter.DASHBOARD,
    network_policy=api_adapter.NETWORK_POLICY,
    cloudrun=api_adapter.CLOUDRUN,
    ))

  mutex_group.add_argument(
      '--generate-password',
      action='store_true',
      default=None,
      help='Ask the server to generate a secure password and use that as the '
      'basic auth password, keeping the existing username.')
  mutex_group.add_argument(
      '--set-password',
      action='store_true',
      default=None,
      help='Set the basic auth password to the specified value, keeping the '
      'existing username.')

  flags.AddBasicAuthFlags(mutex_group)


def _AddAdditionalZonesArg(mutex_group, deprecated=True):
  action = None
  if deprecated:
    action = actions.DeprecationAction(
        'additional-zones',
        warn='This flag is deprecated. '
        'Use --node-locations=PRIMARY_ZONE,[ZONE,...] instead.')
  mutex_group.add_argument(
      '--additional-zones',
      type=arg_parsers.ArgList(),
      action=action,
      metavar='ZONE',
      help="""\
The set of additional zones in which the cluster's node footprint should be
replicated. All zones must be in the same region as the cluster's primary zone.

Note that the exact same footprint will be replicated in all zones, such that
if you created a cluster with 4 nodes in a single zone and then use this option
to spread across 2 more zones, 8 additional nodes will be created.

Multiple locations can be specified, separated by commas. For example:

  $ {command} example-cluster --zone us-central1-a --additional-zones us-central1-b,us-central1-c

To remove all zones other than the cluster's primary zone, pass the empty string
to the flag. For example:

  $ {command} example-cluster --zone us-central1-a --additional-zones ""
""")


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update cluster settings for an existing container cluster."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
          To enable autoscaling for an existing cluster, run:

            $ {command} sample-cluster --enable-autoscaling
          """,
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
    """
    _AddCommonArgs(parser)
    group = parser.add_mutually_exclusive_group(required=True)
    group_locations = group.add_mutually_exclusive_group()
    _AddMutuallyExclusiveArgs(group, base.ReleaseTrack.GA)
    flags.AddNodeLocationsFlag(group_locations)
    flags.AddClusterAutoscalingFlags(parser, group)
    flags.AddMasterAuthorizedNetworksFlags(
        parser, enable_group_for_update=group)
    flags.AddEnableLegacyAuthorizationFlag(group)
    flags.AddStartIpRotationFlag(group)
    flags.AddStartCredentialRotationFlag(group)
    flags.AddCompleteIpRotationFlag(group)
    flags.AddCompleteCredentialRotationFlag(group)
    flags.AddUpdateLabelsFlag(group)
    flags.AddRemoveLabelsFlag(group)
    flags.AddNetworkPolicyFlags(group)
    flags.AddEnableIntraNodeVisibilityFlag(group)
    group_logging_monitoring = group.add_group()
    flags.AddLoggingServiceFlag(group_logging_monitoring)
    flags.AddMonitoringServiceFlag(group_logging_monitoring)
    flags.AddEnableBinAuthzFlag(group)
    flags.AddEnableStackdriverKubernetesFlag(group)
    flags.AddDailyMaintenanceWindowFlag(group, add_unset_text=True)
    flags.AddRecurringMaintenanceWindowFlags(group, is_update=True)
    flags.AddResourceUsageExportFlags(group, is_update=True)
    flags.AddWorkloadIdentityFlags(group)
    flags.AddWorkloadIdentityUpdateFlags(group)
    flags.AddDatabaseEncryptionFlag(group)
    flags.AddDisableDatabaseEncryptionFlag(group)
    flags.AddVerticalPodAutoscalingFlag(group)
    flags.AddAutoprovisioningFlags(group, ga=True)
    flags.AddEnableShieldedNodesFlags(group)

  def ParseUpdateOptions(self, args, locations):
    opts = container_command_util.ParseUpdateOptionsBase(args, locations)
    opts.resource_usage_bigquery_dataset = args.resource_usage_bigquery_dataset
    opts.clear_resource_usage_bigquery_dataset = \
        args.clear_resource_usage_bigquery_dataset
    opts.enable_network_egress_metering = args.enable_network_egress_metering
    opts.enable_resource_consumption_metering = \
        args.enable_resource_consumption_metering
    opts.enable_intra_node_visibility = args.enable_intra_node_visibility
    opts.enable_shielded_nodes = args.enable_shielded_nodes
    return opts

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    adapter = self.context['api_adapter']
    location_get = self.context['location_get']
    location = location_get(args)
    cluster_ref = adapter.ParseCluster(args.name, location)
    cluster_name = args.name
    cluster_node_count = None
    cluster_zone = cluster_ref.zone
    cluster_is_required = self.IsClusterRequired(args)
    try:
      # Attempt to get cluster for better prompts and to validate args.
      # Error is a warning but not fatal. Should only exit with a failure on
      # the actual update API calls below.
      cluster = adapter.GetCluster(cluster_ref)
      cluster_name = cluster.name
      cluster_node_count = cluster.currentNodeCount
      cluster_zone = cluster.zone
    except (exceptions.HttpException, apitools_exceptions.HttpForbiddenError,
            util.Error) as error:
      if cluster_is_required:
        raise
      log.warning(('Problem loading details of cluster to update:\n\n{}\n\n'
                   'You can still attempt updates to the cluster.\n').format(
                       console_attr.SafeText(error)))

    # locations will be None if additional-zones was specified, an empty list
    # if it was specified with no argument, or a populated list if zones were
    # provided. We want to distinguish between the case where it isn't
    # specified (and thus shouldn't be passed on to the API) and the case where
    # it's specified as wanting no additional zones, in which case we must pass
    # the cluster's primary zone to the API.
    # TODO(b/29578401): Remove the hasattr once the flag is GA.
    locations = None
    if hasattr(args, 'additional_zones') and args.additional_zones is not None:
      locations = sorted([cluster_ref.zone] + args.additional_zones)
    if hasattr(args, 'node_locations') and args.node_locations is not None:
      locations = sorted(args.node_locations)

    if args.IsSpecified('username') or args.IsSpecified('enable_basic_auth'):
      flags.MungeBasicAuthFlags(args)
      options = api_adapter.SetMasterAuthOptions(
          action=api_adapter.SetMasterAuthOptions.SET_USERNAME,
          username=args.username,
          password=args.password)

      try:
        op_ref = adapter.SetMasterAuth(cluster_ref, options)
      except apitools_exceptions.HttpError as error:
        raise exceptions.HttpException(error, util.HTTP_ERROR_FORMAT)
    elif (args.generate_password or args.set_password or
          args.IsSpecified('password')):
      if args.generate_password:
        password = ''
        options = api_adapter.SetMasterAuthOptions(
            action=api_adapter.SetMasterAuthOptions.GENERATE_PASSWORD,
            password=password)
      else:
        password = args.password
        if not args.IsSpecified('password'):
          password = input('Please enter the new password:')
        options = api_adapter.SetMasterAuthOptions(
            action=api_adapter.SetMasterAuthOptions.SET_PASSWORD,
            password=password)

      try:
        op_ref = adapter.SetMasterAuth(cluster_ref, options)
        del password
        del options
      except apitools_exceptions.HttpError as error:
        del password
        del options
        raise exceptions.HttpException(error, util.HTTP_ERROR_FORMAT)
    elif args.enable_network_policy is not None:
      console_io.PromptContinue(
          message='Enabling/Disabling Network Policy causes a rolling '
          'update of all cluster nodes, similar to performing a cluster '
          'upgrade.  This operation is long-running and will block other '
          'operations on the cluster (including delete) until it has run '
          'to completion.',
          cancel_on_no=True)
      options = api_adapter.SetNetworkPolicyOptions(
          enabled=args.enable_network_policy)
      try:
        op_ref = adapter.SetNetworkPolicy(cluster_ref, options)
      except apitools_exceptions.HttpError as error:
        raise exceptions.HttpException(error, util.HTTP_ERROR_FORMAT)
    elif args.start_ip_rotation or args.start_credential_rotation:
      if args.start_ip_rotation:
        msg_tmpl = """This will start an IP Rotation on cluster [{name}]. The \
master will be updated to serve on a new IP address in addition to the current \
IP address. Kubernetes Engine will then recreate all nodes ({num_nodes} nodes) \
to point to the new IP address. This operation is long-running and will block \
other operations on the cluster (including delete) until it has run to \
completion."""
        rotate_credentials = False
      elif args.start_credential_rotation:
        msg_tmpl = """This will start an IP and Credentials Rotation on cluster\
 [{name}]. The master will be updated to serve on a new IP address in addition \
to the current IP address, and cluster credentials will be rotated. Kubernetes \
Engine will then recreate all nodes ({num_nodes} nodes) to point to the new IP \
address. This operation is long-running and will block other operations on the \
cluster (including delete) until it has run to completion."""
        rotate_credentials = True
      console_io.PromptContinue(
          message=msg_tmpl.format(
              name=cluster_name,
              num_nodes=cluster_node_count if cluster_node_count else '?'),
          cancel_on_no=True)
      try:
        op_ref = adapter.StartIpRotation(
            cluster_ref, rotate_credentials=rotate_credentials)
      except apitools_exceptions.HttpError as error:
        raise exceptions.HttpException(error, util.HTTP_ERROR_FORMAT)
    elif args.complete_ip_rotation or args.complete_credential_rotation:
      if args.complete_ip_rotation:
        msg_tmpl = """This will complete the in-progress IP Rotation on \
cluster [{name}]. The master will be updated to stop serving on the old IP \
address and only serve on the new IP address. Make sure all API clients have \
been updated to communicate with the new IP address (e.g. by running `gcloud \
container clusters get-credentials --project {project} --zone {zone} {name}`). \
This operation is long-running and will block other operations on the cluster \
(including delete) until it has run to completion."""
      elif args.complete_credential_rotation:
        msg_tmpl = """This will complete the in-progress Credential Rotation on\
 cluster [{name}]. The master will be updated to stop serving on the old IP \
address and only serve on the new IP address. Old cluster credentials will be \
invalidated. Make sure all API clients have been updated to communicate with \
the new IP address (e.g. by running `gcloud container clusters get-credentials \
--project {project} --zone {zone} {name}`). This operation is long-running and \
will block other operations on the cluster (including delete) until it has run \
to completion."""
      console_io.PromptContinue(
          message=msg_tmpl.format(
              name=cluster_name,
              project=cluster_ref.projectId,
              zone=cluster_zone),
          cancel_on_no=True)
      try:
        op_ref = adapter.CompleteIpRotation(cluster_ref)
      except apitools_exceptions.HttpError as error:
        raise exceptions.HttpException(error, util.HTTP_ERROR_FORMAT)
    elif args.update_labels is not None:
      try:
        op_ref = adapter.UpdateLabels(cluster_ref, args.update_labels)
      except apitools_exceptions.HttpError as error:
        raise exceptions.HttpException(error, util.HTTP_ERROR_FORMAT)
    elif args.remove_labels is not None:
      try:
        op_ref = adapter.RemoveLabels(cluster_ref, args.remove_labels)
      except apitools_exceptions.HttpError as error:
        raise exceptions.HttpException(error, util.HTTP_ERROR_FORMAT)
    elif args.logging_service is not None and args.monitoring_service is None:
      try:
        op_ref = adapter.SetLoggingService(cluster_ref, args.logging_service)
      except apitools_exceptions.HttpError as error:
        raise exceptions.HttpException(error, util.HTTP_ERROR_FORMAT)
    elif args.maintenance_window is not None:
      try:
        op_ref = adapter.SetDailyMaintenanceWindow(cluster_ref,
                                                   cluster.maintenancePolicy,
                                                   args.maintenance_window)
      except apitools_exceptions.HttpError as error:
        raise exceptions.HttpException(error, util.HTTP_ERROR_FORMAT)
    elif getattr(args, 'maintenance_window_start', None) is not None:
      try:
        op_ref = adapter.SetRecurringMaintenanceWindow(
            cluster_ref, cluster.maintenancePolicy,
            args.maintenance_window_start, args.maintenance_window_end,
            args.maintenance_window_recurrence)
      except apitools_exceptions.HttpError as error:
        raise exceptions.HttpException(error, util.HTTP_ERROR_FORMAT)
    elif getattr(args, 'clear_maintenance_window', None):
      try:
        op_ref = adapter.RemoveMaintenanceWindow(cluster_ref,
                                                 cluster.maintenancePolicy)
      except apitools_exceptions.HttpError as error:
        raise exceptions.HttpException(error, util.HTTP_ERROR_FORMAT)
    elif getattr(args, 'add_maintenance_exclusion_end', None) is not None:
      try:
        op_ref = adapter.AddMaintenanceExclusion(
            cluster_ref, cluster.maintenancePolicy,
            args.add_maintenance_exclusion_name,
            args.add_maintenance_exclusion_start,
            args.add_maintenance_exclusion_end)
      except apitools_exceptions.HttpError as error:
        raise exceptions.HttpException(error, util.HTTP_ERROR_FORMAT)
    elif getattr(args, 'remove_maintenance_exclusion', None) is not None:
      try:
        op_ref = adapter.RemoveMaintenanceExclusion(
            cluster_ref, cluster.maintenancePolicy,
            args.remove_maintenance_exclusion)
      except apitools_exceptions.HttpError as error:
        raise exceptions.HttpException(error, util.HTTP_ERROR_FORMAT)
    else:
      if args.enable_legacy_authorization is not None:
        op_ref = adapter.SetLegacyAuthorization(
            cluster_ref, args.enable_legacy_authorization)
      else:
        options = self.ParseUpdateOptions(args, locations)
        op_ref = adapter.UpdateCluster(cluster_ref, options)

    if not args.async_:
      adapter.WaitForOperation(
          op_ref, 'Updating {0}'.format(cluster_ref.clusterId), timeout_s=3600)

      log.UpdatedResource(cluster_ref)
      cluster_url = util.GenerateClusterUrl(cluster_ref)
      log.status.Print('To inspect the contents of your cluster, go to: ' +
                       cluster_url)

      if (args.start_ip_rotation or args.complete_ip_rotation or
          args.start_credential_rotation or args.complete_credential_rotation):
        cluster = adapter.GetCluster(cluster_ref)
        try:
          util.ClusterConfig.Persist(cluster, cluster_ref.projectId)
        except kconfig.MissingEnvVarError as error:
          log.warning(error)

  def IsClusterRequired(self, args):
    """Returns if failure getting the cluster should be an error."""
    return bool(
        getattr(args, 'maintenance_window_end', False) or
        getattr(args, 'clear_maintenance_window', False) or
        getattr(args, 'add_maintenance_exclusion_end', False) or
        getattr(args, 'remove_maintenance_exclusion', False))


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBeta(Update):
  """Update cluster settings for an existing container cluster."""

  @staticmethod
  def Args(parser):
    _AddCommonArgs(parser)
    group = parser.add_mutually_exclusive_group(required=True)
    _AddMutuallyExclusiveArgs(group, base.ReleaseTrack.BETA)
    flags.AddClusterAutoscalingFlags(parser, group)
    group_locations = group.add_mutually_exclusive_group()
    _AddAdditionalZonesArg(group_locations, deprecated=True)
    flags.AddNodeLocationsFlag(group_locations)
    group_logging_monitoring = group.add_group()
    flags.AddLoggingServiceFlag(group_logging_monitoring)
    flags.AddMonitoringServiceFlag(group_logging_monitoring)
    flags.AddEnableStackdriverKubernetesFlag(group)
    flags.AddEnableLoggingMonitoringSystemOnlyFlag(group)
    flags.AddMasterAuthorizedNetworksFlags(
        parser, enable_group_for_update=group)
    flags.AddEnableLegacyAuthorizationFlag(group)
    flags.AddStartIpRotationFlag(group)
    flags.AddStartCredentialRotationFlag(group)
    flags.AddCompleteIpRotationFlag(group)
    flags.AddCompleteCredentialRotationFlag(group)
    flags.AddUpdateLabelsFlag(group)
    flags.AddRemoveLabelsFlag(group)
    flags.AddNetworkPolicyFlags(group)
    flags.AddDailyMaintenanceWindowFlag(group, add_unset_text=True)
    flags.AddRecurringMaintenanceWindowFlags(group, is_update=True)
    flags.AddPodSecurityPolicyFlag(group)
    flags.AddEnableBinAuthzFlag(group)
    flags.AddAutoprovisioningFlags(group)
    flags.AddAutoscalingProfilesFlag(group)
    flags.AddVerticalPodAutoscalingFlag(group)
    flags.AddResourceUsageExportFlags(group, is_update=True)
    flags.AddIstioConfigFlag(parser)
    flags.AddEnableIntraNodeVisibilityFlag(group)
    flags.AddWorkloadIdentityFlags(group, use_workload_pool=False)
    flags.AddWorkloadIdentityUpdateFlags(group)
    flags.AddDatabaseEncryptionFlag(group)
    flags.AddDisableDatabaseEncryptionFlag(group)
    flags.AddReleaseChannelFlag(group, is_update=True, hidden=False)
    flags.AddEnableShieldedNodesFlags(group)
    flags.AddTpuFlags(group, enable_tpu_service_networking=True)
    flags.AddMasterGlobalAccessFlag(group)
    flags.AddEnableGvnicFlag(group)

  def ParseUpdateOptions(self, args, locations):
    opts = container_command_util.ParseUpdateOptionsBase(args, locations)
    opts.enable_pod_security_policy = args.enable_pod_security_policy
    opts.istio_config = args.istio_config
    opts.resource_usage_bigquery_dataset = args.resource_usage_bigquery_dataset
    opts.enable_intra_node_visibility = args.enable_intra_node_visibility
    opts.clear_resource_usage_bigquery_dataset = \
        args.clear_resource_usage_bigquery_dataset
    opts.enable_network_egress_metering = args.enable_network_egress_metering
    opts.enable_resource_consumption_metering = args.enable_resource_consumption_metering
    flags.ValidateIstioConfigUpdateArgs(args.istio_config, args.disable_addons)
    if args.disable_addons and api_adapter.NODELOCALDNS in args.disable_addons:
      # NodeLocalDNS is being enabled or disabled
      console_io.PromptContinue(
          message='Enabling/Disabling NodeLocal DNSCache causes a re-creation '
          'of all cluster nodes at versions 1.15 or above. '
          'This operation is long-running and will block other '
          'operations on the cluster (including delete) until it has run '
          'to completion.',
          cancel_on_no=True)
    if args.disable_addons and api_adapter.GCEPDCSIDRIVER in args.disable_addons:
      pdcsi_disabled = args.disable_addons[api_adapter.GCEPDCSIDRIVER]
      if pdcsi_disabled:
        # Persistent Disk CSI Driver is being disabled
        console_io.PromptContinue(
            message='If the Compute Engine Persistent Disk CSI Driver is '
            'disabled, then any pods currently using PersistentVolumes owned '
            'by the driver will fail to terminate. Any new pods that try to '
            'use those PersistentVolumes will also fail to start.',
            cancel_on_no=True)

    opts.enable_stackdriver_kubernetes = args.enable_stackdriver_kubernetes
    opts.enable_logging_monitoring_system_only = args.enable_logging_monitoring_system_only
    opts.release_channel = args.release_channel
    opts.autoscaling_profile = args.autoscaling_profile

    # Top-level update options are automatically forced to be
    # mutually-exclusive, so we don't need special handling for these two.
    opts.identity_namespace = args.identity_namespace
    opts.enable_shielded_nodes = args.enable_shielded_nodes
    opts.enable_tpu = args.enable_tpu
    opts.tpu_ipv4_cidr = args.tpu_ipv4_cidr
    opts.enable_tpu_service_networking = args.enable_tpu_service_networking
    opts.enable_master_global_access = args.enable_master_global_access
    opts.enable_gvnic = args.enable_gvnic

    return opts


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(Update):
  """Update cluster settings for an existing container cluster."""

  @staticmethod
  def Args(parser):
    _AddCommonArgs(parser)
    group = parser.add_mutually_exclusive_group(required=True)
    _AddMutuallyExclusiveArgs(group, base.ReleaseTrack.ALPHA)
    flags.AddClusterAutoscalingFlags(parser, group)
    group_locations = group.add_mutually_exclusive_group()
    _AddAdditionalZonesArg(group_locations, deprecated=True)
    flags.AddNodeLocationsFlag(group_locations)
    group_logging_monitoring = group.add_group()
    flags.AddLoggingServiceFlag(group_logging_monitoring)
    flags.AddMonitoringServiceFlag(group_logging_monitoring)
    flags.AddEnableStackdriverKubernetesFlag(group)
    flags.AddEnableLoggingMonitoringSystemOnlyFlag(group)
    flags.AddMasterAuthorizedNetworksFlags(
        parser, enable_group_for_update=group)
    flags.AddEnableLegacyAuthorizationFlag(group)
    flags.AddStartIpRotationFlag(group)
    flags.AddStartCredentialRotationFlag(group)
    flags.AddCompleteIpRotationFlag(group)
    flags.AddCompleteCredentialRotationFlag(group)
    flags.AddUpdateLabelsFlag(group)
    flags.AddRemoveLabelsFlag(group)
    flags.AddNetworkPolicyFlags(group)
    flags.AddAutoprovisioningFlags(group, hidden=False)
    flags.AddAutoscalingProfilesFlag(group)
    flags.AddDailyMaintenanceWindowFlag(group, add_unset_text=True)
    flags.AddRecurringMaintenanceWindowFlags(group, is_update=True)
    flags.AddPodSecurityPolicyFlag(group)
    flags.AddEnableBinAuthzFlag(group)
    flags.AddResourceUsageExportFlags(group, is_update=True)
    flags.AddVerticalPodAutoscalingFlag(group)
    flags.AddSecurityProfileForUpdateFlag(group)
    flags.AddIstioConfigFlag(parser)
    flags.AddEnableIntraNodeVisibilityFlag(group)
    flags.AddWorkloadIdentityFlags(group, use_workload_pool=False)
    flags.AddWorkloadIdentityUpdateFlags(group)
    flags.AddDisableDefaultSnatFlag(group, for_cluster_create=False)
    flags.AddDatabaseEncryptionFlag(group)
    flags.AddDisableDatabaseEncryptionFlag(group)
    flags.AddCostManagementConfigFlag(group, is_update=True)
    flags.AddReleaseChannelFlag(group, is_update=True, hidden=False)
    flags.AddEnableShieldedNodesFlags(group)
    flags.AddTpuFlags(group, enable_tpu_service_networking=True)
    flags.AddMasterGlobalAccessFlag(group)
    flags.AddEnableGvnicFlag(group)

  def ParseUpdateOptions(self, args, locations):
    opts = container_command_util.ParseUpdateOptionsBase(args, locations)
    opts.autoscaling_profile = args.autoscaling_profile
    opts.enable_pod_security_policy = args.enable_pod_security_policy
    opts.resource_usage_bigquery_dataset = args.resource_usage_bigquery_dataset
    opts.clear_resource_usage_bigquery_dataset = \
        args.clear_resource_usage_bigquery_dataset
    opts.security_profile = args.security_profile
    opts.istio_config = args.istio_config
    opts.enable_intra_node_visibility = args.enable_intra_node_visibility
    opts.enable_network_egress_metering = args.enable_network_egress_metering
    opts.enable_resource_consumption_metering = args.enable_resource_consumption_metering
    flags.ValidateIstioConfigUpdateArgs(args.istio_config, args.disable_addons)
    if args.disable_addons and api_adapter.NODELOCALDNS in args.disable_addons:
      # NodeLocalDNS is being enabled or disabled
      console_io.PromptContinue(
          message='Enabling/Disabling NodeLocal DNSCache causes a re-creation '
          'of all cluster nodes at versions 1.15 or above. '
          'This operation is long-running and will block other '
          'operations on the cluster (including delete) until it has run '
          'to completion.',
          cancel_on_no=True)
    if args.disable_addons and api_adapter.GCEPDCSIDRIVER in args.disable_addons:
      pdcsi_disabled = args.disable_addons[api_adapter.GCEPDCSIDRIVER]
      if pdcsi_disabled:
        # GCE Persistent Disk CSI Driver is being disabled
        console_io.PromptContinue(
            message='If the GCE Persistent Disk CSI Driver is disabled, then any '
            'pods currently using PersistentVolumes owned by the driver '
            'will fail to terminate. Any new pods that try to use those '
            'PersistentVolumes will also fail to start.',
            cancel_on_no=True)
    opts.enable_stackdriver_kubernetes = args.enable_stackdriver_kubernetes
    opts.enable_logging_monitoring_system_only = args.enable_logging_monitoring_system_only
    opts.release_channel = args.release_channel
    opts.enable_tpu = args.enable_tpu
    opts.tpu_ipv4_cidr = args.tpu_ipv4_cidr
    opts.enable_tpu_service_networking = args.enable_tpu_service_networking

    # Top-level update options are automatically forced to be
    # mutually-exclusive, so we don't need special handling for these two.
    opts.identity_namespace = args.identity_namespace
    opts.enable_shielded_nodes = args.enable_shielded_nodes
    opts.disable_default_snat = args.disable_default_snat
    opts.enable_cost_management = args.enable_cost_management
    opts.enable_master_global_access = args.enable_master_global_access
    opts.enable_gvnic = args.enable_gvnic

    return opts
