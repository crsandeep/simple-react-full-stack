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
"""Provides common arguments for the Events command surface."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.events import exceptions
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.core import yaml


def AddSourceFlag(parser):
  """Adds a source flag. This refers to a source kind, not instance."""
  parser.add_argument(
      '--source',
      required=False,
      help='Events source kind by which to filter results.')


def AddEventTypePositionalArg(parser):
  """Adds event type positional arg."""
  parser.add_argument(
      'event_type',
      help='Type of event (e.g. com.google.cloud.auditlog.event).')


def AddTargetServiceFlag(parser, required=False):
  """Adds target service flag."""
  parser.add_argument(
      '--target-service',
      required=required,
      help='Name or absolute uri of the Cloud Run service at which '
      'events should be received.')


def AddEventTypeFlagArg(parser):
  """Adds event type flag arg."""
  parser.add_argument(
      '--type',
      required=True,
      help='Type of event (e.g. com.google.cloud.auditlog.event).')


def AddBrokerFlag(parser):
  """Adds broker flag."""
  parser.add_argument(
      '--broker',
      default='default',
      help='Name of the Broker to send events to. '
      'Defaults to \'default\' if not specified.')


def AddBrokerArg(parser):
  """Adds broker arg."""
  parser.add_argument(
      'BROKER',
      help='Name of the Broker to create.')


def AddServiceAccountFlag(parser):
  """Adds service account flag."""
  parser.add_argument(
      '--service-account',
      required=True,
      type=iam_util.GetIamAccountFormatValidator(),
      help='Email address of an IAM service account which represents the '
      'identity of the internal events operator.')


def AddCustomEventTypeFlag(parser):
  """Adds custom event type boolean flag."""
  parser.add_argument(
      '--custom-type',
      action='store_true',
      help='If specified, the provided event type should be interpreted as a '
      'custom event type.')


_PARAMETERS_FLAG_NAME = 'parameters'


def AddParametersFlags(parser):
  """Adds parameters and parameters-from-file flags."""
  parameters_group = parser.add_mutually_exclusive_group()
  parameters_group.add_argument(
      '--{}'.format(_PARAMETERS_FLAG_NAME),
      type=arg_parsers.ArgDict(),
      action=arg_parsers.UpdateAction,
      default={},
      help='Comma-separated list of parameter names and values. '
      'Names must be one of the parameters shown when describing the '
      'event type. Only simple values can be specified with this flag. '
      'To specify more complex types like lists and nested objects, '
      'use --{}-from-file.'.format(_PARAMETERS_FLAG_NAME),
      metavar='PARAMETER=VALUE')
  parameters_group.add_argument(
      '--{}-from-file'.format(_PARAMETERS_FLAG_NAME),
      type=arg_parsers.YAMLFileContents(validator=yaml.dict_like),
      default={},
      help='Path to a local JSON or YAML file that defines a dictionary of '
      'parameters and their values. Parameters must match the items shown when '
      'describing the event type.')


_SECRETS_FLAG_NAME = 'secrets'


def AddSecretsFlag(parser):
  """Adds secrets flag."""
  parser.add_argument(
      '--{}'.format(_SECRETS_FLAG_NAME),
      type=arg_parsers.ArgDict(),
      action=arg_parsers.UpdateAction,
      default={},
      help='Comma-separated list of secret parameter names and secrets. '
      'Specify secret parameters and the secret name and key to '
      'reference. Parameter names must be one of the secret parameters shown '
      'when describing the event type.',
      metavar='PARAMETER=NAME:KEY')


def _ParseSecretParameters(args):
  """Parses --secrets flag into dict(param -> {'name': secret name, 'key': secret key})."""
  secret_params = {}
  for param, secret_pair in getattr(args, _SECRETS_FLAG_NAME).items():
    try:
      name, key = secret_pair.split(':', 1)
      secret_params[param] = {'name': name, 'key': key}
    except ValueError:
      raise calliope_exceptions.InvalidArgumentException(
          '--{}'.format(_SECRETS_FLAG_NAME),
          'Secret name and key not property specified for [{}].'.format(
              param))
  return secret_params


def _CheckUnknownParameters(event_type, known_params, given_params):
  """Raises an error if any given params are unknown."""
  unknown_parameters = (
      set(given_params) -
      set(known_params))
  if unknown_parameters:
    raise exceptions.UnknownEventTypeParameters(
        unknown_parameters, event_type)


def _CheckMissingRequiredParameters(event_type, required_params, given_params):
  """Raises an error if any required params are missing."""
  missing_parameters = (
      set(required_params) -
      set(given_params))
  if missing_parameters:
    raise exceptions.MissingRequiredEventTypeParameters(
        missing_parameters, event_type)


def _ValidateParameters(event_type, parameters, properties='properties'):
  """Validates given params conform to what's expected."""
  # TODO(b/142421197): Validate nested objects and convert non-string types
  _CheckUnknownParameters(
      event_type,
      [p.name for p in getattr(event_type.crd, properties)],
      parameters.keys())
  _CheckMissingRequiredParameters(
      event_type,
      [p.name for p in getattr(event_type.crd, properties) if p.required],
      parameters.keys())


def GetAndValidateParameters(args, event_type):
  """Validates all source parameters and returns a dict of values."""
  # Check the passed parameters for unknown keys or missing required keys
  parameters = {}
  from_file_flag = '{}_from_file'.format(_PARAMETERS_FLAG_NAME)
  if args.IsSpecified(from_file_flag):
    parameters.update(getattr(args, from_file_flag))
  if args.IsSpecified(_PARAMETERS_FLAG_NAME):
    parameters.update(getattr(args, _PARAMETERS_FLAG_NAME))
  _ValidateParameters(event_type, parameters)

  # Check the passed secret parameters for unknown keys or missing required keys
  secret_parameters = _ParseSecretParameters(args)
  _ValidateParameters(
      event_type, secret_parameters, properties='secret_properties')

  parameters.update(secret_parameters)
  return parameters
