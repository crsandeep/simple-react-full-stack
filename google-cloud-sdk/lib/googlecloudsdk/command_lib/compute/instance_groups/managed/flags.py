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
"""Flags for the compute instance groups managed commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base

DEFAULT_LIST_FORMAT = """\
    table(
      name,
      location():label=LOCATION,
      location_scope():label=SCOPE,
      baseInstanceName,
      size,
      targetSize,
      instanceTemplate.basename(),
      autoscaled
    )
"""


def AddTypeArg(parser):
  parser.add_argument(
      '--type',
      choices={
          'opportunistic': 'Do not proactively replace instances. Create new '
                           'instances and delete old on resizes of the group.',
          'proactive': 'Replace instances proactively.',
      },
      default='proactive',
      category=base.COMMONLY_USED_FLAGS,
      help='Desired update type.')


def AddMaxSurgeArg(parser):
  parser.add_argument(
      '--max-surge',
      type=str,
      help=('Maximum additional number of instances that '
            'can be created during the update process. '
            'This can be a fixed number (e.g. 5) or '
            'a percentage of size to the managed instance '
            'group (e.g. 10%)'))


def AddMaxUnavailableArg(parser):
  parser.add_argument(
      '--max-unavailable',
      type=str,
      help=('Maximum number of instances that can be '
            'unavailable during the update process. '
            'This can be a fixed number (e.g. 5) or '
            'a percentage of size to the managed instance '
            'group (e.g. 10%)'))


def AddMinReadyArg(parser):
  parser.add_argument(
      '--min-ready',
      type=arg_parsers.Duration(lower_bound='0s'),
      help=('Minimum time for which a newly created instance '
            'should be ready to be considered available. For example `10s` '
            'for 10 seconds. See $ gcloud topic datetimes for information '
            'on duration formats.'))


def AddReplacementMethodFlag(parser):
  parser.add_argument(
      '--replacement-method',
      choices={
          'substitute': 'Updated instances will be deleted and created again '
                        'with another name.',
          'recreate': 'Updated instances will be recreated with the same name.',
      },
      help='Type of replacement method. Specifies what action will be taken '
           'to update instances.')


def AddForceArg(parser):
  parser.add_argument(
      '--force',
      action='store_true',
      help=('If set, accepts any original or new version '
            'configurations without validation.'))


INSTANCE_ACTION_CHOICES = {
    'none': 'No action',
    'refresh': 'Apply properties that are possible to apply '
               'without stopping the instance',
    'restart': 'Stop the instance and start it again',
    'replace': 'Delete the instance and create it again'
}


def AddMinimalActionArg(parser):
  parser.add_argument(
      '--minimal-action',
      choices=INSTANCE_ACTION_CHOICES,
      default='none',
      help='Perform at least this action on each instance while updating.')


def AddMostDisruptiveActionArg(parser):
  parser.add_argument(
      '--most-disruptive-allowed-action',
      choices=INSTANCE_ACTION_CHOICES,
      default='replace',
      help='Perform at most this action on each instance while updating. '
      'If the update requires a more disruptive action than the one '
      'specified here, then the update will fail and no changes '
      'will be made.')


def MapInstanceActionEnumValue(instance_action, messages,
                               instance_action_enum):
  """Map the UpdatePolicy action values to appropriate apply updates request enum.

  Args:
    instance_action: instance action to map.
    messages: module containing message classes.
    instance_action_enum: corresponding apply updates request class enum.

  Returns:
    Corresponding apply updates request instance action enum object.
  """
  enum_map = {
      messages.InstanceGroupManagerUpdatePolicy.MinimalActionValueValuesEnum
      .NONE:
          instance_action_enum.NONE,
      messages.InstanceGroupManagerUpdatePolicy.MinimalActionValueValuesEnum
      .REFRESH:
          instance_action_enum.REFRESH,
      messages.InstanceGroupManagerUpdatePolicy.MinimalActionValueValuesEnum
      .RESTART:
          instance_action_enum.RESTART,
      messages.InstanceGroupManagerUpdatePolicy.MinimalActionValueValuesEnum
      .REPLACE:
          instance_action_enum.REPLACE,
  }
  return enum_map[instance_action]


def AddUpdateInstancesArgs(parser):
  """Add args for the update-instances command."""
  parser.add_argument(
      '--instances',
      type=arg_parsers.ArgList(min_length=1),
      metavar='INSTANCE',
      required=True,
      help='Names of instances to update.')
  AddMinimalActionArg(parser)
  AddMostDisruptiveActionArg(parser)
