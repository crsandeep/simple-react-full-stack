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
"""`gcloud domains registrations create` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.domains import operations
from googlecloudsdk.api_lib.domains import registrations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.domains import flags
from googlecloudsdk.command_lib.domains import resource_args
from googlecloudsdk.command_lib.domains import util
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create a new domain registration.

  This command creates a new domain registration.

  ## EXAMPLES

  To create a new registration for example.com interactively, run:

    $ {command} example.com
  """

  @staticmethod
  def Args(parser):
    resource_args.AddRegistrationResourceArg(parser, 'to create')
    flags.AddRegistrationSettingsFlagsToParser(parser)
    flags.AddValidateOnlyFlagToParser(parser, 'create')
    flags.AddAsyncFlagToParser(parser)
    labels_util.AddCreateLabelsFlags(parser)

  def Run(self, args):
    client = registrations.RegistrationsClient()

    registration_ref = args.CONCEPTS.registration.Parse()
    location_ref = registration_ref.Parent()

    labels = labels_util.ParseCreateArgs(
        args, client.messages.Registration.LabelsValue)

    name_servers = util.ParseNameServers(args.name_servers, args.cloud_dns_zone,
                                         registration_ref.registrationsId)
    registrant_contact = util.ParseWhoisContact(
        args.registrant_contact_from_file)
    if registrant_contact is None:
      registrant_contact = util.PromptForWhoisContact()
    if registrant_contact is None:
      raise exceptions.Error(
          'Registrant contact is required. It can be provided interactively or '
          'through --registrant-contact-from-file flag.')

    availability = client.CheckAvailability(
        location_ref, registration_ref.registrationsId).availability

    if availability.available != client.availability_enum.AVAILABLE:
      raise exceptions.Error(
          'Domain [{}] is not available for registration: [{}]'.format(
              registration_ref.registrationsId, availability.available))

    whois_privacy = util.ParseWhoisPrivacy(args.whois_privacy)
    if whois_privacy is None:
      whois_privacy = util.PromptForWhoisPrivacy(
          availability.supportedWhoisPrivacy)

    hsts_notice_accepted = False
    if client.notices_enum.HSTS_PRELOADED in availability.notices:
      console_io.PromptContinue(
          ('{} is a secure namespace. You may purchase {} now but it will '
           'require an SSL certificate for website connection.').format(
               util.DomainNamespace(availability.domainName),
               availability.domainName),
          throw_if_unattended=True,
          cancel_on_no=True)
      hsts_notice_accepted = True

    console_io.PromptContinue(
        'Yearly price: {}\n'.format(
            util.TransformMoneyType(availability.yearlyPrice)),
        throw_if_unattended=True,
        cancel_on_no=True)

    response = client.Create(
        location_ref,
        registration_ref.registrationsId,
        name_servers=name_servers,
        registrant_contact=registrant_contact,
        whois_privacy=whois_privacy,
        yearly_price=availability.yearlyPrice,
        hsts_notice_accepted=hsts_notice_accepted,
        labels=labels,
        validate_only=args.validate_only)

    if args.validate_only:
      # TODO(b/110077203): Log something sensible.
      return

    if args.async_:
      # TODO(b/110077203): Log something sensible.
      return response

    operations_client = operations.Client.FromApiVersion('v1alpha1')
    operation_ref = util.ParseOperation(response.name)
    response = operations_client.WaitForOperation(
        operation_ref,
        'Waiting for [{}] to complete'.format(operation_ref.Name()))

    log.CreatedResource(registration_ref.Name(), 'registration')
    return response
