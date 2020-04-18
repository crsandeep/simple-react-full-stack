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
"""API client library for Cloud Domains Registrations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import exceptions


class NoFieldsSpecifiedError(exceptions.Error):
  """Error when no fields were specified for a Patch operation."""


def GetClientInstance():
  return apis.GetClientInstance('domains', 'v1alpha1')


def GetMessagesModule(client=None):
  client = client or GetClientInstance()
  return client.MESSAGES_MODULE


class RegistrationsClient(object):
  """Client for registrations service in the Cloud Domains API."""

  def __init__(self, client=None, messages=None):
    self.client = client or GetClientInstance()
    self.messages = messages or GetMessagesModule(client)
    self._service = self.client.projects_locations_registrations

  @property
  def notices_enum(self):
    return self.messages.DomainAvailability.NoticesValueListEntryValuesEnum

  @property
  def availability_enum(self):
    return self.messages.DomainAvailability.AvailableValueValuesEnum

  def Create(self,
             parent_ref,
             domain,
             name_servers,
             registrant_contact,
             whois_privacy,
             yearly_price,
             hsts_notice_accepted=False,
             labels=None,
             validate_only=False):
    """Creates a Registration.

    Args:
      parent_ref: a Resource reference to a domains.projects.locations resource
        for the parent of this registration.
      domain: str, the name of the domain to register. Used as resource name.
      name_servers: List of authoritative name servers (DNS).
      registrant_contact: WhoisContact that specifies registrant contact
        information.
      whois_privacy: WhoisPrivacyEnum that specifies Whois privacy setting.
      yearly_price: price for the domain registration and its cost for the
      following years.
      hsts_notice_accepted: bool, Whether HSTS notice was presented & accepted.
      labels: Unified GCP Labels for the resource.
      validate_only: If set to true, performs only validation, without creating.

    Returns:
      Operation: the long running operation to create registration.
    """
    if name_servers:
      dns_config = self.messages.DnsConfig(nameServers=name_servers)
    else:
      dns_config = None

    whois_config = self.messages.WhoisConfig(
        privacy=whois_privacy, registrantContact=registrant_contact)

    notices = []
    if hsts_notice_accepted:
      notices = [
          self.messages.Registration.NoticesValueListEntryValuesEnum
          .HSTS_PRELOADED
      ]
    # pylint: disable=line-too-long
    create_req = self.messages.DomainsProjectsLocationsRegistrationsCreateRequest(
        parent=parent_ref.RelativeName(),
        validateOnly=validate_only,
        registration=self.messages.Registration(
            domainName=domain,
            dnsConfig=dns_config,
            whoisConfig=whois_config,
            yearlyPrice=yearly_price,
            notices=notices,
            labels=labels))

    return self._service.Create(create_req)

  def Detach(self, registration_ref):
    req = self.messages.DomainsProjectsLocationsRegistrationsDetachRequest(
        name=registration_ref.RelativeName())
    return self._service.Detach(req)

  def Delete(self, registration_ref):
    req = self.messages.DomainsProjectsLocationsRegistrationsDeleteRequest(
        name=registration_ref.RelativeName())
    return self._service.Delete(req)

  def Get(self, registration_ref):
    get_req = self.messages.DomainsProjectsLocationsRegistrationsGetRequest(
        name=registration_ref.RelativeName())
    return self._service.Get(get_req)

  def List(self, parent_ref, limit=None, page_size=None, list_filter=None):
    """List the domain registrations in a given project.

    Args:
      parent_ref: a Resource reference to a domains.projects.locations resource
        to list registrations for.
      limit: int, the total number of results to return from the API.
      page_size: int, the number of results in each batch from the API.
      list_filter: str, filter to apply in the list request.

    Returns:
      A generator of the domain registrations in the project.
    """
    list_req = self.messages.DomainsProjectsLocationsRegistrationsListRequest(
        parent=parent_ref.RelativeName(),
        filter=list_filter)
    return list_pager.YieldFromList(
        self._service,
        list_req,
        batch_size=page_size,
        limit=limit,
        field='registrations',
        batch_size_attribute='pageSize')

  def Patch(self,
            registration_ref,
            name_servers=None,
            registrant_contact=None,
            whois_privacy=None,
            labels=None,
            validate_only=False):
    """Updates a Registration.

    Any fields not specified will not be updated; at least one field must be
    specified.

    Args:
      registration_ref: a Resource reference to a
        domains.projects.locations.registrations resource.
      name_servers: List of authoritative name servers (DNS) or None.
      registrant_contact: WhoisContact or None, specifies registrant contact
        information.
      whois_privacy: WhoisPrivacyEnum or None, specifies Whois privacy setting.
      labels: Unified GCP Labels for the resource.
      validate_only: If set to true, performs only validation, without creating.

    Returns:
      Operation: the long running operation to patch registration.

    Raises:
      NoFieldsSpecifiedError: if no fields were specified.
    """
    registration = self.messages.Registration()
    update_mask = []

    if name_servers:
      registration.dnsConfig = self.messages.DnsConfig(nameServers=name_servers)
      update_mask.append('dns_config')

    if registrant_contact or whois_privacy:
      registration.whoisConfig = self.messages.WhoisConfig(
          privacy=whois_privacy, registrantContact=registrant_contact)
      if registrant_contact:
        update_mask.append('whois_config.registrant_contact')
      if whois_privacy:
        update_mask.append('whois_config.privacy')

    if labels is not None:
      registration.labels = labels
      update_mask.append('labels')

    if not update_mask:
      raise NoFieldsSpecifiedError('Must specify at least one field to update.')
    patch_req = self.messages.DomainsProjectsLocationsRegistrationsPatchRequest(
        registration=registration,
        name=registration_ref.RelativeName(),
        updateMask=','.join(update_mask),
        validateOnly=validate_only)

    return self._service.Patch(patch_req)

  def CheckAvailability(self, parent_ref, domain):
    # pylint: disable=line-too-long
    request = self.messages.DomainsProjectsLocationsRegistrationsCheckAvailabilityRequest(
        parent=parent_ref.RelativeName(), domainName=domain)
    return self._service.CheckAvailability(request)

  def SearchAvailability(self, parent_ref, query):
    # pylint: disable=line-too-long
    request = self.messages.DomainsProjectsLocationsRegistrationsSearchAvailabilityRequest(
        parent=parent_ref.RelativeName(), query=query)
    return self._service.SearchAvailability(request).availability
