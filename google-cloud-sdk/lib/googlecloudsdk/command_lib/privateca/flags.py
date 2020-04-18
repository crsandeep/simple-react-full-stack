# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Helpers for parsing flags and arguments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.api_lib.privateca import constants as api_constants
from googlecloudsdk.api_lib.util import messages as messages_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.privateca import text_utils
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import resources
from googlecloudsdk.core.util import times

import ipaddress
import six

_EMAIL_SAN_REGEX = re.compile('^[^@]+@[^@]+$')
# Any number of labels (any character that is not a dot) concatenated by dots
_DNS_SAN_REGEX = re.compile(r'^([^.]+\.)*[^.]+$')

# Flag definitions

PUBLISH_CA_CERT_CREATE_HELP = """
If this is enabled, the following will happen:
1) The CA certificate will be written to a known location within the CA distribution point.
2) The AIA extension in all issued certificates will point to the CA cert URL in that distribition point.

Note that the same bucket may be used for the CRLs if --publish-crl is set.
"""

PUBLISH_CA_CERT_UPDATE_HELP = """
If this is enabled, the following will happen:
1) The CA certificate will be written to a known location within the CA distribution point.
2) The AIA extension in all issued certificates will point to the CA cert URL in that distribution point.

If this gets disabled, the AIA extension will not be written to any future certificates issued
by this CA. However, an existing bucket will not be deleted, and the CA certificate will not
be removed from that bucket.

Note that the same bucket may be used for the CRLs if --publish-crl is set.
"""

PUBLISH_CRL_CREATE_HELP = """
If this gets enabled, the following will happen:
1) CRLs will be written to a known location within the CA distribution point.
2) The CDP extension in all future issued certificates will point to the CRL URL in that distribution point.

Note that the same bucket may be used for the CA cert if --publish-ca-cert is set.
"""

PUBLISH_CRL_UPDATE_HELP = """
If this gets enabled, the following will happen:
1) CRLs will be written to a known location within the CA distribution point.
2) The CDP extension in all future issued certificates will point to the CRL URL in that distribution point.

If this gets disabled, the CDP extension will not be written to any future certificates issued
by this CA, and new CRLs will not be published to that bucket (which affects existing certs).
However, an existing bucket will not be deleted, and any existing CRLs will not be removed
from that bucket.

Note that the same bucket may be used for the CA cert if --publish-ca-cert is set.
"""

_VALID_KEY_USAGES = [
    'digital_signature', 'content_commitment', 'key_encipherment',
    'data_encipherment', 'key_agreement', 'cert_sign', 'crl_sign',
    'encipher_only', 'decipher_only'
]
_VALID_EXTENDED_KEY_USAGES = [
    'server_auth', 'client_auth', 'code_signing', 'email_protection',
    'time_stamping', 'ocsp_signing'
]


def AddPublishCrlFlag(parser, use_update_help_text=False):
  help_text = PUBLISH_CRL_UPDATE_HELP if use_update_help_text else PUBLISH_CRL_CREATE_HELP
  base.Argument(
      '--publish-crl',
      help=help_text,
      action='store_true',
      required=False,
      default=True).AddToParser(parser)


def AddPublishCaCertFlag(parser, use_update_help_text=False):
  help_text = PUBLISH_CA_CERT_UPDATE_HELP if use_update_help_text else PUBLISH_CA_CERT_CREATE_HELP
  base.Argument(
      '--publish-ca-cert',
      help=help_text,
      action='store_true',
      required=False,
      default=True).AddToParser(parser)


def _StripVal(val):
  return six.text_type(val).strip()


def _AddSubjectAlternativeNameFlags(parser):
  """Adds the Subject Alternative Name (san) flags.

  This will add --ip-san, --email-san, --dns-san, and --uri-san to the parser.

  Args:
    parser: The parser to add the flags to.
  """
  base.Argument(
      '--email-san',
      help='One or more comma-separated email Subject Alternative Names.',
      type=arg_parsers.ArgList(element_type=_StripVal),
      metavar='EMAIL_SAN').AddToParser(parser)
  base.Argument(
      '--ip-san',
      help='One or more comma-separated IP Subject Alternative Names.',
      type=arg_parsers.ArgList(element_type=_StripVal),
      metavar='IP_SAN').AddToParser(parser)
  base.Argument(
      '--dns-san',
      help='One or more comma-separated DNS Subject Alternative Names.',
      type=arg_parsers.ArgList(element_type=_StripVal),
      metavar='DNS_SAN').AddToParser(parser)
  base.Argument(
      '--uri-san',
      help='One or more comma-separated URI Subject Alternative Names.',
      type=arg_parsers.ArgList(element_type=_StripVal),
      metavar='URI_SAN').AddToParser(parser)


def _AddSubjectFlag(parser, required):
  base.Argument(
      '--subject',
      required=required,
      metavar='SUBJECT',
      help='X.501 name of the certificate subject. Example:'
      '--subject \"C=US,ST=California,L=Mountain View,O=Google LLC,CN=google.com\"',
      type=arg_parsers.ArgDict(key_type=_StripVal,
                               value_type=_StripVal)).AddToParser(parser)


def AddSubjectFlags(parser, subject_required=False):
  """Adds subject flags to the parser including subject string and SAN flags.

  Args:
    parser: The parser to add the flags to.
    subject_required: Whether the subject flag should be required.
  """
  _AddSubjectFlag(parser, subject_required)
  _AddSubjectAlternativeNameFlags(parser)


def AddValidityFlag(parser,
                    resource_name,
                    default_value='P10Y',
                    default_value_text='10 years'):
  base.Argument(
      '--validity',
      help='The validity of this {}, as an ISO8601 duration. Defaults to {}.'
      .format(resource_name, default_value_text),
      default=default_value).AddToParser(parser)


def AddCertificateAuthorityIssuancePolicyFlag(parser):
  base.Argument(
      '--issuance-policy',
      action='store',
      type=arg_parsers.YAMLFileContents(),
      help=("A YAML file describing this Certificate Authority's issuance "
            "policy.")
  ).AddToParser(parser)


def AddInlineReusableConfigFlags(parser, is_ca):
  """Adds flags for providing inline reusable config values.

  Args:
    parser: The parser to add the flags to.
    is_ca: Whether the current operation is on a CA. This influences the help
      text, and whether the --max-chain-length flag is added.
  """
  resource_name = 'CA' if is_ca else 'certificate'
  group = base.ArgumentGroup()
  group.AddArgument(
      base.Argument(
          '--key-usages',
          metavar='KEY_USAGES',
          help='The list of key usages for this {}. This can only be provided if `--reusable-config` is not provided.'
          .format(resource_name),
          type=arg_parsers.ArgList(
              element_type=_StripVal, choices=_VALID_KEY_USAGES)))
  group.AddArgument(
      base.Argument(
          '--extended-key-usages',
          metavar='EXTENDED_KEY_USAGES',
          help='The list of extended key usages for this {}. This can only be provided if `--reusable-config` is not provided.'
          .format(resource_name),
          type=arg_parsers.ArgList(
              element_type=_StripVal, choices=_VALID_EXTENDED_KEY_USAGES)))
  group.AddArgument(
      base.Argument(
          '--max-chain-length',
          help='Maximum depth of subordinate CAs allowed under this CA for a CA certificate. This can only be provided if `--reusable-config` is not provided.',
          default=0))

  if not is_ca:
    group.AddArgument(
        base.Argument(
            '--is-ca-cert',
            help='Whether this certificate is for a CertificateAuthority or not. Indicates the Certificate Authority field in the x509 basic constraints extension.',
            required=False,
            default=False,
            action='store_true'))

  group.AddToParser(parser)


# Flag parsing


def ParseReusableConfig(args, location, is_ca):
  """Parses the reusable config flags into an API ReusableConfigWrapper.

  Args:
    args: The parsed argument values.
    location: The location of the resource with which this reusable config
      will be used.
    is_ca: Whether the current operation is on a CA. If so, certSign and crlSign
      key usages are added.

  Returns:
    A ReusableConfigWrapper object.
  """
  messages = privateca_base.GetMessagesModule()
  has_resource = args.IsSpecified('reusable_config')
  has_inline_values = any([
      flag in vars(args) and args.IsSpecified(flag) for flag in
      ['key_usages', 'extended_key_usages', 'max_chain_length', 'is_ca_cert']
  ])

  if has_resource and has_inline_values:
    raise exceptions.InvalidArgumentException(
        '--reusable-config',
        '--reusable-config may not be specified if one or more of '
        '--key-usages, --extended-key-usages or --max-chain-length are '
        'specified.')

  if has_resource:
    # TODO(b/149316889): Use concepts library once attribute fallthroughs work.
    resource = resources.REGISTRY.Parse(
        args.reusable_config,
        collection='privateca.projects.locations.reusableConfigs',
        params={
            'projectsId': api_constants.PREDEFINED_REUSABLE_CONFIG_PROJECT,
            'locationsId': location,
        })
    return messages.ReusableConfigWrapper(
        reusableConfig=resource.RelativeName())

  base_key_usages = args.key_usages or []
  if is_ca:
    # A CA should have these KeyUsages to be RFC 5280 compliant.
    base_key_usages.extend(['cert_sign', 'crl_sign'])
  key_usage_dict = {}
  for key_usage in base_key_usages:
    key_usage = text_utils.SnakeCaseToCamelCase(key_usage)
    key_usage_dict[key_usage] = True
  extended_key_usage_dict = {}
  for extended_key_usage in args.extended_key_usages or []:
    extended_key_usage = text_utils.SnakeCaseToCamelCase(extended_key_usage)
    extended_key_usage_dict[extended_key_usage] = True

  return messages.ReusableConfigWrapper(
      reusableConfigValues=messages.ReusableConfigValues(
          keyUsage=messages.KeyUsage(
              baseKeyUsage=messages_util.DictToMessageWithErrorCheck(
                  key_usage_dict, messages.KeyUsageOptions),
              extendedKeyUsage=messages_util.DictToMessageWithErrorCheck(
                  extended_key_usage_dict, messages.ExtendedKeyUsageOptions)),
          caOptions=messages.CaOptions(
              isCa=is_ca,
              maxIssuerPathLength=int(args.max_chain_length) if is_ca else None)
      ))


def _ParseSubject(args):
  """Parses a dictionary with subject attributes into a API Subject type and common name.

  Args:
    args: The argparse namespace that contains the flag values.

  Returns:
    A tuple with (common_name, Subject) where common name is a string and
    Subject is the Subject type represented in the api.
  """
  subject_args = args.subject
  if 'CN' in subject_args:
    common_name = subject_args['CN']
  else:
    common_name = None
  remap_args = {
      'C': 'countryCode',
      'ST': 'province',
      'L': 'locality',
      'O': 'organization',
      'OU': 'organizationalUnit'
  }

  mapped_args = {}
  for key, val in subject_args.items():
    if key == 'CN':
      continue
    if key in remap_args:
      mapped_args[remap_args[key]] = val
    else:
      mapped_args[key] = val

  try:
    return common_name, messages_util.DictToMessageWithErrorCheck(
        mapped_args,
        privateca_base.GetMessagesModule().Subject)
  except messages_util.DecodeError:
    raise exceptions.InvalidArgumentException(
        '--subject', 'Unrecognized subject attribute.')


def _ParseSanFlags(args):
  """Validates the san flags and creates a SubjectAltNames message from them.

  Args:
    args: The parser that contains the flags.

  Returns:
    The SubjectAltNames message with the flag data.
  """
  email_addresses, dns_names, ip_addresses, uris = [], [], [], []
  if args.IsSpecified('email_san'):
    email_addresses = list(map(ValidateEmailSanFlag, args.email_san))
  if args.IsSpecified('dns_san'):
    dns_names = list(map(ValidateDnsSanFlag, args.dns_san))
  if args.IsSpecified('ip_san'):
    ip_addresses = list(map(ValidateIpSanFlag, args.ip_san))
  if args.IsSpecified('uri_san'):
    uris = args.uri_san

  return privateca_base.GetMessagesModule().SubjectAltNames(
      emailAddresses=email_addresses,
      dnsNames=dns_names,
      ipAddresses=ip_addresses,
      uris=uris)


def ParseSubjectFlags(args, is_ca):
  """Parses subject flags into a subject config.

  Args:
    args: The parser that contains all the flag values
    is_ca: Whether to parse this subject as a CA or not.

  Returns:
    A subject config representing the parsed flags.
  """
  messages = privateca_base.GetMessagesModule()
  subject_config = messages.SubjectConfig(
      subject=messages.Subject(), subjectAltName=messages.SubjectAltNames())

  if args.IsSpecified('subject'):
    subject_config.commonName, subject_config.subject = _ParseSubject(args)
  if _SanFlagsAreSpecified(args):
    subject_config.subjectAltName = _ParseSanFlags(args)

  if not subject_config.commonName and not _SanFlagsAreSpecified(args):
    raise exceptions.InvalidArgumentException(
        '--subject',
        'The certificate you are creating does not contain a common name or a subject alternative name.'
    )

  if is_ca and not subject_config.commonName:
    raise exceptions.InvalidArgumentException(
        '--subject',
        'A common name must be provided for a certificate authority certificate.'
    )
  if is_ca and not subject_config.subject.organization:
    raise exceptions.InvalidArgumentException(
        '--subject',
        'An organization must be provided for a certificate authority certificate.'
    )
  return subject_config


def _SanFlagsAreSpecified(args):
  """Returns true if any san flags are specified."""
  return args.IsSpecified('email_san') or args.IsSpecified(
      'dns_san') or args.IsSpecified('ip_san') or args.IsSpecified('uri_san')


def ParseIssuingOptions(args):
  """Parses the IssuingOptions proto message from the args."""
  return privateca_base.GetMessagesModule().IssuingOptions(
      includeCaCertUrl=args.publish_ca_cert,
      includeCrlAccessUrl=args.publish_crl)


def ParseIssuancePolicy(args):
  """Parses a CertificateAuthorityPolicy proto message from the args."""
  if not args.IsSpecified('issuance_policy'):
    return None
  try:
    return messages_util.DictToMessageWithErrorCheck(
        args.issuance_policy,
        privateca_base.GetMessagesModule().CertificateAuthorityPolicy)
  except messages_util.DecodeError:
    raise exceptions.InvalidArgumentException(
        '--issuance-policy', 'Unrecognized field in the Issuance Policy.')


# Flag validation helpers


def ValidateEmailSanFlag(san):
  if not re.match(_EMAIL_SAN_REGEX, san):
    raise exceptions.InvalidArgumentException('--email-san',
                                              'Invalid email address.')
  return san


def ValidateDnsSanFlag(san):
  if not re.match(_DNS_SAN_REGEX, san):
    raise exceptions.InvalidArgumentException('--dns-san',
                                              'Invalid domain name value')
  return san


def ValidateIpSanFlag(san):
  try:
    ipaddress.ip_address(san)
  except ValueError:
    raise exceptions.InvalidArgumentException('--ip-san',
                                              'Invalid IP address value.')
  return san


def AddLocationFlag(parser, resource_name, flag_name='--location'):
  """Add location flag to parser.

  Args:
    parser: The argparse parser to add the flag to.
    resource_name: The name of resource that the location refers to e.g.
      'certificate authority'
    flag_name: The name of the flag.
  """
  base.Argument(
      flag_name,
      help='Location of the {}.'.format(resource_name)).AddToParser(parser)


_REVOCATION_MAPPING = {
    'REVOCATION_REASON_UNSPECIFIED': 'unspecified',
    'KEY_COMPROMISE': 'key-compromise',
    'CERTIFICATE_AUTHORITY_COMPROMISE': 'certificate-authority-compromise',
    'AFFILIATION_CHANGED': 'affiliation-changed',
    'SUPERSEDED': 'superseded',
    'CESSATION_OF_OPERATION': 'cessation-of-operation',
    'CERTIFICATE_HOLD': 'certificate-hold',
    'PRIVILEGE_WITHDRAWN': 'privilege-withdrawn',
    'ATTRIBUTE_AUTHORITY_COMPROMISE': 'attribute-authority-compromise'
}

_REVOCATION_REASON_MAPPER = arg_utils.ChoiceEnumMapper(
    arg_name='--reason',
    default='unspecified',
    help_str='Revocation reason to include in the CRL.',
    message_enum=privateca_base.GetMessagesModule().RevokeCertificateRequest
    .ReasonValueValuesEnum,
    custom_mappings=_REVOCATION_MAPPING)


def AddRevocationReasonFlag(parser):
  """Add a revocation reason enum flag to the parser.

  Args:
    parser: The argparse parser to add the flag to.
  """
  _REVOCATION_REASON_MAPPER.choice_arg.AddToParser(parser)


def ParseRevocationChoiceToEnum(choice):
  """Return the apitools revocation reason enum value from the string choice.

  Args:
    choice: The string value of the revocation reason.

  Returns:
    The revocation enum value for the choice text.
  """
  return _REVOCATION_REASON_MAPPER.GetEnumForChoice(choice)


def ParseValidityFlag(args):
  return times.FormatDurationForJson(times.ParseDuration(args.validity))
