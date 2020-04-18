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
"""Defines arguments for gcloud auth."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers


def AddAccountArg(parser):
  parser.add_argument(
      'account',
      nargs='?',
      help=('Account to print the identity token for. If not specified, '
            'the current active account will be used.'))


def AddAudienceArg(parser):
  parser.add_argument(
      '--audiences',
      type=arg_parsers.ArgList(),
      metavar='AUDIENCES',
      help=('Comma-separated list of audiences which are the intended '
            'recipients of the token.'))


def AddIncludeEmailArg(parser):
  parser.add_argument(
      '--include-email',
      action='store_true',
      help=('Specify whether or not service account email is included in the '
            "identity token. If specified, the token will contain 'email' and "
            "'email_verified' claims. This flag should only be used for "
            'impersonate service account.'))


def AddGCESpecificArgs(parser):
  """Add GCE specific arguments to parser."""
  gce_arg_group = parser.add_argument_group(
      help='Parameters for Google Compute Engine instance identity tokens.')
  gce_arg_group.add_argument(
      '--token-format',
      choices=['standard', 'full'],
      default='standard',
      help='Specify whether or not the project and instance details are '
      'included in the identity token payload. This flag only applies to '
      'Google Compute Engine instance identity tokens. '
      'See https://cloud.google.com/compute/docs/instances/verifying-instance-identity#token_format '
      'for more details on token format.')
  gce_arg_group.add_argument(
      '--include-license',
      action='store_true',
      help='Specify whether or not license codes for images associated with '
      'this instance are included in the identity token payload. Default '
      'is False. This flag does not have effect unless '
      '`--token-format=full`.')
