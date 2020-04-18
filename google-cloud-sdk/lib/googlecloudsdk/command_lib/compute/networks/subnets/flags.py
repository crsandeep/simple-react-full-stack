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
"""Flags and helpers for the compute subnetworks commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import utils as compute_api
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.util.apis import arg_utils

DEFAULT_LIST_FORMAT = """\
    table(
      name,
      region.basename(),
      network.basename(),
      ipCidrRange:label=RANGE
    )"""


class SubnetworksCompleter(compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(SubnetworksCompleter, self).__init__(
        collection='compute.subnetworks',
        list_command='beta compute networks subnets list --uri',
        api_version='beta',
        **kwargs)


def SubnetworkArgument(required=True, plural=False):
  return compute_flags.ResourceArgument(
      resource_name='subnetwork',
      completer=SubnetworksCompleter,
      plural=plural,
      required=required,
      regional_collection='compute.subnetworks',
      region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION)


def SubnetworkResolver():
  return compute_flags.ResourceResolver.FromMap(
      'subnetwork', {compute_scope.ScopeEnum.REGION: 'compute.subnetworks'})


def AddUpdateArgs(parser, include_alpha_logging,
                  include_l7_internal_load_balancing,
                  include_private_ipv6_access_alpha,
                  include_private_ipv6_access_beta):
  """Add args to the parser for subnet update.

  Args:
    parser: The argparse parser.
    include_alpha_logging: Include alpha-specific logging args.
    include_l7_internal_load_balancing: Include Internal HTTP(S) LB args.
    include_private_ipv6_access_alpha: Include alpha Private Ipv6 Access args.
    include_private_ipv6_access_beta: Include beta Private Ipv6 Access args.
  """
  messages = apis.GetMessagesModule('compute',
                                    compute_api.COMPUTE_GA_API_VERSION)

  updated_field = parser.add_mutually_exclusive_group()

  updated_field.add_argument(
      '--enable-private-ip-google-access',
      action=arg_parsers.StoreTrueFalseAction,
      help=('Enable/disable access to Google Cloud APIs from this subnet for '
            'instances without a public ip address.'))

  updated_field.add_argument(
      '--add-secondary-ranges',
      type=arg_parsers.ArgDict(min_length=1),
      action='append',
      metavar='PROPERTY=VALUE',
      help="""\
      Adds secondary IP ranges to the subnetwork for use in IP aliasing.

      For example, `--add-secondary-ranges range1=192.168.64.0/24` adds
      a secondary range 192.168.64.0/24 with name range1.

      * `RANGE_NAME` - Name of the secondary range.
      * `RANGE` - `IP range in CIDR format.`
      """)

  updated_field.add_argument(
      '--remove-secondary-ranges',
      type=arg_parsers.ArgList(min_length=1),
      action='append',
      metavar='PROPERTY=VALUE',
      help="""\
      Removes secondary ranges from the subnetwork.

      For example, `--remove-secondary-ranges range2,range3` removes the
      secondary ranges with names range2 and range3.
      """)

  updated_field.add_argument(
      '--enable-flow-logs',
      action=arg_parsers.StoreTrueFalseAction,
      help=('Enable/disable VPC Flow Logs for this subnet. More information '
            'for VPC Flow Logs can be found at '
            'https://cloud.google.com/vpc/docs/using-flow-logs.'))

  AddLoggingAggregationInterval(parser, messages)
  parser.add_argument(
      '--logging-flow-sampling',
      type=arg_parsers.BoundedFloat(lower_bound=0.0, upper_bound=1.0),
      help="""\
      Can only be specified if VPC Flow logs for this subnetwork is
      enabled. The value of the field must be in [0, 1]. Set the sampling rate
      of VPC flow logs within the subnetwork where 1.0 means all collected
      logs are reported and 0.0 means no logs are reported. Default is 0.5
      which means half of all collected logs are reported.
      """)
  AddLoggingMetadata(parser, messages)

  parser.add_argument(
      '--logging-filter-expr',
      help="""\
      Can only be specified if VPC Flow Logs for this subnetwork is enabled.
      Export filter used to define which logs should be generated.
      """)
  parser.add_argument(
      '--logging-metadata-fields',
      type=arg_parsers.ArgList(),
      metavar='METADATA_FIELD',
      default=None,
      help="""\
      Can only be specified if VPC Flow Logs for this subnetwork is enabled
      and "metadata" is set to CUSTOM_METADATA. The comma-separated list of
      metadata fields that should be added to reported logs.
      """)

  if include_alpha_logging:
    messages = apis.GetMessagesModule('compute',
                                      compute_api.COMPUTE_ALPHA_API_VERSION)
    AddLoggingAggregationIntervalDeprecated(parser, messages)
    parser.add_argument(
        '--flow-sampling',
        type=arg_parsers.BoundedFloat(lower_bound=0.0, upper_bound=1.0),
        help="""\
        Can only be specified if VPC Flow Logs for this subnetwork is enabled.
        The value of the field must be in [0, 1]. Set the sampling rate of
        VPC Flow Logs within the subnetwork where 1.0 means all collected
        logs are reported and 0.0 means no logs are reported. Default is 0.5
        which means half of all collected logs are reported.
        """)
    AddLoggingMetadataDeprecated(parser, messages)

  if include_l7_internal_load_balancing:
    updated_field.add_argument(
        '--role',
        choices={'ACTIVE': 'The ACTIVE subnet that is currently used.'},
        type=lambda x: x.replace('-', '_').upper(),
        help=('The role is set to ACTIVE to update a BACKUP reserved '
              'address range to\nbe the new ACTIVE address range. Note '
              'that the only supported value for\nthis flag is ACTIVE since '
              'setting an address range to BACKUP is not\nsupported. '
              '\n\nThis field is only valid when updating a reserved IP '
              'address range used\nfor the purpose of Internal HTTP(S) Load '
              'Balancer.'))
    parser.add_argument(
        '--drain-timeout',
        type=arg_parsers.Duration(lower_bound='0s'),
        default='0s',
        help="""\
        The time period for draining traffic from Internal HTTP(S) Load Balancer
        proxies that are assigned addresses in the current ACTIVE subnetwork.
        For example, ``1h'', ``60m'' and ``3600s'' each specify a duration of
        1 hour for draining the traffic. Longer times reduce the number of
        proxies that are draining traffic at any one time, and so improve
        the availability of proxies for load balancing. The drain timeout is
        only applicable when the [--role=ACTIVE] flag is being used.
        """)

  if include_private_ipv6_access_alpha:
    messages = apis.GetMessagesModule('compute',
                                      compute_api.COMPUTE_ALPHA_API_VERSION)
    updated_field.add_argument(
        '--enable-private-ipv6-access',
        action=arg_parsers.StoreTrueFalseAction,
        help=('Enable/disable private IPv6 access for the subnet.'))
    update_private_ipv6_access_field = updated_field.add_argument_group()
    GetPrivateIpv6GoogleAccessTypeFlagMapperAlpha(
        messages).choice_arg.AddToParser(update_private_ipv6_access_field)
    update_private_ipv6_access_field.add_argument(
        '--private-ipv6-google-access-service-accounts',
        default=None,
        metavar='EMAIL',
        type=arg_parsers.ArgList(min_length=0),
        help="""\
        The service accounts can be used to selectively turn on Private IPv6
        Google Access only on the VMs primary service account matching the
        value.

        Setting this will override the existing Private IPv6 Google Access
        service accounts for the subnetwork.
        The following will clear the existing Private IPv6 Google Access service
        accounts:

        $ {command} MY-SUBNET --private-ipv6-google-access-service-accounts ''
        """)
  elif include_private_ipv6_access_beta:
    messages = apis.GetMessagesModule('compute',
                                      compute_api.COMPUTE_BETA_API_VERSION)
    update_private_ipv6_access_field = updated_field.add_argument_group()
    GetPrivateIpv6GoogleAccessTypeFlagMapperBeta(
        messages).choice_arg.AddToParser(update_private_ipv6_access_field)


def GetPrivateIpv6GoogleAccessTypeFlagMapperAlpha(messages):
  return arg_utils.ChoiceEnumMapper(
      '--private-ipv6-google-access-type',
      messages.Subnetwork.PrivateIpv6GoogleAccessValueValuesEnum,
      custom_mappings={
          'DISABLE_GOOGLE_ACCESS':
              'disable',
          'ENABLE_BIDIRECTIONAL_ACCESS_TO_GOOGLE':
              'enable-bidirectional-access',
          'ENABLE_OUTBOUND_VM_ACCESS_TO_GOOGLE':
              'enable-outbound-vm-access',
          'ENABLE_OUTBOUND_VM_ACCESS_TO_GOOGLE_FOR_SERVICE_ACCOUNTS':
              'enable-outbound-vm-access-for-service-accounts'
      },
      help_str='The private IPv6 google access type for the VMs in this subnet.'
  )


def GetPrivateIpv6GoogleAccessTypeFlagMapperBeta(messages):
  return arg_utils.ChoiceEnumMapper(
      '--private-ipv6-google-access-type',
      messages.Subnetwork.PrivateIpv6GoogleAccessValueValuesEnum,
      custom_mappings={
          'DISABLE_GOOGLE_ACCESS':
              'disable',
          'ENABLE_BIDIRECTIONAL_ACCESS_TO_GOOGLE':
              'enable-bidirectional-access',
          'ENABLE_OUTBOUND_VM_ACCESS_TO_GOOGLE':
              'enable-outbound-vm-access'
      },
      help_str='The private IPv6 google access type for the VMs in this subnet.'
  )


def GetLoggingAggregationIntervalArg(messages):
  return arg_utils.ChoiceEnumMapper(
      '--logging-aggregation-interval',
      messages.SubnetworkLogConfig.AggregationIntervalValueValuesEnum,
      custom_mappings={
          'INTERVAL_5_SEC': 'interval-5-sec',
          'INTERVAL_30_SEC': 'interval-30-sec',
          'INTERVAL_1_MIN': 'interval-1-min',
          'INTERVAL_5_MIN': 'interval-5-min',
          'INTERVAL_10_MIN': 'interval-10-min',
          'INTERVAL_15_MIN': 'interval-15-min'
      },
      help_str="""\
        Can only be specified if VPC Flow Logs for this subnetwork is
        enabled. Toggles the aggregation interval for collecting flow logs.
        Increasing the interval time will reduce the amount of generated flow
        logs for long lasting connections. Default is an interval of 5 seconds
        per connection.
        """)


def AddLoggingAggregationInterval(parser, messages):
  GetLoggingAggregationIntervalArg(messages).choice_arg.AddToParser(parser)


def GetLoggingAggregationIntervalArgDeprecated(messages):
  return arg_utils.ChoiceEnumMapper(
      '--aggregation-interval',
      messages.SubnetworkLogConfig.AggregationIntervalValueValuesEnum,
      custom_mappings={
          'INTERVAL_5_SEC': 'interval-5-sec',
          'INTERVAL_30_SEC': 'interval-30-sec',
          'INTERVAL_1_MIN': 'interval-1-min',
          'INTERVAL_5_MIN': 'interval-5-min',
          'INTERVAL_10_MIN': 'interval-10-min',
          'INTERVAL_15_MIN': 'interval-15-min'
      },
      help_str="""\
        Can only be specified if VPC Flow Logs for this subnetwork is
        enabled. Toggles the aggregation interval for collecting flow logs.
        Increasing the interval time will reduce the amount of generated flow
        logs for long lasting connections. Default is an interval of 5 seconds
        per connection.
        """)


def AddLoggingAggregationIntervalDeprecated(parser, messages):
  GetLoggingAggregationIntervalArgDeprecated(messages).choice_arg.AddToParser(
      parser)


def GetLoggingMetadataArg(messages):
  return arg_utils.ChoiceEnumMapper(
      '--logging-metadata',
      messages.SubnetworkLogConfig.MetadataValueValuesEnum,
      custom_mappings={
          'INCLUDE_ALL_METADATA': 'include-all',
          'EXCLUDE_ALL_METADATA': 'exclude-all',
          'CUSTOM_METADATA': 'custom'
      },
      help_str="""\
        Can only be specified if VPC Flow Logs for this subnetwork is
        enabled. Configures whether metadata fields should be added to the
        reported logs. Default is to include all metadata.
        """)


def AddLoggingMetadata(parser, messages):
  GetLoggingMetadataArg(messages).choice_arg.AddToParser(parser)


def GetLoggingMetadataArgDeprecated(messages):
  return arg_utils.ChoiceEnumMapper(
      '--metadata',
      messages.SubnetworkLogConfig.MetadataValueValuesEnum,
      custom_mappings={
          'INCLUDE_ALL_METADATA': 'include-all-metadata',
          'EXCLUDE_ALL_METADATA': 'exclude-all-metadata'
      },
      help_str="""\
        Can only be specified if VPC Flow Logs for this subnetwork is
        enabled. Configures whether metadata fields should be added to the
        reported logs. Default is to include all metadata.
        """)


def AddLoggingMetadataDeprecated(parser, messages):
  GetLoggingMetadataArgDeprecated(messages).choice_arg.AddToParser(parser)
