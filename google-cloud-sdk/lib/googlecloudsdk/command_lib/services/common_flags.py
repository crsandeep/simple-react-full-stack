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
"""Common flags for the consumers subcommand group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.api_lib.services import services_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util import completers
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs

_SERVICES_LEGACY_LIST_COMMAND = ('services list --format=disable '
                                 '--flatten=serviceName')
_SERVICES_LIST_COMMAND = ('beta services list --format=disable '
                          '--flatten=config.name')

_OPERATION_NAME_RE = re.compile(r'operations/(?P<namespace>\w+)\.(?P<id>.*)')


class ConsumerServiceCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(ConsumerServiceCompleter, self).__init__(
        collection=services_util.SERVICES_COLLECTION,
        list_command=_SERVICES_LIST_COMMAND,
        flags=['enabled'],
        **kwargs)


class ConsumerServiceLegacyCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(ConsumerServiceLegacyCompleter, self).__init__(
        collection=services_util.SERVICES_COLLECTION,
        list_command=_SERVICES_LEGACY_LIST_COMMAND,
        flags=['enabled'],
        **kwargs)


def operation_flag(suffix='to act on'):
  return base.Argument(
      'operation', help='The name of the operation {0}.'.format(suffix))


def get_operation_namespace(op_name):
  match = _OPERATION_NAME_RE.match(op_name)
  if not match:
    raise arg_parsers.ArgumentTypeError("Invalid value '{0}': {1}".format(
        op_name, 'Operation format should be operations/namespace.id'))
  return match.group('namespace')


def consumer_service_flag(suffix='to act on', flag_name='service'):
  return base.Argument(
      flag_name,
      nargs='*',
      completer=ConsumerServiceCompleter,
      help='The name of the service(s) {0}.'.format(suffix))


def single_consumer_service_flag(suffix='to act on', flag_name='service'):
  return base.Argument(
      flag_name,
      completer=ConsumerServiceCompleter,
      help='The name of the service {0}.'.format(suffix))


def available_service_flag(suffix='to act on', flag_name='service'):
  # NOTE: Because listing available services often forces the tab completion
  #       code to timeout, this flag will not enable tab completion.
  return base.Argument(
      flag_name,
      nargs='*',
      help='The name of the service(s) {0}.'.format(suffix))


def _create_key_resource_arg(help_txt):
  return presentation_specs.ResourcePresentationSpec(
      'key', _get_key_resource_spec(), help_txt, required=True)


def _get_key_resource_spec():
  """Return the resource specification for a key."""
  return concepts.ResourceSpec(
      'apikeys.projects.keys',
      resource_name='key',
      keysId=_key_attribute_config(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)


def _key_attribute_config():
  return concepts.ResourceParameterAttributeConfig(
      name='key', help_text='Id of the key')


def key_flag(parser, suffix='to act on'):
  return concept_parsers.ConceptParser([
      _create_key_resource_arg(
          help_txt='The name of the key {0}.'.format(suffix))
  ]).AddToParser(parser)


def display_name_flag(parser, suffix='to act on'):
  base.Argument(
      '--display-name',
      help='Display name of the key {0}.'.format(suffix)).AddToParser(parser)


def add_key_update_args(parser):
  """Add args for api-keys update command."""
  update_set_group = parser.add_mutually_exclusive_group(required=False)
  _add_clear_restrictions_arg(update_set_group)
  restriction_group = update_set_group.add_argument_group()
  client_restriction_group = restriction_group.add_mutually_exclusive_group()
  _allowed_referrers_arg(client_restriction_group)
  _allowed_ips_arg(client_restriction_group)
  _allowed_bundle_ids(client_restriction_group)
  _allowed_application(client_restriction_group)
  _api_targets_arg(restriction_group)


def add_key_create_args(parser):
  """Add args for api-keys create command."""
  restriction_group = parser.add_argument_group()
  client_restriction_group = restriction_group.add_mutually_exclusive_group()
  _allowed_referrers_arg(client_restriction_group)
  _allowed_ips_arg(client_restriction_group)
  _allowed_bundle_ids(client_restriction_group)
  _allowed_application(client_restriction_group)
  _api_targets_arg(restriction_group)


def _add_clear_restrictions_arg(parser):
  base.Argument(
      '--clear-restrictions',
      action='store_true',
      help='If set, clear all restrictions on the key.').AddToParser(parser)


def _allowed_referrers_arg(parser):
  base.Argument(
      '--allowed-referrers',
      default=[],
      type=arg_parsers.ArgList(),
      metavar='ALLOWED_REFERRERS',
      help='A list of regular expressions for the referrer URLs that are '
           'allowed to make API calls with this key.'
  ).AddToParser(parser)


def _allowed_ips_arg(parser):
  base.Argument(
      '--allowed-ips',
      default=[],
      type=arg_parsers.ArgList(),
      metavar='ALLOWED_IPS',
      help='A list of the caller IP addresses that are allowed to make API '
           'calls with this key.'
  ).AddToParser(parser)


def _allowed_bundle_ids(parser):
  base.Argument(
      '--allowed-bundle-ids',
      default=[],
      metavar='ALLOWED_BUNDLE_IDS',
      type=arg_parsers.ArgList(),
      help='iOS app\'s bundle ids that are allowed to use the key.'
  ).AddToParser(parser)


def _allowed_application(parser):
  base.Argument(
      '--allowed-application',
      type=arg_parsers.ArgDict(
          spec={
              'sha1_fingerprint': str,
              'package_name': str
          },
          required_keys=['sha1_fingerprint', 'package_name'],
          max_length=2),
      metavar='sha1_fingerprint=SHA1_FINGERPRINT,package_name=PACKAGE_NAME',
      action='append',
      help=('This flag is repeatable to specify multiple allowed applications. '
            'The accepted keys are `sha1_fingerprint` and `package_name`.'
           )).AddToParser(parser)


def _api_targets_arg(parser):
  base.Argument(
      '--api-target',
      type=arg_parsers.ArgDict(
          spec={
              'service': str,
              'methods': list
          },
          required_keys=['service'],
          min_length=1),
      metavar='service=SERVICE',
      action='append',
      help="""\
       This flag is repeatable to specify multiple api targets.
        `service` and optionally one or multiple specific `methods`.
        Both fields are case insensitive.
        If you need to specify methods, it should be specified
      with the `--flags-file`. See $ gcloud topic flags-file for details.
      See the examples section for how to use `--api-target` in
      `--flags-file`.""").AddToParser(parser)
