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
"""Flags for serverless local development setup."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.util.args import map_util
from googlecloudsdk.core import exceptions
import six


def CommonFlags(parser):
  """Add common flags for local developement environments."""
  parser.add_argument(
      '--dockerfile',
      default='Dockerfile',
      help='Dockerfile for the service image.')

  parser.add_argument(
      '--service-name', required=False, help='Name of the service.')

  parser.add_argument(
      '--image-name', required=False, help='Name for the built docker image.')

  parser.add_argument(
      '--build-context-directory',
      help='If set, use this as the context directory when building the '
      'container image. Otherwise, the directory of the Dockerfile will be '
      'used.')

  parser.add_argument(
      '--builder',
      help='Build with a given Cloud Native Computing Foundation Buildpack '
      'builder.')

  parser.add_argument(
      '--service-account',
      help='When connecting to Google Cloud Platform services, use a service '
      'account key.')

  parser.add_argument(
      '--local-port',
      type=int,
      help='Local port to which the service connection is forwarded. If this '
      'flag is not set, then a random port is chosen.')

  parser.add_argument(
      '--cloudsql-instances',
      type=arg_parsers.ArgList(),
      metavar='CLOUDSQL_INSTANCE',
      help='Cloud SQL instance connection strings. Must be in the form '
      '<project>:<region>:<instance>.')

  parser.add_argument(
      '--cpu-limit',
      type=arg_parsers.BoundedFloat(lower_bound=0.0),
      help='Container CPU limit. Limit is expressed as a number of CPUs. '
      'Fractional CPU limits are allowed (e.g. 1.5).')

  parser.add_argument(
      '--memory-limit',
      type=arg_parsers.BinarySize(default_unit='B'),
      help='Container memory limit. Limit is expressed either as an integer '
      'representing the number of bytes or an integer followed by a unit '
      'suffix. Valid unit suffixes are "B", "KB", "MB", "GB", "TB", "KiB", '
      '"MiB", "GiB", "TiB", or "PiB".')

  env_var_group = parser.add_mutually_exclusive_group(required=False)
  env_var_group.add_argument(
      '--env-vars',
      metavar='KEY=VALUE',
      action=arg_parsers.UpdateAction,
      type=arg_parsers.ArgDict(
          key_type=six.text_type, value_type=six.text_type),
      help='List of key-value pairs to set as environment variables.')

  env_var_group.add_argument(
      '--env-vars-file',
      metavar='FILE_PATH',
      type=map_util.ArgDictFile(
          key_type=six.text_type, value_type=six.text_type),
      help='Path to a local YAML file with definitions for all environment '
      'variables.')


class InvalidFlagError(exceptions.Error):
  """Flag settings are illegal."""


def Validate(namespace):
  """Validate flag requirements that cannot be handled by argparse."""
  if (namespace.IsSpecified('cloudsql_instances') and
      not namespace.IsSpecified('service_account')):
    raise InvalidFlagError(
        '--cloudsql-instances requires --service-account to be specified.')
