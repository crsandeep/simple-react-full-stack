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
"""Shared flags for Cloud Domains commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util.apis import arg_utils


def AddRegistrationSettingsFlagsToParser(parser):
  """Get flags for registration commands.

  Args:
    parser: argparse parser to which to add these flags.

  """
  dns_group = base.ArgumentGroup(
      mutex=True,
      help=('Set the addresses of authoritative name servers for the given '
            'domain.'))
  dns_group.AddArgument(
      base.Argument(
          '--name-servers',
          help='List of DNS name servers for the domain.',
          metavar='NAME_SERVER',
          type=arg_parsers.ArgList(str, min_length=2)))

  dns_group.AddArgument(
      base.Argument(
          '--cloud-dns-zone',
          help=('The name of the Cloud DNS managed-zone to set as the name '
                'server for the domain.\n'
                'If it\'s in the same project, you can use short name. If not, '
                'use the full resource name, e.g.: --cloud-dns-zone='
                'projects/example-project/managedZones/example-zone')))
  dns_group.AddToParser(parser)

  base.Argument(
      '--registrant-contact-from-file',
      help="""\
      A YAML file containing the required WHOIS data. If specified, this file
      must contain values for all required fields: email, phoneNumber and
      postalAddress in google.type.PostalAddress format.

      For more guidance on how to specify postalAddress, please see:
      https://support.google.com/business/answer/6397478

      Example file contents:

      ```
      email: 'example@example.com'
      phoneNumber: '+11234567890'
      postalAddress:
        regionCode: 'US'
        postalCode: '94043'
        administrativeArea: 'CA'
        locality: 'Mountain View'
        addressLines: ['1600 Amphitheatre Pkwy']
        recipients: ['Jane Doe']
      ```
      """).AddToParser(parser)

  WHOIS_PRIVACY_ENUM_MAPPER.choice_arg.AddToParser(parser)


def AddValidateOnlyFlagToParser(parser, verb):
  base.Argument(
      '--validate-only',
      help='Don\'t actually {} registration. Only validate arguments.'.format(
          verb),
      default=False,
      action='store_true').AddToParser(parser)


def AddAsyncFlagToParser(parser):
  base.ASYNC_FLAG.AddToParser(parser)


def _GetWhoisPrivacyEnum():
  """Get WhoisPrivacyValuesEnum from api messages."""
  messages = apis.GetMessagesModule('domains', 'v1alpha1')
  return messages.WhoisConfig.PrivacyValueValuesEnum

WHOIS_PRIVACY_ENUM_MAPPER = arg_utils.ChoiceEnumMapper(
    '--whois-privacy',
    _GetWhoisPrivacyEnum(),
    custom_mappings={
        'USE_WHOIS_PRIVACY_PROXY': (
            'use-whois-privacy-proxy',
            ('Your contact info won\'t be available to the public. To help '
             'protect your info and prevent spam, a third party provides '
             'alternate contact info for your domain in the WHOIS directory at '
             'no extra cost.')),
        'PUBLISH_REDACTED_CONTACT_DATA': (
            'publish-redacted-contact-data',
            ('Limited personal info will be available to the public. The '
             'actual information redacted depends on the domain.')),
    },
    required=False,
    help_str=('The WHOIS privacy mode to use.'))
