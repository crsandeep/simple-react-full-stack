# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Provides common arguments for the Run command surface."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import collections
import os
import re
from apitools.base.py import exceptions as apitools_exceptions
import enum

from googlecloudsdk.api_lib.container import kubeconfig
from googlecloudsdk.api_lib.run import global_methods
from googlecloudsdk.api_lib.run import traffic
from googlecloudsdk.api_lib.services import enable_api
from googlecloudsdk.api_lib.services import exceptions as services_exceptions
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.functions.deploy import env_vars_util
from googlecloudsdk.command_lib.run import config_changes
from googlecloudsdk.command_lib.run import exceptions as serverless_exceptions
from googlecloudsdk.command_lib.run import pretty_print
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.util.args import map_util
from googlecloudsdk.command_lib.util.args import repeated
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import files

_VISIBILITY_MODES = {
    'internal': 'Visible only within the cluster.',
    'external': 'Visible from outside the cluster.',
}

PLATFORM_MANAGED = 'managed'
PLATFORM_GKE = 'gke'
PLATFORM_KUBERNETES = 'kubernetes'

_PLATFORMS = collections.OrderedDict([
    (PLATFORM_MANAGED, 'Fully managed version of Cloud Run. '
     'Use with the `--region` flag or set the [run/region] property '
     'to specify a Cloud Run region.'),
    (PLATFORM_GKE, 'Cloud Run for Anthos on Google Cloud. '
     'Use with the `--cluster` and `--cluster-location` flags or set the '
     '[run/cluster] and [run/cluster_location] properties to specify a '
     'cluster in a given zone.'),
    (PLATFORM_KUBERNETES, 'Use a Knative-compatible kubernetes cluster. '
     'Use with the `--kubeconfig` and `--context` flags to specify a '
     'kubeconfig file and the context for connecting.'),
])

_PLATFORM_SHORT_DESCRIPTIONS = {
    PLATFORM_MANAGED: 'Cloud Run (fully managed)',
    PLATFORM_GKE: 'Cloud Run for Anthos deployed on Google Cloud',
    PLATFORM_KUBERNETES: 'Cloud Run for Anthos deployed on VMware',
}

_DEFAULT_KUBECONFIG_PATH = '~/.kube/config'

_FIFTEEN_MINUTES = 15 * 60


class ArgumentError(exceptions.Error):
  pass


class KubeconfigError(exceptions.Error):
  pass


class Product(enum.Enum):
  RUN = 'Run'
  EVENTS = 'Events'


def AddImageArg(parser):
  """Add an image resource arg."""
  parser.add_argument(
      '--image',
      required=True,
      help='Name of the container image to deploy (e.g. '
      '`gcr.io/cloudrun/hello:latest`).')


def AddConfigFlags(parser):
  """Add config flags."""
  build_config = parser.add_mutually_exclusive_group()
  build_config.add_argument(
      '--image',
      help='Name of the container image to deploy (e.g. '
      '`gcr.io/cloudrun/hello:latest`).')
  build_config.add_argument(
      '--config',
      hidden=True,
      default='cloudbuild.yaml',  # By default, find this in the current dir
      help='The YAML or JSON file to use as the build configuration file.')


_ARG_GROUP_HELP_TEXT = ('Only applicable if connecting to {platform_desc}. '
                        'Specify {platform} to use:')


def _GetOrAddArgGroup(parser, help_text):
  """Create a new arg group or return existing group with given help text."""
  for arg in parser.arguments:
    if arg.is_group and arg.help == help_text:
      return arg
  return parser.add_argument_group(help_text)


def GetManagedArgGroup(parser):
  """Get an arg group for managed CR-only flags."""
  return _GetOrAddArgGroup(
      parser,
      _ARG_GROUP_HELP_TEXT.format(
          platform='`--platform={}`'.format(PLATFORM_MANAGED),
          platform_desc=_PLATFORM_SHORT_DESCRIPTIONS[PLATFORM_MANAGED]))


def GetGkeArgGroup(parser):
  """Get an arg group for CRoGKE-only flags."""
  return _GetOrAddArgGroup(
      parser,
      _ARG_GROUP_HELP_TEXT.format(
          platform='`--platform={}`'.format(PLATFORM_GKE),
          platform_desc=_PLATFORM_SHORT_DESCRIPTIONS[PLATFORM_GKE]))


def GetKubernetesArgGroup(parser):
  """Get an arg group for --platform=kubernetes only flags."""
  return _GetOrAddArgGroup(
      parser,
      _ARG_GROUP_HELP_TEXT.format(
          platform='`--platform={}`'.format(PLATFORM_KUBERNETES),
          platform_desc=_PLATFORM_SHORT_DESCRIPTIONS[PLATFORM_KUBERNETES]))


def GetClusterArgGroup(parser):
  """Get an arg group for any generic cluster flags."""
  return _GetOrAddArgGroup(
      parser,
      _ARG_GROUP_HELP_TEXT.format(
          platform='`--platform={}` or `--platform={}`'.format(
              PLATFORM_GKE, PLATFORM_KUBERNETES),
          platform_desc='{} or {}'.format(
              _PLATFORM_SHORT_DESCRIPTIONS[PLATFORM_GKE],
              _PLATFORM_SHORT_DESCRIPTIONS[PLATFORM_KUBERNETES])))


def AddAllowUnauthenticatedFlag(parser):
  """Add the --allow-unauthenticated flag."""
  parser.add_argument(
      '--allow-unauthenticated',
      action=arg_parsers.StoreTrueFalseAction,
      help='Whether to enable allowing unauthenticated access to the service. '
      'This may take a few moments to take effect.')


def AddAsyncFlag(parser):
  """Add an async flag."""
  base.ASYNC_FLAG.AddToParser(parser)


def AddEndpointVisibilityEnum(parser):
  """Add the --connectivity=[external|internal] flag."""
  parser.add_argument(
      '--connectivity',
      choices=_VISIBILITY_MODES,
      help=('Defaults to \'external\'. If \'external\', the service can be '
            'invoked through the internet, in addition to through the cluster '
            'network.'))


def AddServiceFlag(parser):
  """Add a service resource flag."""
  parser.add_argument(
      '--service',
      required=False,
      help='Limit matched revisions to the given service.')


def AddRegionArg(parser):
  """Add a region arg."""
  parser.add_argument(
      '--region',
      help='Region in which the resource can be found. '
      'Alternatively, set the property [run/region].')


def AddFunctionArg(parser):
  """Add a function resource arg."""
  parser.add_argument(
      '--function',
      hidden=True,
      help="""\
      Specifies that the deployed object is a function. If a value is
      provided, that value is used as the entrypoint.
      """)


def AddNoTrafficFlag(parser):
  """Add flag to deploy a revision with no traffic."""
  parser.add_argument(
      '--no-traffic',
      default=False,
      action='store_true',
      help='True to avoid sending traffic to the revision being deployed. '
      'Setting this flag assigns any traffic assigned to the LATEST revision '
      'to the specific revision bound to LATEST before the deployment. The '
      'effect is that the revsion being deployed will not receive traffic. '
      'After a deployment with this flag the LATEST revision will not receive '
      'traffic on future deployments.')


def AddTrafficTagsFlags(parser):
  """Add flags for updating traffic tags for a service."""
  AddMapFlagsNoFile(
      parser,
      group_help=('Specify traffic tags. Traffic tags can be '
                  'assigned to a revision by name or to the '
                  'latest ready revision. Assigning a tag to a '
                  'revision generates a URL prefixed with the '
                  'tag that allows addressing that revision '
                  'directly, regardless of the percent traffic '
                  'specified. Keys are tags. Values are revision names or '
                  '"LATEST" for the latest ready revision. For example, '
                  '--set-tags=candidate=LATEST,current='
                  'myservice-v1 assigns the tag "candidate" '
                  'to the latest ready revision and the tag'
                  ' "current" to the revision with name '
                  '"myservice-v1" and clears any existing tags. '
                  'Changing tags does not '
                  'affect the traffic percentage assigned to '
                  'revisions. When using a tags flag and '
                  'one or more of --to-latest and --to-revisions in the same '
                  'command, the tags change occurs first then the traffic '
                  'percentage change occurs.'),
      flag_name='tags')


def AddUpdateTrafficFlags(parser):
  """Add flags for updating traffic assignments for a service."""

  @staticmethod
  def TrafficTargetKey(key):
    return key

  @staticmethod
  def TrafficPercentageValue(value):
    """Type validation for traffic percentage flag values."""
    try:
      result = int(value)
    except (TypeError, ValueError):
      raise ArgumentError('Traffic percentage value %s is not an integer.' %
                          value)

    if result < 0 or result > 100:
      raise ArgumentError(
          'Traffic percentage value %s is not between 0 and 100.' % value)
    return result

  group = parser.add_mutually_exclusive_group()

  group.add_argument(
      '--to-revisions',
      metavar='REVISION-NAME=PERCENTAGE',
      action=arg_parsers.UpdateAction,
      type=arg_parsers.ArgDict(
          key_type=TrafficTargetKey.__func__,
          value_type=TrafficPercentageValue.__func__),
      help='Comma separated list of traffic assignments in the form '
      'REVISION-NAME=PERCENTAGE. REVISION-NAME must be the name for a '
      'revision for the service as returned by \'gcloud beta run list '
      'revisions\'. PERCENTAGE must be an integer percentage between '
      '0 and 100 inclusive.  Ex service-nw9hs=10,service-nw9hs=20 '
      'Up to 100 percent of traffic may be assigned. If 100 percent '
      'of traffic is assigned,  the Service traffic is updated as '
      'specified. If under 100 percent of traffic is assigned, the '
      'Service traffic is updated as specified for revisions with '
      'assignments and traffic is scaled up or down down proportionally '
      'as needed for revision that are currently serving traffic but that do '
      'not have new assignments. For example assume revision-1 is serving '
      '40 percent of traffic and revision-2 is serving 60 percent. If '
      'revision-1 is assigned 45 percent of traffic and no assignment is '
      'made for revision-2, the service is updated with revsion-1 assigned '
      '45 percent of traffic and revision-2 scaled down to 55 percent. '
      'You can use "LATEST" as a special revision name to always put the given '
      'percentage of traffic on the latest ready revision.')

  group.add_argument(
      '--to-latest',
      default=False,
      action='store_true',
      help='True to assign 100 percent of traffic to the \'latest\' '
      'revision of this service. Note that when a new revision is '
      'created, it will become the \'latest\' and traffic will be '
      'directed to it. Defaults to False. Synonymous with '
      '\'--to-revisions=LATEST=100\'.')


def AddCloudSQLFlags(parser):
  """Add flags for setting CloudSQL stuff."""
  repeated.AddPrimitiveArgs(
      parser,
      'Service',
      'cloudsql-instances',
      'Cloud SQL instances',
      auto_group_help=False,
      additional_help="""\
      These flags modify the Cloud SQL instances this Service connects to.
      You can specify a name of a Cloud SQL instance if it's in the same
      project and region as your Cloud Run service; otherwise specify
      <project>:<region>:<instance> for the instance.""")


def AddMapFlagsNoFile(parser,
                      flag_name,
                      group_help='',
                      long_name=None,
                      key_type=None,
                      value_type=None):
  """Add flags like map_util.AddUpdateMapFlags but without the file one.

  Args:
    parser: The argument parser
    flag_name: The name for the property to be used in flag names
    group_help: Help text for the group of flags
    long_name: The name for the property to be used in help text
    key_type: A function to apply to map keys.
    value_type: A function to apply to map values.
  """
  if not long_name:
    long_name = flag_name

  group = parser.add_mutually_exclusive_group(group_help)
  update_remove_group = group.add_argument_group(
      help=('Only --update-{0} and --remove-{0} can be used together. If both '
            'are specified, --remove-{0} will be applied first.'
           ).format(flag_name))
  map_util.AddMapUpdateFlag(
      update_remove_group,
      flag_name,
      long_name,
      key_type=key_type,
      value_type=value_type)
  map_util.AddMapRemoveFlag(
      update_remove_group, flag_name, long_name, key_type=key_type)
  map_util.AddMapClearFlag(group, flag_name, long_name)
  map_util.AddMapSetFlag(
      group, flag_name, long_name, key_type=key_type, value_type=value_type)


def AddMutexEnvVarsFlags(parser):
  """Add flags for creating updating and deleting env vars."""
  # TODO(b/119837621): Use env_vars_util.AddUpdateEnvVarsFlags when
  # `gcloud run` supports an env var file.
  AddMapFlagsNoFile(
      parser,
      flag_name='env-vars',
      long_name='environment variables',
      key_type=env_vars_util.EnvVarKeyType,
      value_type=env_vars_util.EnvVarValueType)


def AddMemoryFlag(parser):
  parser.add_argument('--memory', help='Set a memory limit. Ex: 1Gi, 512Mi.')


def AddCpuFlag(parser):
  parser.add_argument(
      '--cpu',
      help='Set a CPU limit in Kubernetes cpu units. '
      'Ex: .5, 500m, 2.')


def _ConcurrencyValue(value):
  """Returns True if value is an int > 0 or 'default'."""
  try:
    return value == 'default' or int(value) > 0
  except ValueError:
    return False


def AddConcurrencyFlag(parser):
  parser.add_argument(
      '--concurrency',
      type=arg_parsers.CustomFunctionValidator(
          _ConcurrencyValue, 'must be an integer greater than 0 or "default".'),
      help='Set the number of concurrent requests allowed per '
      'container instance. A concurrency of 0 or unspecified indicates '
      'any number of concurrent requests are allowed. To unset '
      'this field, provide the special value `default`.')


def AddTimeoutFlag(parser):
  parser.add_argument(
      '--timeout',
      type=arg_parsers.Duration(lower_bound='1s'),
      help='Set the maximum request execution time (timeout). It is specified '
      'as a duration; for example, "10m5s" is ten minutes, and five seconds. '
      'If you don\'t specify a unit, seconds is assumed. For example, "10" is '
      '10 seconds.')


def AddServiceAccountFlag(parser):
  parser.add_argument(
      '--service-account',
      help='Email address of the IAM service account associated with the '
      'revision of the service. The service account represents the identity of '
      'the running revision, and determines what permissions the revision has. '
      'If not provided, the revision will use the project\'s default service '
      'account.')


def AddServiceAccountFlagAlpha(parser):
  parser.add_argument(
      '--service-account',
      help='The service account associated with the revision of the service. '
      'The service account represents the identity of '
      'the running revision, and determines what permissions the revision has. '
      'For the {} platform, this is the email address of an IAM '
      'service account. For the Kubernetes-based platforms ({}, {}), this is '
      'the name of a Kubernetes service account in the same namespace as the '
      'service. If not provided, the revision will use the default service '
      'account of the project, or default Kubernetes namespace service account '
      'respectively.'.format(PLATFORM_MANAGED, PLATFORM_GKE,
                             PLATFORM_KUBERNETES))


def AddPlatformArg(parser):
  """Add a platform arg."""
  parser.add_argument(
      '--platform',
      choices=_PLATFORMS,
      action=actions.StoreProperty(properties.VALUES.run.platform),
      help='Target platform for running commands. '
      'Alternatively, set the property [run/platform]. '
      'If not specified, the user will be prompted to choose a platform.')


def AddKubeconfigFlags(parser):
  parser.add_argument(
      '--kubeconfig',
      help='The absolute path to your kubectl config file. If not specified, '
      'the colon- or semicolon-delimited list of paths specified by '
      '$KUBECONFIG will be used. If $KUBECONFIG is unset, this defaults to '
      '`{}`.'.format(_DEFAULT_KUBECONFIG_PATH))
  parser.add_argument(
      '--context',
      help='The name of the context in your kubectl config file to use for '
      'connecting.')


def AddRevisionSuffixArg(parser):
  parser.add_argument(
      '--revision-suffix',
      help='Specify the suffix of the revision name. Revision names always '
      'start with the service name automatically. For example, specifying '
      '[--revision-suffix=v1] for a service named \'helloworld\', '
      'would lead to a revision named \'helloworld-v1\'.')


def AddVpcConnectorArg(parser):
  parser.add_argument(
      '--vpc-connector', help='Set a VPC connector for this Service.')
  parser.add_argument(
      '--clear-vpc-connector',
      action='store_true',
      help='Remove the VPC connector for this Service.')


def AddSecretsFlags(parser):
  """Adds flags for creating, updating, and deleting secrets."""
  AddMapFlagsNoFile(
      parser,
      group_help=('Specify secrets to mount or provide as environment '
                  "variables. Keys starting with a forward slash '/' are mount "
                  'paths. All other keys correspond to environment variables. '
                  'The values associated with each of these should be in the '
                  'form SECRET_NAME:KEY_IN_SECRET; you may omit the '
                  'key within the secret to specify a mount of all keys '
                  'within the secret. For example: '
                  "'--update-secrets=/my/path=mysecret,"
                  "ENV=othersecret:key.json' "
                  "will create a volume with secret 'mysecret' "
                  "and mount that volume at '/my/path'. Because no secret "
                  "key was specified, all keys in 'mysecret' will be included. "
                  'An environment variable named ENV will also be created '
                  "whose value is the value of 'key.json' in 'othersecret'."),
      flag_name='secrets')


def AddConfigMapsFlags(parser):
  """Adds flags for creating, updating, and deleting config maps."""
  AddMapFlagsNoFile(
      parser,
      group_help=('Specify config map to mount or provide as environment '
                  "variables. Keys starting with a forward slash '/' are mount "
                  'paths. All other keys correspond to environment variables. '
                  'The values associated with each of these should be in the '
                  'form CONFIG_MAP_NAME:KEY_IN_CONFIG_MAP; you may omit the '
                  'key within the config map to specify a mount of all keys '
                  'within the config map. For example: '
                  "'--update-config-maps=/my/path=myconfig,"
                  "ENV=otherconfig:key.json' "
                  "will create a volume with config map 'myconfig' "
                  "and mount that volume at '/my/path'. Because no config map "
                  "key was specified, all keys in 'myconfig' will be included. "
                  'An environment variable named ENV will also be created '
                  "whose value is the value of 'key.json' in 'otherconfig'."),
      flag_name='config-maps')


def AddLabelsFlags(parser):
  """Adds update command labels flags to an argparse parser.

  Args:
    parser: The argparse parser to add the flags to.
  """
  group = parser.add_group()
  add_group = group.add_mutually_exclusive_group()
  labels_util.GetCreateLabelsFlag(
      'An alias to --update-labels.',
      validate_keys=False,
      validate_values=False).AddToParser(add_group)
  labels_util.GetUpdateLabelsFlag(
      '', validate_keys=False, validate_values=False).AddToParser(add_group)
  remove_group = group.add_mutually_exclusive_group()
  labels_util.GetClearLabelsFlag().AddToParser(remove_group)
  labels_util.GetRemoveLabelsFlag('').AddToParser(remove_group)


class _ScaleValue(object):
  """Type for min/max-instaces flag values."""

  def __init__(self, value):
    self.restore_default = value == 'default'
    if not self.restore_default:
      try:
        self.instance_count = int(value)
      except (TypeError, ValueError):
        raise ArgumentError('Instance count value %s is not an integer '
                            'or \'default\'.' % value)

      if self.instance_count < 0:
        raise ArgumentError('Instance count value %s is negative.' % value)


def AddMinInstancesFlag(parser):
  """Add min scaling flag."""
  parser.add_argument(
      '--min-instances',
      type=_ScaleValue,
      help=('The minimum number of container instances of the Service to run '
            "or 'default' to remove any minimum."))


def AddMaxInstancesFlag(parser):
  """Add max scaling flag."""
  parser.add_argument(
      '--max-instances',
      type=_ScaleValue,
      help=('The maximum number of container instances of the Service to run. '
            "Use 'default' to unset the limit and use the platform default."))


def AddCommandFlag(parser):
  """Add flags for specifying container's startup command."""
  parser.add_argument(
      '--command',
      metavar='COMMAND',
      type=arg_parsers.ArgList(),
      action=arg_parsers.UpdateAction,
      help='Entrypoint for the container image. If not specified, the '
      'container image\'s default Entrypoint is run. '
      'To reset this field to its default, pass an empty string.')


def AddArgsFlag(parser):
  """Add flags for specifying container's startup args."""
  parser.add_argument(
      '--args',
      metavar='ARG',
      type=arg_parsers.ArgList(),
      action=arg_parsers.UpdateAction,
      help='Comma-separated arguments passed to the command run by the '
      'container image. If not specified and no \'--command\' is provided, the '
      'container image\'s default Cmd is used. Otherwise, if not specified, no '
      'arguments are passed. '
      'To reset this field to its default, pass an empty string.')


def _PortValue(value):
  """Returns True if port value is an int within range or 'default'."""
  try:
    return value == 'default' or (int(value) >= 1 and int(value) <= 65535)
  except ValueError:
    return False


def AddPortFlag(parser):
  """Add port flag to override $PORT."""
  parser.add_argument(
      '--port',
      type=arg_parsers.CustomFunctionValidator(
          _PortValue,
          'must be an integer between 1 and 65535, inclusive, or "default".'),
      help='Container port to receive requests at. Also sets the $PORT '
      'environment variable. Must be a number between 1 and 65535, inclusive. '
      'To unset this field, pass the special value "default".')


def AddHttp2Flag(parser):
  """Add http/2 flag to set the port name."""
  parser.add_argument(
      '--use-http2',
      action=arg_parsers.StoreTrueFalseAction,
      help='Whether to use HTTP/2 for connections to the service.')


def _HasChanges(args, flags):
  """True iff any of the passed flags are set."""
  return any(FlagIsExplicitlySet(args, flag) for flag in flags)


def _HasEnvChanges(args):
  """True iff any of the env var flags are set."""
  env_flags = [
      'update_env_vars', 'set_env_vars', 'remove_env_vars', 'clear_env_vars'
  ]
  return _HasChanges(args, env_flags)


def _HasCloudSQLChanges(args):
  """True iff any of the cloudsql flags are set."""
  instances_flags = [
      'add_cloudsql_instances', 'set_cloudsql_instances',
      'remove_cloudsql_instances', 'clear_cloudsql_instances'
  ]
  return _HasChanges(args, instances_flags)


def _EnabledCloudSqlApiRequired(args):
  """True iff flags that add or set cloud sql instances are set."""
  instances_flags = (
      'add_cloudsql_instances',
      'set_cloudsql_instances',
  )
  return _HasChanges(args, instances_flags)


def _HasLabelChanges(args):
  """True iff any of the label flags are set."""
  label_flags = ['labels', 'update_labels', 'clear_labels', 'remove_labels']
  return _HasChanges(args, label_flags)


def _HasSecretsChanges(args):
  """True iff any of the secret flags are set."""
  secret_flags = [
      'update_secrets', 'set_secrets', 'remove_secrets', 'clear_secrets'
  ]
  return _HasChanges(args, secret_flags)


def _HasConfigMapsChanges(args):
  """True iff any of the config maps flags are set."""
  config_maps_flags = [
      'update_config_maps', 'set_config_maps', 'remove_config_maps',
      'clear_config_maps'
  ]
  return _HasChanges(args, config_maps_flags)


def _HasTrafficTagsChanges(args):
  """True iff any of the traffic tags flags are set."""
  tags_flags = ['update_tags', 'set_tags', 'remove_tags', 'clear_tags']
  return _HasChanges(args, tags_flags)


def _HasTrafficChanges(args):
  """True iff any of the traffic flags are set."""
  traffic_flags = ['to_revisions', 'to_latest']
  return _HasChanges(args, traffic_flags) or _HasTrafficTagsChanges(args)


def _GetEnvChanges(args):
  """Return config_changes.EnvVarLiteralChanges for given args."""
  kwargs = {}

  update = args.update_env_vars or args.set_env_vars
  if update:
    kwargs['env_vars_to_update'] = update

  remove = args.remove_env_vars
  if remove:
    kwargs['env_vars_to_remove'] = remove

  if args.set_env_vars or args.clear_env_vars:
    kwargs['clear_others'] = True

  return config_changes.EnvVarLiteralChanges(**kwargs)


def _GetScalingChanges(args):
  """Returns the list of changes for scaling for given args."""
  result = []
  if 'min_instances' in args and args.min_instances is not None:
    scale_value = args.min_instances
    if scale_value.restore_default or scale_value.instance_count == 0:
      result.append(
          config_changes.DeleteTemplateAnnotationChange(
              'autoscaling.knative.dev/minScale'))
    else:
      result.append(
          config_changes.SetTemplateAnnotationChange(
              'autoscaling.knative.dev/minScale',
              str(scale_value.instance_count)))
  if 'max_instances' in args and args.max_instances is not None:
    scale_value = args.max_instances
    if scale_value.restore_default:
      result.append(
          config_changes.DeleteTemplateAnnotationChange(
              'autoscaling.knative.dev/maxScale'))
    else:
      result.append(
          config_changes.SetTemplateAnnotationChange(
              'autoscaling.knative.dev/maxScale',
              str(scale_value.instance_count)))
  return result


def _IsVolumeMountKey(key):
  """Returns True if the key refers to a volume mount."""
  return key.startswith('/')


def _GetSecretsChanges(args):
  """Return secret env var and volume changes for given args."""
  volume_kwargs = {}
  env_kwargs = {}

  update = args.update_secrets or args.set_secrets
  if update:
    volume_update = {k: v for k, v in update.items() if _IsVolumeMountKey(k)}
    if volume_update:
      volume_kwargs['mounts_to_update'] = volume_update
    env_update = {k: v for k, v in update.items() if not _IsVolumeMountKey(k)}
    if env_update:
      env_kwargs['env_vars_to_update'] = env_update

  remove = args.remove_secrets
  if remove:
    volume_remove = [k for k in remove if _IsVolumeMountKey(k)]
    if volume_remove:
      volume_kwargs['mounts_to_remove'] = volume_remove
    env_remove = [k for k in remove if not _IsVolumeMountKey(k)]
    if env_remove:
      env_kwargs['env_vars_to_remove'] = env_remove

  if args.set_secrets or args.clear_secrets:
    env_kwargs['clear_others'] = True
    volume_kwargs['clear_others'] = True

  secret_changes = []
  if env_kwargs:
    secret_changes.append(config_changes.SecretEnvVarChanges(**env_kwargs))
  if volume_kwargs:
    secret_changes.append(config_changes.SecretVolumeChanges(**volume_kwargs))
  return secret_changes


def _GetConfigMapsChanges(args):
  """Return config map env var and volume changes for given args."""
  volume_kwargs = {}
  env_kwargs = {}

  update = args.update_config_maps or args.set_config_maps
  if update:
    volume_update = {k: v for k, v in update.items() if _IsVolumeMountKey(k)}
    if volume_update:
      volume_kwargs['mounts_to_update'] = volume_update
    env_update = {k: v for k, v in update.items() if not _IsVolumeMountKey(k)}
    if env_update:
      env_kwargs['env_vars_to_update'] = env_update

  remove = args.remove_config_maps
  if remove:
    volume_remove = [k for k in remove if _IsVolumeMountKey(k)]
    if volume_remove:
      volume_kwargs['mounts_to_remove'] = volume_remove
    env_remove = [k for k in remove if not _IsVolumeMountKey(k)]
    if env_remove:
      env_kwargs['env_vars_to_remove'] = env_remove

  if args.set_config_maps or args.clear_config_maps:
    env_kwargs['clear_others'] = True
    volume_kwargs['clear_others'] = True

  secret_changes = []
  if env_kwargs:
    secret_changes.append(config_changes.ConfigMapEnvVarChanges(**env_kwargs))
  if volume_kwargs:
    secret_changes.append(
        config_changes.ConfigMapVolumeChanges(**volume_kwargs))
  return secret_changes


def PromptToEnableApi(service_name):
  """Prompts to enable the API and throws if the answer is no.

  Args:
    service_name: str, The service token of the API to prompt for.
  """
  if not properties.VALUES.core.should_prompt_to_enable_api.GetBool():
    return

  project = properties.VALUES.core.project.Get(required=True)
  # Don't prompt to enable an already enabled API
  if not enable_api.IsServiceEnabled(project, service_name):
    if console_io.PromptContinue(
        default=False,
        cancel_on_no=True,
        prompt_string=('API [{}] not enabled on project [{}]. '
                       'Would you like to enable and retry (this will take a '
                       'few minutes)?').format(service_name, project)):
      enable_api.EnableService(project, service_name)


_CLOUD_SQL_API_SERVICE_TOKEN = 'sql-component.googleapis.com'
_CLOUD_SQL_ADMIN_API_SERVICE_TOKEN = 'sqladmin.googleapis.com'


def _CheckCloudSQLApiEnablement():
  if not properties.VALUES.core.should_prompt_to_enable_api.GetBool():
    return
  try:
    PromptToEnableApi(_CLOUD_SQL_API_SERVICE_TOKEN)
    PromptToEnableApi(_CLOUD_SQL_ADMIN_API_SERVICE_TOKEN)
  except (services_exceptions.GetServicePermissionDeniedException,
          apitools_exceptions.HttpError):
    log.status.Print('Skipped validating Cloud SQL API and Cloud SQL Admin API'
                     ' enablement due to an issue contacting the Service Usage '
                     ' API. Please ensure the Cloud SQL API and Cloud SQL Admin'
                     ' API are activated (see '
                     'https://console.cloud.google.com/apis/dashboard).')


def _GetTrafficChanges(args):
  """Returns a changes for traffic assignment based on the flags."""
  # Check if args has tags changes again in case args does not include tags
  # flags. Tags will launch in the alpha release track only.
  if _HasTrafficTagsChanges(args):
    update_tags = args.update_tags or args.set_tags
    remove_tags = args.remove_tags
    clear_other_tags = bool(args.set_tags) or args.clear_tags
  else:
    update_tags = None
    remove_tags = None
    clear_other_tags = False
  if args.to_latest:
    # Mutually exlcusive flag with to-revisions
    new_percentages = {traffic.LATEST_REVISION_KEY: 100}
  else:
    new_percentages = args.to_revisions if args.to_revisions else {}
  return config_changes.TrafficChanges(new_percentages, update_tags,
                                       remove_tags, clear_other_tags)


def GetConfigurationChanges(args):
  """Returns a list of changes to Configuration, based on the flags set."""
  changes = []
  changes.extend(_GetScalingChanges(args))
  if _HasEnvChanges(args):
    changes.append(_GetEnvChanges(args))

  if _HasTrafficChanges(args):
    changes.append(_GetTrafficChanges(args))

  if _HasCloudSQLChanges(args):
    region = GetRegion(args)
    project = (
        getattr(args, 'project', None) or
        properties.VALUES.core.project.Get(required=True))
    if _EnabledCloudSqlApiRequired(args):
      _CheckCloudSQLApiEnablement()
    changes.append(config_changes.CloudSQLChanges(project, region, args))

  if _HasSecretsChanges(args):
    changes.extend(_GetSecretsChanges(args))

  if _HasConfigMapsChanges(args):
    changes.extend(_GetConfigMapsChanges(args))

  if 'no_traffic' in args and args.no_traffic:
    changes.append(config_changes.NoTrafficChange())

  if 'cpu' in args and args.cpu:
    changes.append(config_changes.ResourceChanges(cpu=args.cpu))
  if 'memory' in args and args.memory:
    changes.append(config_changes.ResourceChanges(memory=args.memory))
  if 'concurrency' in args and args.concurrency:
    changes.append(
        config_changes.ConcurrencyChanges(concurrency=args.concurrency))
  if 'timeout' in args and args.timeout:
    changes.append(config_changes.TimeoutChanges(timeout=args.timeout))
  if 'service_account' in args and args.service_account:
    changes.append(
        config_changes.ServiceAccountChanges(
            service_account=args.service_account))
  if _HasLabelChanges(args):
    additions = (
        args.labels
        if FlagIsExplicitlySet(args, 'labels') else args.update_labels)
    diff = labels_util.Diff(
        additions=additions,
        subtractions=args.remove_labels,
        clear=args.clear_labels)
    if diff.MayHaveUpdates():
      changes.append(config_changes.LabelChanges(diff))
  if 'revision_suffix' in args and args.revision_suffix:
    changes.append(config_changes.RevisionNameChanges(args.revision_suffix))
  if 'vpc_connector' in args and args.vpc_connector:
    changes.append(config_changes.VpcConnectorChange(args.vpc_connector))
  if 'clear_vpc_connector' in args and args.clear_vpc_connector:
    changes.append(config_changes.ClearVpcConnectorChange())
  if 'connectivity' in args and args.connectivity:
    if args.connectivity == 'internal':
      changes.append(config_changes.EndpointVisibilityChange(True))
    elif args.connectivity == 'external':
      changes.append(config_changes.EndpointVisibilityChange(False))
  if 'command' in args and args.command is not None:
    # Allow passing an empty string here to reset the field
    changes.append(config_changes.ContainerCommandChange(args.command))
  if 'args' in args and args.args is not None:
    # Allow passing an empty string here to reset the field
    changes.append(config_changes.ContainerArgsChange(args.args))
  if FlagIsExplicitlySet(args, 'port'):
    changes.append(config_changes.ContainerPortChange(port=args.port))
  if FlagIsExplicitlySet(args, 'use_http2'):
    changes.append(config_changes.ContainerPortChange(use_http2=args.use_http2))
  return changes


def GetService(args):
  """Get and validate the service resource from the args."""
  service_ref = args.CONCEPTS.service.Parse()
  # Valid service names comprise only alphanumeric characters and dashes. Must
  # not begin or end with a dash, and must not contain more than 63 characters.
  # Must be lowercase.
  service_re = re.compile(r'(?=^[a-z0-9-]{1,63}$)(?!^\-.*)(?!.*\-$)')
  if service_re.match(service_ref.servicesId):
    return service_ref
  raise ArgumentError(
      'Invalid service name [{}]. Service name must use only lowercase '
      'alphanumeric characters and dashes. Cannot begin or end with a dash, '
      'and cannot be longer than 63 characters.'.format(service_ref.servicesId))


def GetClusterRef(cluster):
  project = properties.VALUES.core.project.Get(required=True)
  return resources.REGISTRY.Parse(
      cluster.name,
      params={
          'projectId': project,
          'zone': cluster.zone
      },
      collection='container.projects.zones.clusters')


def PromptForRegion():
  """Prompt for region from list of available regions.

  This method is referenced by the declaritive iam commands as a fallthrough
  for getting the region.

  Returns:
    The region specified by the user, str
  """
  if console_io.CanPrompt():
    client = global_methods.GetServerlessClientInstance()
    all_regions = global_methods.ListRegions(client)
    idx = console_io.PromptChoice(
        all_regions, message='Please specify a region:\n', cancel_option=True)
    region = all_regions[idx]
    log.status.Print('To make this the default region, run '
                     '`gcloud config set run/region {}`.\n'.format(region))
    return region


def GetRegion(args, prompt=False):
  """Prompt for region if not provided.

  Region is decided in the following order:
  - region argument;
  - run/region gcloud config;
  - prompt user.

  Args:
    args: Namespace, The args namespace.
    prompt: bool, whether to attempt to prompt.

  Returns:
    A str representing region.
  """
  if getattr(args, 'region', None):
    return args.region
  if properties.VALUES.run.region.IsExplicitlySet():
    return properties.VALUES.run.region.Get()
  if prompt:
    region = PromptForRegion()
    if region:
      # set the region on args, so we're not embarassed the next time we call
      # GetRegion
      args.region = region
      return region


def GetAllowUnauthenticated(args, client=None, service_ref=None, prompt=False):
  """Return bool for the explicit intent to allow unauth invocations or None.

  If --[no-]allow-unauthenticated is set, return that value. If not set,
  prompt for value if desired. If prompting not necessary or doable,
  return None, indicating that no action needs to be taken.

  Args:
    args: Namespace, The args namespace
    client: from googlecloudsdk.command_lib.run import serverless_operations
      serverless_operations.ServerlessOperations object
    service_ref: service resource reference (e.g. args.CONCEPTS.service.Parse())
    prompt: bool, whether to attempt to prompt.

  Returns:
    bool indicating whether to allow/unallow unauthenticated or None if N/A
  """
  if getattr(args, 'allow_unauthenticated', None) is not None:
    return args.allow_unauthenticated

  if prompt:
    # Need to check if the user has permissions before we prompt
    assert client is not None and service_ref is not None
    if client.CanSetIamPolicyBinding(service_ref):
      return console_io.PromptContinue(
          prompt_string=('Allow unauthenticated invocations '
                         'to [{}]'.format(service_ref.servicesId)),
          default=False)
    else:
      pretty_print.Info(
          'This service will require authentication to be invoked.')
  return None


def GetKubeconfig(args):
  """Get config from kubeconfig file.

  Get config from potentially 3 different places, falling back to the next
  option as necessary:
  1. file_path specified as argument by the user
  2. List of file paths specified in $KUBECONFIG
  3. Default config path (~/.kube/config)

  Args:
    args: Namespace, The args namespace.

  Returns:
    dict: config object

  Raises:
    KubeconfigError: if $KUBECONFIG is set but contains no valid paths
  """
  if getattr(args, 'kubeconfig', None):
    return kubeconfig.Kubeconfig.LoadFromFile(
        files.ExpandHomeDir(args.kubeconfig))
  if encoding.GetEncodedValue(os.environ, 'KUBECONFIG'):
    config_paths = encoding.GetEncodedValue(os.environ,
                                            'KUBECONFIG').split(os.pathsep)
    config = None
    # Merge together all valid paths into single config
    for path in config_paths:
      try:
        other_config = kubeconfig.Kubeconfig.LoadFromFile(
            files.ExpandHomeDir(path))
        if not config:
          config = other_config
        else:
          config.Merge(other_config)
      except kubeconfig.Error:
        pass
    if not config:
      raise KubeconfigError('No valid file paths found in $KUBECONFIG')
    return config
  return kubeconfig.Kubeconfig.LoadFromFile(
      files.ExpandHomeDir(_DEFAULT_KUBECONFIG_PATH))


def FlagIsExplicitlySet(args, flag):
  """Return True if --flag is explicitly passed by the user."""
  # hasattr check is to allow the same code to work for release tracks that
  # don't have the args at all yet.
  return hasattr(args, flag) and args.IsSpecified(flag)


def VerifyOnePlatformFlags(args, release_track, product):
  """Raise ConfigurationError if args includes GKE only arguments."""
  error_msg = ('The `{flag}` flag is not supported on the fully managed '
               'version of Cloud Run. Specify `--platform {platform}` or run '
               '`gcloud config set run/platform {platform}` to work with '
               '{platform_desc}.')

  if FlagIsExplicitlySet(args, 'connectivity'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--connectivity=[internal|external]',
            platform=PLATFORM_GKE,
            platform_desc=_PLATFORM_SHORT_DESCRIPTIONS[PLATFORM_GKE]))

  if FlagIsExplicitlySet(args, 'namespace'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--namespace',
            platform=PLATFORM_GKE,
            platform_desc=_PLATFORM_SHORT_DESCRIPTIONS[PLATFORM_GKE]))

  if FlagIsExplicitlySet(args, 'cluster'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--cluster',
            platform=PLATFORM_GKE,
            platform_desc=_PLATFORM_SHORT_DESCRIPTIONS[PLATFORM_GKE]))

  if FlagIsExplicitlySet(args, 'cluster_location'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--cluster-location',
            platform=PLATFORM_GKE,
            platform_desc=_PLATFORM_SHORT_DESCRIPTIONS[PLATFORM_GKE]))

  if _HasSecretsChanges(args):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--[update|set|remove|clear]-secrets',
            platform=PLATFORM_GKE,
            platform_desc=_PLATFORM_SHORT_DESCRIPTIONS[PLATFORM_GKE]))

  if _HasConfigMapsChanges(args):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--[update|set|remove|clear]-config-maps',
            platform=PLATFORM_GKE,
            platform_desc=_PLATFORM_SHORT_DESCRIPTIONS[PLATFORM_GKE]))

  if FlagIsExplicitlySet(args, 'use_http2'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--[no-]-use-http2',
            platform=PLATFORM_GKE,
            platform_desc=_PLATFORM_SHORT_DESCRIPTIONS[PLATFORM_GKE]))

  if FlagIsExplicitlySet(args, 'broker'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--broker',
            platform=PLATFORM_GKE,
            platform_desc=_PLATFORM_SHORT_DESCRIPTIONS[PLATFORM_GKE]))

  if FlagIsExplicitlySet(args, 'custom_type') and product == Product.EVENTS:
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--custom-type',
            platform=PLATFORM_GKE,
            platform_desc=_PLATFORM_SHORT_DESCRIPTIONS[PLATFORM_GKE]))

  if FlagIsExplicitlySet(args, 'kubeconfig'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--kubeconfig',
            platform=PLATFORM_KUBERNETES,
            platform_desc=_PLATFORM_SHORT_DESCRIPTIONS[PLATFORM_KUBERNETES]))

  if FlagIsExplicitlySet(args, 'context'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--context',
            platform=PLATFORM_KUBERNETES,
            platform_desc=_PLATFORM_SHORT_DESCRIPTIONS[PLATFORM_KUBERNETES]))

  if (FlagIsExplicitlySet(args, 'min_instances') and
      release_track != base.ReleaseTrack.ALPHA):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--min-instances',
            platform=PLATFORM_KUBERNETES,
            platform_desc=_PLATFORM_SHORT_DESCRIPTIONS[PLATFORM_KUBERNETES]))

  if (FlagIsExplicitlySet(args, 'timeout') and
      release_track == base.ReleaseTrack.GA):
    if args.timeout > _FIFTEEN_MINUTES:
      raise serverless_exceptions.ConfigurationError(
          'Timeout duration must be less than 15m.')


def VerifyGKEFlags(args, release_track, product):
  """Raise ConfigurationError if args includes OnePlatform only arguments."""
  error_msg = ('The `{flag}` flag is not supported with Cloud Run for Anthos '
               'deployed on Google Cloud. Specify `--platform {platform}` or '
               'run `gcloud config set run/platform {platform}` to work with '
               '{platform_desc}.')

  if FlagIsExplicitlySet(args, 'allow_unauthenticated'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--allow-unauthenticated',
            platform=PLATFORM_MANAGED,
            platform_desc=_PLATFORM_SHORT_DESCRIPTIONS[PLATFORM_MANAGED]))

  if (release_track != base.ReleaseTrack.ALPHA and
      FlagIsExplicitlySet(args, 'service_account') and product == Product.RUN):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--service-account',
            platform=PLATFORM_MANAGED,
            platform_desc=_PLATFORM_SHORT_DESCRIPTIONS[PLATFORM_MANAGED]))

  if FlagIsExplicitlySet(args, 'region'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--region',
            platform=PLATFORM_MANAGED,
            platform_desc=_PLATFORM_SHORT_DESCRIPTIONS[PLATFORM_MANAGED]))

  if FlagIsExplicitlySet(args, 'vpc_connector'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--vpc-connector',
            platform=PLATFORM_MANAGED,
            platform_desc=_PLATFORM_SHORT_DESCRIPTIONS[PLATFORM_MANAGED]))

  if FlagIsExplicitlySet(args, 'clear_vpc_connector'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--clear-vpc-connector',
            platform=PLATFORM_MANAGED,
            platform_desc=_PLATFORM_SHORT_DESCRIPTIONS[PLATFORM_MANAGED]))

  if FlagIsExplicitlySet(args, 'kubeconfig'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--kubeconfig',
            platform=PLATFORM_KUBERNETES,
            platform_desc=_PLATFORM_SHORT_DESCRIPTIONS[PLATFORM_KUBERNETES]))

  if FlagIsExplicitlySet(args, 'context'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--context',
            platform=PLATFORM_KUBERNETES,
            platform_desc=_PLATFORM_SHORT_DESCRIPTIONS[PLATFORM_KUBERNETES]))


def VerifyKubernetesFlags(args, release_track, product):
  """Raise ConfigurationError if args includes OnePlatform or GKE only arguments."""
  error_msg = ('The `{flag}` flag is not supported with Cloud Run for Anthos '
               'deployed on VMware. Specify `--platform {platform}` or run '
               '`gcloud config set run/platform {platform}` to work with '
               '{platform_desc}.')

  if FlagIsExplicitlySet(args, 'allow_unauthenticated'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--allow-unauthenticated',
            platform=PLATFORM_MANAGED,
            platform_desc=_PLATFORM_SHORT_DESCRIPTIONS[PLATFORM_MANAGED]))

  if (release_track != base.ReleaseTrack.ALPHA and
      FlagIsExplicitlySet(args, 'service_account') and product == Product.RUN):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--service-account',
            platform=PLATFORM_MANAGED,
            platform_desc=_PLATFORM_SHORT_DESCRIPTIONS[PLATFORM_MANAGED]))

  if FlagIsExplicitlySet(args, 'region'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--region',
            platform=PLATFORM_MANAGED,
            platform_desc=_PLATFORM_SHORT_DESCRIPTIONS[PLATFORM_MANAGED]))

  if FlagIsExplicitlySet(args, 'vpc_connector'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--vpc-connector',
            platform='managed',
            platform_desc=_PLATFORM_SHORT_DESCRIPTIONS['managed']))

  if FlagIsExplicitlySet(args, 'clear_vpc_connector'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--clear-vpc-connector',
            platform=PLATFORM_MANAGED,
            platform_desc=_PLATFORM_SHORT_DESCRIPTIONS[PLATFORM_MANAGED]))

  if FlagIsExplicitlySet(args, 'cluster'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--cluster',
            platform=PLATFORM_GKE,
            platform_desc=_PLATFORM_SHORT_DESCRIPTIONS[PLATFORM_GKE]))

  if FlagIsExplicitlySet(args, 'cluster_location'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--cluster-location',
            platform=PLATFORM_GKE,
            platform_desc=_PLATFORM_SHORT_DESCRIPTIONS[PLATFORM_GKE]))


def GetPlatform():
  """Returns the platform to run on.

  If not set by the user, this prompts the user to choose a platform and sets
  the property so future calls to this method do continue to prompt.

  Raises:
    ArgumentError: if not platform is specified and prompting is not allowed.
  """
  platform = properties.VALUES.run.platform.Get()
  if platform is None:
    if console_io.CanPrompt():
      platform_descs = [_PLATFORM_SHORT_DESCRIPTIONS[k] for k in _PLATFORMS]
      index = console_io.PromptChoice(
          platform_descs,
          message='Please choose a target platform:',
          cancel_option=True)
      platform = list(_PLATFORMS.keys())[index]
      # Set platform so we don't re-prompt on future calls to this method
      # and so it's available to anyone who wants to know the platform.
      properties.VALUES.run.platform.Set(platform)
      log.status.Print(
          'To specify the platform yourself, pass `--platform {0}`. '
          'Or, to make this the default target platform, run '
          '`gcloud config set run/platform {0}`.\n'.format(platform))
    else:
      raise ArgumentError(
          'No platform specified. Pass the `--platform` flag or set '
          'the [run/platform] property to specify a target platform.\n'
          'Available platforms:\n{}'.format('\n'.join(
              ['- {}: {}'.format(k, v) for k, v in _PLATFORMS.items()])))
  return platform


def GetAndValidatePlatform(args, release_track, product):
  """Returns the platform to run on."""
  platform = GetPlatform()
  if platform == PLATFORM_MANAGED:
    VerifyOnePlatformFlags(args, release_track, product)
  elif platform == PLATFORM_GKE:
    VerifyGKEFlags(args, release_track, product)
  elif platform == PLATFORM_KUBERNETES:
    VerifyKubernetesFlags(args, release_track, product)
  if platform not in _PLATFORMS:
    raise ArgumentError(
        'Invalid target platform specified: [{}].\n'
        'Available platforms:\n{}'.format(
            platform,
            '\n'.join(['- {}: {}'.format(k, v) for k, v in _PLATFORMS.items()
                      ])))
  return platform


def ValidatePlatformIsManaged(unused_ref, unused_args, req):
  """Validate the specified platform is managed.

  This method is referenced by the declaritive iam commands which only work
  against the managed platform.

  Args:
    unused_ref: ref to the service.
    unused_args: Namespace, The args namespace.
    req: The request to be made.

  Returns:
    Unmodified request
  """
  if GetPlatform() != PLATFORM_MANAGED:
    raise calliope_exceptions.BadArgumentException(
        '--platform', 'The platform [{platform}] is not supported by this '
        'operation. Specify `--platform {managed}` or run '
        '`gcloud config set run/platform {managed}`.'.format(
            platform=GetPlatform(), managed=PLATFORM_MANAGED))
  return req


def AddBuildTimeoutFlag(parser):
  parser.add_argument(
      '--build-timeout',
      hidden=True,
      help='Set the maximum request execution time (timeout) to build the '
      'resource. It is specified as a duration; for example, "10m5s" is ten '
      'minutes, and five seconds. If you don\'t specify a unit, seconds is '
      'assumed. For example, "10" is 10 seconds.',
      action=actions.StoreProperty(properties.VALUES.builds.timeout))


def AddSourceFlag(parser):
  """Add deploy source flags, an image or a source for build."""
  parser.add_argument(
      '--source',
      hidden=True,
      help='The location of the source to build. The location can be a '
      'directory on a local disk or a gzipped archive file (.tar.gz) in '
      'Google Cloud Storage. If the source is a local directory, this '
      'command skips the files specified in the `--ignore-file`. If '
      '`--ignore-file` is not specified, use`.gcloudignore` file. If a '
      '`.gitignore` file is present in the local source directory, gcloud '
      'will use a Git-compatible `.gcloudignore` file that respects your '
      '.gitignored files. The global `.gitignore` is not respected. For more '
      'information on `.gcloudignore`, see `gcloud topic gcloudignore`.',
  )
