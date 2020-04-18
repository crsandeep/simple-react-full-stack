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
"""`gcloud domains registrations detach` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.domains import operations
from googlecloudsdk.api_lib.domains import registrations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.domains import flags
from googlecloudsdk.command_lib.domains import resource_args
from googlecloudsdk.command_lib.domains import util
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Detach(base.DeleteCommand):
  """Detach a domain registration.

  This command transfers the domain to direct management by Google Domains.
  The domain remains valid until expiry.

  See https://support.google.com/domains/answer/6339340 for information how to
  access it in Google Domains after detaching.

  ## EXAMPLES

  To detach a registration for example.com, run:

    $ {command} example.com

  """

  @staticmethod
  def Args(parser):
    resource_args.AddRegistrationResourceArg(parser, 'to detach')
    flags.AddAsyncFlagToParser(parser)

  def Run(self, args):
    client = registrations.RegistrationsClient()
    registration_ref = args.CONCEPTS.registration.Parse()

    # TODO(b/110077203) Tweak the message.
    console_io.PromptContinue(
        'You are about to detach registration [{}]'.format(
            registration_ref.registrationsId),
        throw_if_unattended=True,
        cancel_on_no=True)

    response = client.Detach(registration_ref)

    if args.async_:
      # TODO(b/110077203): Log something sensible.
      return response

    operations_client = operations.Client.FromApiVersion('v1alpha1')
    operation_ref = util.ParseOperation(response.name)
    response = operations_client.WaitForOperation(
        operation_ref,
        'Waiting for [{}] to complete'.format(operation_ref.Name()))

    log.UpdatedResource(
        registration_ref.Name(),
        'registration',
        details=('Note:\nRegistration remains valid until expiry. See '
                 'https://support.google.com/domains/answer/6339340 for '
                 'information how to access it in Google Domains.'))
    return response
