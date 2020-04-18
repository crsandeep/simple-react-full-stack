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
"""Flags and helpers for the Cloud Filestore instances commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.filestore import filestore_client
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.filestore import flags
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.util.concepts import concept_parsers

INSTANCES_LIST_FORMAT = """\
    table(
      name.basename():label=INSTANCE_NAME:sort=1,
      name.segment(3):label=ZONE,
      tier,
      fileShares[0].capacityGb:label=CAPACITY_GB,
      fileShares[0].name:label=FILE_SHARE_NAME,
      networks[0].ipAddresses[0]:label=IP_ADDRESS,
      state,
      createTime.date()
    )"""

NETWORK_ARG_SPEC = {
    'name': str,
    'reserved-ip-range': str,
}


FILE_SHARE_ARG_SPEC = {
    'name':
        str,
    'capacity':
        arg_parsers.BinarySize(
            default_unit='GB',
            lower_bound='1TB',
            upper_bound='65434GB',
            suggested_binary_size_scales=['GB', 'GiB', 'TB', 'TiB']
        ),
    'source-snapshot':
        str,
    'source-snapshot-region':
        str,
}


def AddAsyncFlag(parser):
  base.ASYNC_FLAG.AddToParser(parser)


def AddLocationArg(parser):
  action = actions.DeprecationAction(
      'location',
      warn='The `--location` flag is deprecated. Use `--zone`.')
  parser.add_argument('--location', required=False, action=action,
                      help='Location of the Cloud Filestore instance.')


def AddDescriptionArg(parser):
  parser.add_argument(
      '--description', help='A description of the Cloud Filestore instance.')


def GetTierArg(messages):
  """Adds a --tier flag to the given parser.

  Args:
    messages: The messages module.

  Returns:
    the choice arg.
  """
  tier_arg = arg_utils.ChoiceEnumMapper(
      '--tier',
      messages.Instance.TierValueValuesEnum,
      help_str='The service tier for the Cloud Filestore instance.',
      custom_mappings={
          'STANDARD': ('standard', 'Standard Filestore instance.'),
          'PREMIUM': ('premium', 'Premium Filestore instance.')},
      default='STANDARD')
  return tier_arg


def AddNetworkArg(parser):
  """Adds a --network flag to the given parser.

  Args:
    parser: argparse parser.
  """
  network_help = """\
      Network configuration for a Cloud Filestore instance. Specifying
      `reserved-ip-range` is optional.

      *name*::: The name of the Google Compute Engine
      [VPC network](/compute/docs/networks-and-firewalls#networks) to which the
      instance is connected.

      *reserved-ip-range*::: A /29 CIDR block in one of the
      [internal IP address ranges](https://www.arin.net/knowledge/address_filters.html)
      that identifies the range of IP addresses reserved for this
      instance. For example, 10.0.0.0/29 or 192.168.0.0/29. The range you
      specify can't overlap with either existing subnets or assigned IP address
      ranges for other Cloud Filestore instances in the selected VPC network.

      """
  parser.add_argument(
      '--network',
      type=arg_parsers.ArgDict(spec=NETWORK_ARG_SPEC,
                               required_keys=['name']),
      required=True,
      help=network_help)


def AddFileShareArg(parser, include_snapshot_flags=False, required=True):
  """Adds a --file-share flag to the given parser.

  Args:
    parser: argparse parser.
    include_snapshot_flags: bool, whether to include --source-snapshot flags.
    required: bool, passthrough to parser.add_argument.
  """
  file_share_help = """\
      File share configuration for an instance. Specifying both `name` and
      `capacity` is required.

      *capacity*::: The desired size of the volume. The capacity must be a whole
      number followed by a size unit such as ``TB'' for terabyte. If no size
      unit is specified, GB is assumed. The minimum size for a standard instance
      is 1TB. The minimum size for a premium instance is 2.5TB.

      *name*::: The desired logical name of the volume.

      """
  source_snapshot_help = """\
      *source-snapshot*::: The name of the snapshot to restore from.

      *source-snapshot-region*::: The region of the source snapshot. If
      unspecified, it is assumed that the Filestore snapshot is local and
      instance-zone will be used.
      """
  parser.add_argument(
      '--file-share',
      type=arg_parsers.ArgDict(spec=FILE_SHARE_ARG_SPEC,
                               required_keys=['name', 'capacity']),
      required=required,
      help=file_share_help + (source_snapshot_help if include_snapshot_flags
                              else ''))


def AddInstanceCreateArgs(parser, api_version):
  """Add args for creating an instance."""
  concept_parsers.ConceptParser([flags.GetInstancePresentationSpec(
      'The instance to create.')]).AddToParser(parser)
  AddDescriptionArg(parser)
  AddLocationArg(parser)
  messages = filestore_client.GetMessages(version=api_version)
  GetTierArg(messages).choice_arg.AddToParser(parser)
  AddAsyncFlag(parser)
  AddFileShareArg(parser, include_snapshot_flags=
                  (api_version == filestore_client.ALPHA_API_VERSION))
  AddNetworkArg(parser)
  labels_util.AddCreateLabelsFlags(parser)


def AddInstanceUpdateArgs(parser):
  """Add args for updating an instance."""
  concept_parsers.ConceptParser([flags.GetInstancePresentationSpec(
      'The instance to update.')]).AddToParser(parser)
  AddDescriptionArg(parser)
  AddLocationArg(parser)
  AddAsyncFlag(parser)
  labels_util.AddUpdateLabelsFlags(parser)
  AddFileShareArg(parser, required=False)
