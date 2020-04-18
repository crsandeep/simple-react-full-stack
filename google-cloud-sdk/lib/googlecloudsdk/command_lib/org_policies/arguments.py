# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Utilities for defining Org Policy arguments on a parser."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.resource_manager import completers
from googlecloudsdk.command_lib.util.args import common_args


def AddConstraintArgToParser(parser):
  """Adds argument for the constraint name to the parser.

  Args:
    parser: ArgumentInterceptor, An argparse parser.
  """
  parser.add_argument(
      'constraint',
      metavar='CONSTRAINT',
      help=(
          'Name of the org policy constraint. The list of available constraints'
          ' can be found here: '
          'https://cloud.google.com/resource-manager/docs/organization-policy/org-policy-constraints'
      ))


def AddValueArgToParser(parser):
  """Adds argument for a list of values to the parser.

  Args:
    parser: ArgumentInterceptor, An argparse parser.
  """
  parser.add_argument(
      'value',
      metavar='VALUE',
      nargs='*',
      help=(
          'Values to add to the policy. The set of valid values corresponding '
          'to the different constraints are covered here: '
          'https://cloud.google.com/resource-manager/docs/organization-policy/org-policy-constraints'
      ))


def AddResourceFlagsToParser(parser):
  """Adds flags for the resource ID to the parser.

  Adds --organization, --folder, and --project flags to the parser. The flags
  are added as a required group with a mutex condition, which ensures that the
  user passes in exactly one of the flags.

  Args:
    parser: ArgumentInterceptor, An argparse parser.
  """
  resource_group = parser.add_mutually_exclusive_group(
      required=True,
      help='Resource that is associated with the organization policy.')
  resource_group.add_argument(
      '--organization',
      metavar='ORGANIZATION_ID',
      completer=completers.OrganizationCompleter,
      help='Organization ID.')
  resource_group.add_argument(
      '--folder', metavar='FOLDER_ID', help='Folder ID.')
  common_args.ProjectArgument(
      help_text_to_overwrite='Project ID.').AddToParser(resource_group)


# TODO (b/138656127): One aliasing is implemented for all commands that take in
# --condition, update this documentation to reflect the newly available input.
def AddConditionFlagToParser(parser):
  """Adds flag for the condition to the parser.

  Args:
    parser: ArgumentInterceptor, An argparse parser.
  """
  parser.add_argument(
      '--condition',
      metavar='CONDITION',
      help=(
          'Condition expression for filtering the resources the policy applies '
          'to. The standard syntax for a condition is '
          '\'resource.matchLabels("labelKeys/{label_key_id}", "labelValues/{label_value_id}")\'.'
          'By using the --label-parent flag you may use the display names for '
          'LabelKey and LabelValue with syntax '
          '\'resource.matchLabels("{label_key_display_name}", "{label_value_display_name}")\'.'
      ))
