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
"""Utilities for defining Label Manager arguments on a parser."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


def AddLabelKeyIdArgToParser(parser):
  """Adds argument for the LabelKey display name or numeric id to the parser.

  Args:
    parser: ArgumentInterceptor, An argparse parser.
  """
  parser.add_argument(
      'LABEL_KEY_ID',
      metavar='LABEL_KEY_ID',
      help=('Display name or numeric id for the LabelKey. The display name '
            'must be 1-63 characters, beginning and ending with an '
            'alphanumeric character ([a-z0-9A-Z]) with dashes (-), underscores '
            '(_), dots (.), and alphanumerics between. The numeric id should '
            'be of the form labelKeys/{numeric_id}.'))


def AddLabelValueIdArgToParser(parser):
  """Adds argument for the LabelValue display name or numeric id to the parser.

  Args:
    parser: ArgumentInterceptor, An argparse parser.
  """
  parser.add_argument(
      'LABEL_VALUE_ID',
      metavar='LABEL_VALUE_ID',
      help=('Display name or numeric id for the LabelValue. The display name '
            'must be 1-63 characters, beginning and ending with an '
            'alphanumeric character ([a-z0-9A-Z]) with dashes (-), underscores '
            '(_), dots (.), and alphanumerics between. The numeric id should '
            'be of the form labelValues/{numeric_id}.'))


def AddDisplayNameArgToParser(parser):
  """Adds argument for the LabelKey display name to the parser.

  Args:
    parser: ArgumentInterceptor, An argparse parser.
  """
  parser.add_argument(
      'DISPLAY_NAME',
      metavar='DISPLAY_NAME',
      help=('Display name for the LabelKey. The display name must be 1-63 '
            'characters, beginning and ending with an alphanumeric character '
            '([a-z0-9A-Z]) with dashes (-), underscores (_), dots (.), and '
            'alphanumerics between.'))


def AddLabelParentArgToParser(parser, required=False, message=''):
  """Adds argument for the LabelKey's parent to the parser.

  Args:
    parser: ArgumentInterceptor, An argparse parser.
    required: Boolean, to enforce --label-parent as a required flag.
    message: String, additional help text for flag.
  """
  parser.add_argument(
      '--label-parent',
      metavar='LABEL_PARENT',
      required=required,
      help=('Parent of the LabelKey. This must be the form '
            'organizations/{org_id}. ' + message))


def AddDescriptionArgToParser(parser):
  """Adds argument for the LabelKey's or LabelValue's description to the parser.

  Args:
    parser: ArgumentInterceptor, An argparse parser.
  """
  parser.add_argument(
      '--description',
      metavar='DESCRIPTION',
      help=('Optional user-assigned description of the LabelKey or LabelValue. '
            'Must not exceed 256 characters.'))


def AddAsyncArgToParser(parser):
  """Adds async flag to the parser.

  Args:
    parser: ArgumentInterceptor, An argparse parser.
  """
  base.ASYNC_FLAG.AddToParser(parser)


def AddOperationNameArgToParser(parser):
  """Adds operation name flag to the parser.

  Args:
    parser: ArgumentInterceptor, An argparse parser.
  """
  parser.add_argument(
      'OPERATION_NAME',
      metavar='OPERATION_NAME',
      help='Name of the long running operation in label manager.')


def AddLabelKeyArgToParser(parser, required=True, message=''):
  """Adds argument for the LabelKey to the parser.

  Args:
    parser: ArgumentInterceptor, An argparse parser.
    required: Boolean, to enforce --label-key as a required flag.
    message: String, additional help text for flag.
  """
  parser.add_argument(
      '--label-key',
      required=required,
      metavar='LABEL_KEY',
      help=('Display name or numeric id of the parent LabelKey. Numeric ids '
            'should be of the form labelKeys/{numeric_id}. ' + message))


def AddResourceArgToParser(
    parser,
    required=True,
    message=('Full resource name of the resource the LabelValue will '
             'be bound to.')):
  """Adds argument for the LabelKey to the parser.

  Args:
    parser: ArgumentInterceptor, An argparse parser.
    required: Boolean, to enforce --resource as a required flag.
    message: String, help text for flag.
  """
  parser.add_argument(
      '--resource', required=required, metavar='RESOURCE', help=message)


def AddPolicyFileArgToParser(parser):
  """Adds argument for the local Policy file to set.

  Args:
    parser: ArgumentInterceptor, An argparse parser.
  """
  parser.add_argument(
      'POLICY_FILE',
      metavar='POLICY_FILE',
      help=(
          'Path to a local JSON or YAML formatted file containing a valid '
          'policy. The output of the `get-iam-policy` command is a valid '
          'file, as is any JSON or YAML file conforming to the structure of '
          'a [Policy](https://cloud.google.com/iam/reference/rest/v1/Policy).'))


def AddShowDeletedArgToParser(
    parser,
    message=('Show deleted resources when listing.')):
  """Adds argument for to show deleted resources when listing.

  Args:
    parser: ArgumentInterceptor, An argparse parser.
    message: String, help text for flag.
  """
  parser.add_argument(
      '--show-deleted', required=False, metavar='SHOW_DELETED', help=message)
