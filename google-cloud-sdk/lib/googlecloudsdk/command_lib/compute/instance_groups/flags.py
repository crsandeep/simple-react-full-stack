# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Flags and helpers for the compute instance groups commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap
import enum
from googlecloudsdk.api_lib.compute import managed_instance_groups_utils
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.util import completers
import six


# TODO(b/110191362): resign from passing whole args to functions in this file


class RegionalInstanceGroupManagersCompleter(
    compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(RegionalInstanceGroupManagersCompleter, self).__init__(
        collection='compute.regionInstanceGroupManagers',
        list_command=('compute instance-groups managed list --uri '
                      '--filter=region:*'),
        **kwargs)


class ZonalInstanceGroupManagersCompleter(
    compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(ZonalInstanceGroupManagersCompleter, self).__init__(
        collection='compute.instanceGroupManagers',
        list_command=('compute instance-groups managed list --uri '
                      '--filter=zone:*'),
        **kwargs)


class InstanceGroupManagersCompleter(completers.MultiResourceCompleter):

  def __init__(self, **kwargs):
    super(InstanceGroupManagersCompleter, self).__init__(
        completers=[RegionalInstanceGroupManagersCompleter,
                    ZonalInstanceGroupManagersCompleter],
        **kwargs)


class AutoDeleteFlag(enum.Enum):
  """CLI flag values for `auto-delete' flag."""

  NEVER = 'never'
  ON_PERMANENT_INSTANCE_DELETION = 'on-permanent-instance-deletion'

  def GetAutoDeleteEnumValue(self, base_enum):
    return base_enum(self.name)

  @staticmethod
  def ValidateAutoDeleteFlag(flag_value, flag_name):
    values = [
        auto_delete_flag_value.value
        for auto_delete_flag_value in AutoDeleteFlag
    ]
    if flag_value not in values:
      raise exceptions.InvalidArgumentException(
          parameter_name=flag_name,
          message='Value for [auto-delete] must be [never] or '
          '[on-permanent-instance-deletion], not [{0}]'.format(flag_value))
    return AutoDeleteFlag(flag_value)

  @staticmethod
  def ValidatorWithFlagName(flag_name):
    def Validator(flag_value):
      return AutoDeleteFlag.ValidateAutoDeleteFlag(flag_value, flag_name)
    return Validator


def MakeZonalInstanceGroupArg(plural=False):
  return flags.ResourceArgument(
      resource_name='instance group',
      completer=compute_completers.InstanceGroupsCompleter,
      plural=plural,
      zonal_collection='compute.instanceGroups',
      zone_explanation=flags.ZONE_PROPERTY_EXPLANATION)

MULTISCOPE_INSTANCE_GROUP_ARG = flags.ResourceArgument(
    resource_name='instance group',
    completer=compute_completers.InstanceGroupsCompleter,
    zonal_collection='compute.instanceGroups',
    regional_collection='compute.regionInstanceGroups',
    zone_explanation=flags.ZONE_PROPERTY_EXPLANATION_NO_DEFAULT,
    region_explanation=flags.REGION_PROPERTY_EXPLANATION_NO_DEFAULT)

MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG = flags.ResourceArgument(
    resource_name='managed instance group',
    completer=InstanceGroupManagersCompleter,
    zonal_collection='compute.instanceGroupManagers',
    regional_collection='compute.regionInstanceGroupManagers',
    zone_explanation=flags.ZONE_PROPERTY_EXPLANATION_NO_DEFAULT,
    region_explanation=flags.REGION_PROPERTY_EXPLANATION_NO_DEFAULT)

MULTISCOPE_INSTANCE_GROUP_MANAGERS_ARG = flags.ResourceArgument(
    resource_name='managed instance group',
    plural=True,
    name='names',
    completer=InstanceGroupManagersCompleter,
    zonal_collection='compute.instanceGroupManagers',
    regional_collection='compute.regionInstanceGroupManagers',
    zone_explanation=flags.ZONE_PROPERTY_EXPLANATION_NO_DEFAULT,
    region_explanation=flags.REGION_PROPERTY_EXPLANATION_NO_DEFAULT)


def AddGroupArg(parser):
  parser.add_argument(
      'group',
      help='The name of the instance group.')


def AddNamedPortsArgs(parser):
  """Adds flags for handling named ports."""
  parser.add_argument(
      '--named-ports',
      required=True,
      type=arg_parsers.ArgList(),
      metavar='NAME:PORT',
      help="""\
          The comma-separated list of key:value pairs representing
          the service name and the port that it is running on.

          To clear the list of named ports pass empty list as flag value.
          For example:

            $ {command} example-instance-group --named-ports ""
          """)


def AddScopeArgs(parser, multizonal):
  """Adds flags for group scope."""
  if multizonal:
    scope_parser = parser.add_mutually_exclusive_group()
    flags.AddRegionFlag(
        scope_parser,
        resource_type='instance group',
        operation_type='set named ports for',
        explanation=flags.REGION_PROPERTY_EXPLANATION_NO_DEFAULT)
    flags.AddZoneFlag(
        scope_parser,
        resource_type='instance group',
        operation_type='set named ports for',
        explanation=flags.ZONE_PROPERTY_EXPLANATION_NO_DEFAULT)
  else:
    flags.AddZoneFlag(
        parser,
        resource_type='instance group',
        operation_type='set named ports for')


def AddZonesFlag(parser):
  """Add flags for choosing zones for regional managed instance group."""
  parser.add_argument(
      '--zones',
      metavar='ZONE',
      help="""\
          If this flag is specified a regional managed instance group will be
          created. The managed instance group will be in the same region as
          specified zones and will spread instances in it between specified
          zones.

          All zones must belong to the same region. You may specify --region
          flag but it must be the region to which zones belong. This flag is
          mutually exclusive with --zone flag.""",
      type=arg_parsers.ArgList(min_length=1),
      completer=compute_completers.ZonesCompleter,
      default=[])


def ValidateManagedInstanceGroupScopeArgs(args, resources):
  """Validate arguments specifying scope of the managed instance group."""
  ignored_required_params = {'project': 'fake'}
  if args.zones and args.zone:
    raise exceptions.ConflictingArgumentsException('--zone', '--zones')
  zone_names = []
  for zone in args.zones:
    zone_ref = resources.Parse(
        zone, collection='compute.zones', params=ignored_required_params)
    zone_names.append(zone_ref.Name())

  zone_regions = set([utils.ZoneNameToRegionName(z) for z in zone_names])
  if len(zone_regions) > 1:
    raise exceptions.InvalidArgumentException(
        '--zones', 'All zones must be in the same region.')
  elif len(zone_regions) == 1 and args.region:
    zone_region = zone_regions.pop()
    region_ref = resources.Parse(args.region, collection='compute.regions',
                                 params=ignored_required_params)
    region = region_ref.Name()
    if zone_region != region:
      raise exceptions.InvalidArgumentException(
          '--zones', 'Specified zones not in specified region.')


def ValidateStatefulDisksDict(stateful_disks, flag_name):
  """Validate device-name and auto-delete flags in a stateful disk for per-instance configs."""
  device_names = set()
  for stateful_disk in stateful_disks or []:
    if not stateful_disk.get('device-name'):
      raise exceptions.InvalidArgumentException(
          parameter_name=flag_name, message='[device-name] is required')
    if stateful_disk.get('device-name') in device_names:
      raise exceptions.InvalidArgumentException(
          parameter_name=flag_name,
          message='[device-name] `{0}` is not unique in the collection'.format(
              stateful_disk.get('device-name')))
    device_names.add(stateful_disk.get('device-name'))


def ValidateManagedInstanceGroupStatefulProperties(args):
  ValidateStatefulDisksDict(args.stateful_disk, '--stateful-disk')


def GetInstanceGroupManagerArg(zones_flag=False, region_flag=True):
  """Returns ResourceArgument for working with instance group managers."""
  if zones_flag:
    extra_region_info_about_zones_flag = (
        '\n\nIf you specify `--zones` flag this flag must be unspecified '
        'or specify the region to which the zones you listed belong.'
    )
    region_explanation = (flags.REGION_PROPERTY_EXPLANATION_NO_DEFAULT +
                          extra_region_info_about_zones_flag)
  else:
    region_explanation = flags.REGION_PROPERTY_EXPLANATION_NO_DEFAULT
  if region_flag:
    regional_collection = 'compute.regionInstanceGroupManagers'
  else:
    regional_collection = None
  return flags.ResourceArgument(
      resource_name='managed instance group',
      completer=InstanceGroupManagersCompleter,
      zonal_collection='compute.instanceGroupManagers',
      regional_collection=regional_collection,
      zone_explanation=flags.ZONE_PROPERTY_EXPLANATION_NO_DEFAULT,
      region_explanation=region_explanation)


def CreateGroupReference(client, resources, args):
  resource_arg = GetInstanceGroupManagerArg()
  default_scope = compute_scope.ScopeEnum.ZONE
  scope_lister = flags.GetDefaultScopeLister(client)
  return resource_arg.ResolveAsResource(
      args, resources, default_scope=default_scope,
      scope_lister=scope_lister)


_LIST_INSTANCES_FORMAT = """\
        table(instance.basename():label=NAME,
              instance.scope().segment(0):label=ZONE,
              instanceStatus:label=STATUS,
              instanceHealth[0].detailedHealthState:label=HEALTH_STATE,
              currentAction:label=ACTION,
              version.instanceTemplate.basename():label=INSTANCE_TEMPLATE,
              version.name:label=VERSION_NAME,
              lastAttempt.errors.errors.map().format(
                "Error {0}: {1}", code, message).list(separator=", ")
                :label=LAST_ERROR
        )"""

_LIST_INSTANCES_FORMAT_BETA = """\
        table(instance.basename():label=NAME,
              instance.scope().segment(0):label=ZONE,
              instanceStatus:label=STATUS,
              instanceHealth[0].detailedHealthState:label=HEALTH_STATE,
              currentAction:label=ACTION,
              preservedState():label=PRESERVED_STATE,
              version.instanceTemplate.basename():label=INSTANCE_TEMPLATE,
              version.name:label=VERSION_NAME,
              lastAttempt.errors.errors.map().format(
                "Error {0}: {1}", code, message).list(separator=", ")
                :label=LAST_ERROR
        )"""

_LIST_INSTANCES_FORMAT_ALPHA = """\
        table(instance.basename():label=NAME,
              instance.scope().segment(0):label=ZONE,
              instanceStatus:label=STATUS,
              instanceHealth[0].detailedHealthState:label=HEALTH_STATE,
              currentAction:label=ACTION,
              preservedState():label=PRESERVED_STATE,
              version.instanceTemplate.basename():label=INSTANCE_TEMPLATE,
              version.name:label=VERSION_NAME,
              lastAttempt.errors.errors.map().format(
                "Error {0}: {1}", code, message).list(separator=", ")
                :label=LAST_ERROR
        )"""

_RELEASE_TRACK_TO_LIST_INSTANCES_FORAMT = {
    base.ReleaseTrack.GA: _LIST_INSTANCES_FORMAT,
    base.ReleaseTrack.BETA: _LIST_INSTANCES_FORMAT_BETA,
    base.ReleaseTrack.ALPHA: _LIST_INSTANCES_FORMAT_ALPHA,
}


def _TransformPreservedState(instance):
  """Transform for the PRESERVED_STATE field in the table output.

  PRESERVED_STATE is generated from the fields preservedStateFromPolicy and
  preservedStateFromConfig fields in the managedInstance message.

  Args:
    instance: instance dictionary for transform

  Returns:
    Preserved state status as one of ('POLICY', 'CONFIG', 'POLICY,CONFIG')
  """
  preserved_state_value = ''
  if ('preservedStateFromPolicy' in instance and
      instance['preservedStateFromPolicy']):
    preserved_state_value += 'POLICY,'
  if ('preservedStateFromConfig' in instance and
      instance['preservedStateFromConfig']):
    preserved_state_value += 'CONFIG'
  if preserved_state_value.endswith(','):
    preserved_state_value = preserved_state_value[:-1]
  return preserved_state_value


def AddListInstancesOutputFormat(parser, release_track=base.ReleaseTrack.GA):
  parser.display_info.AddTransforms({
      'preservedState': _TransformPreservedState,
  })
  parser.display_info.AddFormat(
      _RELEASE_TRACK_TO_LIST_INSTANCES_FORAMT[release_track])


def AddSettingStatefulDisksFlag(parser, required=False):
  """Add --stateful-disks and --no-stateful-disks flags to the parser."""
  # TODO(b/69900323): merge this function with AddMigStatefulFlags
  stateful_disks = parser.add_mutually_exclusive_group(required=required)
  stateful_disks.add_argument(
      '--stateful-disks',
      metavar='DEVICE_NAME',
      type=arg_parsers.ArgList(min_length=1),
      help=('Disks, specified in the group\'s instance template, to consider '
            'stateful. Usually, a managed instance group deletes and recreates '
            'disks from their original images when recreating instances; '
            'however, in the case of stateful disks, these disks are detached '
            'and reattached when the instance is recreated.'),
  )
  stateful_disks.add_argument(
      '--no-stateful-disks',
      action='store_true',
      help='The group will have no stateful disks.',
  )

# Rename ot HELP_BASE
STATEFUL_DISKS_HELP_BASE = """
      Disks considered stateful by the instance group. Managed instance groups
      preserve and reattach stateful disks on VM autohealing, update, and
      recreate events.
      """

STATEFUL_DISKS_HELP_INSTANCE_CONFIGS = STATEFUL_DISKS_HELP_BASE + """
      You can also attach and preserve disks, not defined in the group's
      instance template, to a given instance.

      The same disk can be attached to more than one instance but only in
      read-only mode.
      """

STATEFUL_DISKS_HELP_INSTANCE_CONFIGS_UPDATE = (
    STATEFUL_DISKS_HELP_INSTANCE_CONFIGS + """
      Use this argument multiple times to update multiple disks.

      If stateful disk with given `device-name` exists in current instance
      config, its properties will be replaced by the newly provided ones. In
      other case new stateful disk definition will be added to the instance
      config.
      """)

STATEFUL_DISK_DEVICE_NAME_ARG_HELP = """
      *device-name*::: Name under which disk is or will be attached.
      """

STATEFUL_DISK_SOURCE_ARG_HELP = """
      *source*::: Optional argument used to specify the URI of an existing
      persistent disk to attach under specified `device-name`.
      """

STATEFUL_DISK_MODE_ARG_HELP = """
      *mode*::: Specifies the mode of the disk to attach. Supported options are
      `ro` for read-only and `rw` for read-write. If omitted when source is
      specified, `rw` is used as a default. `mode` can only be specified if
      `source` is given.
      """

STATEFUL_DISK_AUTO_DELETE_ARG_HELP = """
      *auto-delete*::: (Optional) Specifies the auto deletion policy of the
      stateful disk. Supported values are ``never'' (never delete this disk) and
      ``on-permanent-instance-deletion'' (delete the stateful disk when the
      given instance is permanently deleted from the instance group; for example
      when the group is resized down). If omitted, ``never'' is used as the
      default.
      """

STATEFUL_METADATA_HELP = """
      Additional metadata to be made available to the guest operating system
      in addition to the metadata defined in the instance template.

      Stateful metadata may be used to define a key/value pair specific for
      the one given instance to differentiate it from the other instances in
      the managed instance group.

      Stateful metadata key/value pairs are preserved on instance recreation,
      autohealing, updates, and any other lifecycle transitions of the
      instance.

      Stateful metadata have priority over the metadata defined in the
      instance template. This means that stateful metadata that is defined for a
      key that already exists in the instance template overrides the instance
      template value.

      Each metadata entry is a key/value pair separated by an equals sign.
      Metadata keys must be unique and less than 128 bytes in length. Multiple
      entries can be passed to this flag, e.g.,
      ``{argument_name} key-1=value-1,key-2=value-2,key-3=value-3''.
      """

STATEFUL_METADATA_HELP_UPDATE = """
      If stateful metadata with the given key exists in current instance config,
      its value will be overridden with the newly provided one. If the key does
      not exist in the current instance config, a new key/value pair will be
      added.
      """


def AddMigCreateStatefulFlags(parser):
  """Adding stateful flags for disks and names to the parser."""
  stateful_disks_help = textwrap.dedent(STATEFUL_DISKS_HELP_BASE + """
      Use this argument multiple times to attach more disks.

      *device-name*::: (Requied) Device name of the disk to mark stateful.
      """ + STATEFUL_DISK_AUTO_DELETE_ARG_HELP)
  parser.add_argument(
      '--stateful-disk',
      type=arg_parsers.ArgDict(
          spec={
              'device-name':
                  str,
              'auto-delete': AutoDeleteFlag.ValidatorWithFlagName(
                  '--stateful_disk'),
          }),
      action='append',
      help=stateful_disks_help,
  )


def _AddMigStatefulInstanceConfigsInstanceArg(parser):
  parser.add_argument(
      '--instance',
      required=True,
      help="""
        URI/name of an existing instance in the managed instance group.
      """)


def AddMigStatefulFlagsForUpdateInstanceConfigs(parser):
  """Add args for per-instance configs update command."""
  _AddMigStatefulInstanceConfigsInstanceArg(parser)

  # Add stateful disk update args
  stateful_disk_argument_name = '--stateful-disk'
  stateful_disk_argument_name_old = '--update-stateful-disk'
  disk_help_text = textwrap.dedent(
      (STATEFUL_DISKS_HELP_INSTANCE_CONFIGS_UPDATE +
       STATEFUL_DISK_DEVICE_NAME_ARG_HELP + STATEFUL_DISK_SOURCE_ARG_HELP +
       STATEFUL_DISK_MODE_ARG_HELP + STATEFUL_DISK_AUTO_DELETE_ARG_HELP))
  parser.add_argument(
      stateful_disk_argument_name,
      type=arg_parsers.ArgDict(
          spec={
              'device-name':
                  str,
              'source':
                  str,
              'mode':
                  str,
              'auto-delete':
                  AutoDeleteFlag.ValidatorWithFlagName(
                      stateful_disk_argument_name)
          }),
      action='append',
      help=disk_help_text,
  )
  # DEPRECATED: --update-stateful-disk
  parser.add_argument(
      stateful_disk_argument_name_old,
      type=arg_parsers.ArgDict(
          spec={
              'device-name':
                  str,
              'source':
                  str,
              'mode':
                  str,
              'auto-delete':
                  AutoDeleteFlag.ValidatorWithFlagName(
                      stateful_disk_argument_name_old)
          }),
      action=actions.DeprecationAction(
          stateful_disk_argument_name_old,
          warn='The {flag_name} option is deprecated; '
          'use --stateful-disk instead.',
          removed=False,
          action='append'),
      dest='stateful_disk',
      help=disk_help_text)
  # Add remove disk args
  parser.add_argument(
      '--remove-stateful-disks',
      metavar='DEVICE_NAME',
      type=arg_parsers.ArgList(min_length=1),
      help='List all device names to remove from the instance\'s config.',
  )

  # Add stateful metadata args
  stateful_metadata_argument_name = '--stateful-metadata'
  stateful_metadata_argument_name_old = '--update-stateful-metadata'
  metadata_help_text = textwrap.dedent(
      (STATEFUL_METADATA_HELP + STATEFUL_METADATA_HELP_UPDATE).format(
          argument_name=stateful_metadata_argument_name))
  parser.add_argument(
      stateful_metadata_argument_name,
      type=arg_parsers.ArgDict(min_length=1),
      default={},
      action=arg_parsers.StoreOnceAction,
      metavar='KEY=VALUE',
      help=textwrap.dedent(metadata_help_text))
  # DEPRECATED: --update-stateful-metadata
  parser.add_argument(
      stateful_metadata_argument_name_old,
      type=arg_parsers.ArgDict(min_length=1),
      default={},
      action=actions.DeprecationAction(
          stateful_metadata_argument_name_old,
          warn='The {flag_name} option is deprecated; '
          'use --stateful-metadata instead.',
          removed=False,
          action=arg_parsers.StoreOnceAction),
      metavar='KEY=VALUE',
      dest='stateful_metadata',
      help=textwrap.dedent(metadata_help_text))
  parser.add_argument(
      '--remove-stateful-metadata',
      metavar='KEY',
      type=arg_parsers.ArgList(min_length=1),
      help=('List all stateful metadata keys to remove from the'
            'instance\'s config.'),
  )


def AddMigStatefulFlagsForInstanceConfigs(parser):
  """Adding stateful flags for creating instance configs."""
  _AddMigStatefulInstanceConfigsInstanceArg(parser)

  # Add stateful disk args
  stateful_disk_argument_name = '--stateful-disk'
  stateful_disks_help = textwrap.dedent(
      (STATEFUL_DISKS_HELP_INSTANCE_CONFIGS + """
        Use this argument multiple times to attach and preserve multiple disks.
      """ + STATEFUL_DISK_DEVICE_NAME_ARG_HELP + STATEFUL_DISK_SOURCE_ARG_HELP +
       STATEFUL_DISK_MODE_ARG_HELP + STATEFUL_DISK_AUTO_DELETE_ARG_HELP))
  parser.add_argument(
      stateful_disk_argument_name,
      type=arg_parsers.ArgDict(
          spec={
              'device-name':
                  str,
              'source':
                  str,
              'mode':
                  str,
              'auto-delete':
                  AutoDeleteFlag.ValidatorWithFlagName(
                      stateful_disk_argument_name)
          }),
      action='append',
      help=stateful_disks_help,
  )

  # Add stateful metdata args
  stateful_metadata_argument_name = '--stateful-metadata'
  metadata_help_text = textwrap.dedent(
      STATEFUL_METADATA_HELP.format(
          argument_name=stateful_metadata_argument_name))
  parser.add_argument(
      stateful_metadata_argument_name,
      type=arg_parsers.ArgDict(min_length=1),
      default={},
      action=arg_parsers.StoreOnceAction,
      metavar='KEY=VALUE',
      help=metadata_help_text)


def AddCreateInstancesFlags(parser, add_stateful_args=True):
  """Adding stateful flags for creating and updating instance configs."""
  parser.add_argument(
      '--instance',
      required=True,
      help="""Name of the new instance to create.""")
  if add_stateful_args:
    parser.add_argument(
        '--stateful-disk',
        type=arg_parsers.ArgDict(
            spec={
                'device-name':
                    str,
                'source':
                    str,
                'mode':
                    str,
                'auto-delete':
                    AutoDeleteFlag.ValidatorWithFlagName('--stateful-disk'),
            }),
        action='append',
        help=textwrap.dedent(STATEFUL_DISKS_HELP_INSTANCE_CONFIGS),
    )
    stateful_metadata_argument_name = '--stateful-metadata'
    parser.add_argument(
        stateful_metadata_argument_name,
        type=arg_parsers.ArgDict(min_length=1),
        default={},
        action=arg_parsers.StoreOnceAction,
        metavar='KEY=VALUE',
        help=textwrap.dedent(
            STATEFUL_METADATA_HELP.format(
                argument_name=stateful_metadata_argument_name)))


def AddMigStatefulUpdateInstanceFlag(parser):
  parser.add_argument(
      '--update-instance',
      default=True,
      action='store_true',
      help="""
          Apply the configuration changes immediately to the instance. If you
          disable this flag, the managed instance group will apply the config
          update when you next recreate or update the instance.

          Example: say you have an instance with a disk attached to it and you
          created a stateful config for the disk. If you decide to delete the
          stateful config for the disk and you provide this flag, the MIG
          immediately refreshes the instance and removes the stateful config
          for the disk. Similarly if you have attached a new disk or changed its
          definition, with this flag the MIG immediately refreshes the instance
          with the new config.""")


def ValidateMigStatefulFlagsForInstanceConfigs(args,
                                               for_update=False,
                                               need_disk_source=False):
  """Validates the values of stateful flags for instance configs."""
  if for_update:
    stateful_disks = args.stateful_disk
    flag_name = '--stateful-disk'
  else:
    stateful_disks = args.stateful_disk
    flag_name = '--stateful-disk'
  device_names = set()
  for stateful_disk in stateful_disks or []:
    if not stateful_disk.get('device-name'):
      raise exceptions.InvalidArgumentException(
          parameter_name=flag_name, message='[device-name] is required')

    if stateful_disk.get('device-name') in device_names:
      raise exceptions.InvalidArgumentException(
          parameter_name=flag_name,
          message='[device-name] `{0}` is not unique in the collection'.format(
              stateful_disk.get('device-name')))
    device_names.add(stateful_disk.get('device-name'))

    mode_value = stateful_disk.get('mode')
    if mode_value and mode_value not in ('rw', 'ro'):
      raise exceptions.InvalidArgumentException(
          parameter_name=flag_name,
          message='Value for [mode] must be [rw] or [ro], not [{0}]'.format(
              mode_value))

    if need_disk_source and not stateful_disk.get('source'):
      raise exceptions.InvalidArgumentException(
          parameter_name=flag_name,
          message='[source] is required for all stateful disks')

    if mode_value and not stateful_disk.get('source'):
      raise exceptions.InvalidArgumentException(
          parameter_name=flag_name,
          message='[mode] can be set then and only then when [source] is given')

  if for_update:
    remove_stateful_disks_set = set(args.remove_stateful_disks or [])
    for stateful_disk_to_update in args.stateful_disk or []:
      if stateful_disk_to_update.get(
          'device-name') in remove_stateful_disks_set:
        raise exceptions.InvalidArgumentException(
            parameter_name=flag_name,
            message=('the same [device-name] `{0}` cannot be updated and'
                     ' removed in one command call'.format(
                         stateful_disk_to_update.get('device-name'))))

    remove_stateful_metadata_set = set(args.remove_stateful_metadata or [])
    update_stateful_metadata_set = set(args.stateful_metadata.keys())
    keys_intersection = remove_stateful_metadata_set.intersection(
        update_stateful_metadata_set)
    if keys_intersection:
      raise exceptions.InvalidArgumentException(
          parameter_name=flag_name,
          message=('the same metadata key(s) `{0}` cannot be updated and'
                   ' removed in one command call'.format(
                       ', '.join(keys_intersection))))


def AddMigUpdateStatefulFlags(parser):
  """Add --stateful-disk and --remove-stateful-disks to the parser."""
  stateful_disks_help = textwrap.dedent(STATEFUL_DISKS_HELP_BASE + """
      Use this argument multiple times to update more disks.

      If stateful disk with given `device-name` exists in current instance
      config, its properties will be replaced by the newly provided ones. In
      other case new stateful disk definition will be added to the instance
      config.

      *device-name*::: (Requied) Device name of the disk to mark stateful.
      """ + STATEFUL_DISK_AUTO_DELETE_ARG_HELP)
  stateful_disk_flag_name = '--stateful-disk'
  stateful_disk_flag_name_old = '--update-stateful-disk'
  parser.add_argument(
      stateful_disk_flag_name,
      type=arg_parsers.ArgDict(
          spec={
              'device-name':
                  str,
              'auto-delete':
                  AutoDeleteFlag.ValidatorWithFlagName(stateful_disk_flag_name)
          }),
      action='append',
      help=stateful_disks_help,
  )

  # DEPRECATED: --update-stateful-disk
  parser.add_argument(
      stateful_disk_flag_name_old,
      type=arg_parsers.ArgDict(
          spec={
              'device-name':
                  str,
              'auto-delete':
                  AutoDeleteFlag.ValidatorWithFlagName(
                      stateful_disk_flag_name_old)
          }),
      action=actions.DeprecationAction(
          stateful_disk_flag_name_old,
          warn='The {flag_name} option is deprecated; '
          'use --stateful-disk instead.',
          removed=False,
          action='append'),
      dest='stateful_disk',
      help=stateful_disks_help,
  )
  parser.add_argument(
      '--remove-stateful-disks',
      metavar='DEVICE_NAME',
      type=arg_parsers.ArgList(min_length=1),
      help='Stop considering the disks stateful by the instance group.',
  )


def ValidateUpdateStatefulPolicyParams(args, current_stateful_policy):
  """Check stateful properties of update request."""
  current_device_names = set(
      managed_instance_groups_utils.GetDeviceNamesFromStatefulPolicy(
          current_stateful_policy))
  update_disk_names = []
  if args.stateful_disk:
    ValidateStatefulDisksDict(args.stateful_disk, '--stateful-disk')
    update_disk_names = [
        stateful_disk.get('device-name') for stateful_disk in args.stateful_disk
    ]
  if args.remove_stateful_disks:
    if any(
        args.remove_stateful_disks.count(x) > 1
        for x in args.remove_stateful_disks):
      raise exceptions.InvalidArgumentException(
          parameter_name='update',
          message=(
              'When removing device names from Stateful Policy, please provide '
              'each name exactly once.'))

  update_set = set(update_disk_names)
  remove_set = set(args.remove_stateful_disks or [])
  intersection = update_set.intersection(remove_set)

  if intersection:
    raise exceptions.InvalidArgumentException(
        parameter_name='update',
        message=
        ('You cannot simultaneously add and remove the same device names {} to '
         'Stateful Policy.'.format(six.text_type(intersection))))
  not_current_device_names = remove_set - current_device_names
  if not_current_device_names:
    raise exceptions.InvalidArgumentException(
        parameter_name='update',
        message=('Disks [{}] are not currently set as stateful, '
                 'so they cannot be removed from Stateful Policy.'.format(
                     six.text_type(not_current_device_names))))


INSTANCE_REDISTRIBUTION_TYPES = ['NONE', 'PROACTIVE']


def AddMigInstanceRedistributionTypeFlag(parser):
  """Add --instance-redistribution-type flag to the parser."""
  parser.add_argument(
      '--instance-redistribution-type',
      metavar='TYPE',
      type=lambda x: x.upper(),
      choices=INSTANCE_REDISTRIBUTION_TYPES,
      help="""\
      Specifies the type of the instance redistribution policy. An instance
      redistribution type lets you enable or disable automatic instance
      redistribution across zones to meet the target distribution. The target
      distribution is a state of a regional managed instance group where all
      instances are spread out evenly across all target zones.

      An instance redistribution type can be specified only for a non-autoscaled
      regional managed instance group. By default it is set to PROACTIVE.

      The following types are available:

       * NONE - The managed instance group does not redistribute instances
         across zones.

       * PROACTIVE - The managed instance group proactively redistributes
         instances to meet its target distribution.
      """)


def ValidateMigInstanceRedistributionTypeFlag(instance_redistribution_type,
                                              group_ref):
  """Check correctness of instance-redistribution-type flag value."""
  if instance_redistribution_type and (group_ref.Collection() !=
                                       'compute.regionInstanceGroupManagers'):
    raise exceptions.InvalidArgumentException(
        parameter_name='--instance-redistribution-type',
        message=(
            'Flag --instance-redistribution-type may be specified for regional '
            'managed instance groups only.'))


DISTRIBUTION_POLICY_TARGET_SHAPES = ['EVEN', 'ANY']


def AddMigDistributionPolicyTargetShapeFlag(parser):
  """Add --target-distribution-shape flag to the parser."""
  parser.add_argument(
      '--target-distribution-shape',
      metavar='SHAPE',
      type=lambda x: x.upper(),
      choices=DISTRIBUTION_POLICY_TARGET_SHAPES,
      help="""\
      Specify distribution policy target shape.

      Target shape may be specified for regional managed instance group only.
      By default it is set to EVEN.

      The following target shapes are available:

       * EVEN - managed instance group will create and delete instances
         in a manner preserving or converging to even distribution.

       * ANY - managed instance group will create instances based on present
         capacity constraints and will not attempt to converge to even
         distribution.
      """)


def ValidateMigDistributionPolicyTargetShapeFlag(target_shape, group_ref):
  """Check correctness of --target-distribution-shape flag value."""
  if target_shape and (group_ref.Collection() !=
                       'compute.regionInstanceGroupManagers'):
    raise exceptions.InvalidArgumentException(
        parameter_name='--target-distribution-shape',
        message=('Flag --target-distribution-shape may be specified for '
                 'regional managed instance groups only.'))
