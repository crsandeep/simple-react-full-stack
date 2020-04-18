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
"""`gcloud domains registrations update` command."""

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
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(base.UpdateCommand):
  """Update a domain registration.

  This command updates an existing registration.

  ## EXAMPLES

  To enable WHOIS privacy for example.com, run:

    $ {command} example.com --whois-privacy=use-whois-privacy-proxy
  """

  @staticmethod
  def Args(parser):
    resource_args.AddRegistrationResourceArg(parser, 'to update')
    flags.AddRegistrationSettingsFlagsToParser(parser)
    flags.AddValidateOnlyFlagToParser(parser, 'update')
    flags.AddAsyncFlagToParser(parser)
    labels_util.AddUpdateLabelsFlags(parser)

  def Run(self, args):
    client = registrations.RegistrationsClient()

    registration_ref = args.CONCEPTS.registration.Parse()

    name_servers = util.ParseNameServers(args.name_servers, args.cloud_dns_zone,
                                         registration_ref.registrationsId)

    registrant_contact = util.ParseWhoisContact(
        args.registrant_contact_from_file)

    whois_privacy = util.ParseWhoisPrivacy(args.whois_privacy)

    new_labels = None
    labels_diff = labels_util.Diff.FromUpdateArgs(args)
    if labels_diff.MayHaveUpdates():
      orig_resource = client.Get(registration_ref)
      new_labels = labels_diff.Apply(
          client.messages.Registration.LabelsValue,
          orig_resource.labels).GetOrNone()

    response = client.Patch(
        registration_ref,
        name_servers=name_servers,
        registrant_contact=registrant_contact,
        whois_privacy=whois_privacy,
        labels=new_labels,
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

    log.UpdatedResource(registration_ref.Name(), 'registration')
    return response
