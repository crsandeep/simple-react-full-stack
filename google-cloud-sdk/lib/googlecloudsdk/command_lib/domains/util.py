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
"""General utilties for Cloud Domains commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.dns import util as dns_api_util
from googlecloudsdk.api_lib.domains import registrations
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.domains import flags
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core import yaml
from googlecloudsdk.core.console import console_io

LOCATIONS_COLLECTION = 'domains.projects.locations'
OPERATIONS_COLLECTION = 'domains.projects.locations.operations'
REGISTRATIONS_COLLECTION = 'domains.projects.locations.registrations'
_PROJECT = lambda: properties.VALUES.core.project.Get(required=True)


def RegistrationsUriFunc(resource):
  return ParseRegistration(resource.name).SelfLink()


# TODO(b/110077203): Add some validation.
def ParseNameServers(name_servers, cloud_dns_zone, domain):
  if name_servers is not None:
    return name_servers
  if cloud_dns_zone is not None:
    return GetCloudDnsNameServers(cloud_dns_zone, domain)
  return None


def GetCloudDnsNameServers(cloud_dns_zone, domain):
  """Fetches list of name servers from provided Cloud DNS Managed Zone."""
  # Get the managed-zone.
  dns_api_version = 'v1'
  dns = apis.GetClientInstance('dns', dns_api_version)
  zone_ref = dns_api_util.GetRegistry(dns_api_version).Parse(
      cloud_dns_zone,
      params={
          'project': properties.VALUES.core.project.GetOrFail,
      },
      collection='dns.managedZones')

  try:
    zone = dns.managedZones.Get(
        dns.MESSAGES_MODULE.DnsManagedZonesGetRequest(
            project=zone_ref.project, managedZone=zone_ref.managedZone))
  except apitools_exceptions.HttpError as error:
    raise calliope_exceptions.HttpException(error)
  domain_with_dot = domain + '.'
  if zone.dnsName != domain_with_dot:
    raise exceptions.Error(
        'The dnsName [{}] of specified Cloud DNS zone [{}] does not match the '
        'registration domain [{}]'.format(zone.dnsName, cloud_dns_zone,
                                          domain_with_dot))
  return zone.nameServers


def ParseWhoisContact(path):
  if path is None:
    return None
  raw_contact = yaml.load_path(path)
  messages = registrations.GetMessagesModule()
  parsed_contact = messages.WhoisContact(**raw_contact)
  return parsed_contact


def PromptForWhoisContact():
  """Interactively prompts for Whois Contact information."""
  if not console_io.PromptContinue(
      'Registrant contact information not provided',
      prompt_string='Do you want to enter it interactively',
      default=False):
    return None
  messages = registrations.GetMessagesModule()
  whois_contact = messages.WhoisContact()
  whois_contact.postalAddress = messages.PostalAddress()
  # TODO(b/110077203): Improve interactive address info.
  whois_contact.postalAddress.recipients.append(
      console_io.PromptWithValidator(
          validator=_ValidateNonEmpty,
          error_message='Name must not be empty.',
          prompt_string=' full name:  '))
  whois_contact.postalAddress.organization = console_io.PromptResponse(
      ' organization (if applicable):  ')
  whois_contact.email = console_io.PromptWithDefault(
      message=' email', default=properties.VALUES.core.account.Get())
  whois_contact.phoneNumber = console_io.PromptWithValidator(
      validator=_ValidateNonEmpty,
      error_message='Phone number must not be empty.',
      prompt_string=' phone number:  ',
      message='Enter phone number with country code, e.g. "+1.1234567890".')
  whois_contact.postalAddress.regionCode = console_io.PromptWithValidator(
      validator=_ValidateRegionCode,
      error_message=(
          'Country code must be in ISO 3166-1 format, e.g. "US" or "PL".\n'
          'See https://support.google.com/business/answer/6270107 for a list '
          'of valid choices.'),
      prompt_string=' country code:  ',
      message='Enter two-letter country code, e.g. "US" or "PL".')
  whois_contact.postalAddress.postalCode = console_io.PromptResponse(
      ' postal code/zipcode:  ')
  whois_contact.postalAddress.administrativeArea = console_io.PromptResponse(
      ' state (if applicable):  ')
  whois_contact.postalAddress.locality = console_io.PromptResponse(' city:  ')
  whois_contact.postalAddress.addressLines.append(
      console_io.PromptResponse(' street address (incl. building, apt):  '))
  return whois_contact


def _ValidateNonEmpty(s):
  return bool(s)


def _ValidateRegionCode(rc):
  return rc is not None and len(rc) == 2 and rc.isalpha() and rc.isupper()


def ParseWhoisPrivacy(whois_privacy):
  if whois_privacy is None:
    return None
  return flags.WHOIS_PRIVACY_ENUM_MAPPER.GetEnumForChoice(whois_privacy)


def PromptForWhoisPrivacy(choices):
  index = console_io.PromptChoice(
      options=choices,
      default=0,
      message='Specify WHOIS privacy setting')
  return ParseWhoisPrivacy(
      flags.WHOIS_PRIVACY_ENUM_MAPPER.GetChoiceForEnum(choices[index]))


def GetRegistry():
  registry = resources.REGISTRY.Clone()
  registry.RegisterApiByName('domains', 'v1alpha1')
  return registry


def ParseRegistration(registration):
  return GetRegistry().Parse(
      registration,
      params={
          'projectsId': _PROJECT,
          'locationsId': 'global'
      },
      collection=REGISTRATIONS_COLLECTION)


def ParseOperation(operation):
  return GetRegistry().Parse(
      operation,
      params={
          'projectsId': _PROJECT,
          'locationsId': 'global'
      },
      collection=OPERATIONS_COLLECTION)


def DomainNamespace(domain):
  # Return everything after the first encountered dot.
  # This is needed to accommodate two-level domains like .co.uk.
  return domain[domain.find('.'):]


def TransformMoneyType(r):
  if r is None:
    return None
  dr = r
  if not isinstance(dr, dict):
    dr = encoding.MessageToDict(r)
  return '{}.{:02d} {}'.format(dr['units'], int(dr.get('nanos', 0) / (10**7)),
                               dr.get('currencyCode', ''))
