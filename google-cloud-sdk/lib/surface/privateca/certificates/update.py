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
"""Update an existing certificate."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.api_lib.privateca import request_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.privateca import operations
from googlecloudsdk.command_lib.privateca import resource_args
from googlecloudsdk.command_lib.util.args import labels_util


class Update(base.UpdateCommand):
  r"""Update an existing certificate.

  ## EXAMPLES

   To update labels on a certificate:

      $ {command} frontend-server-tls \
        --issuer server-tls-1 --issuer-location us \
        --update-labels in_use=true
  """

  NO_CHANGES_MESSAGE = (
      'There are no changes to the certificate [{certificate}].')

  @staticmethod
  def Args(parser):
    resource_args.AddCertificatePositionalResourceArg(parser, 'to update')
    labels_util.AddUpdateLabelsFlags(parser)

  def _RunUpdate(self, client, messages, original_cert, args):
    # Collect the list of update masks
    labels_diff = labels_util.GetAndValidateOpsFromArgs(args)
    labels_update = labels_diff.Apply(messages.Certificate.LabelsValue,
                                      original_cert.labels)

    if not labels_update.needs_update:
      raise exceptions.InvalidArgumentException(
          'labels',
          self.NO_CHANGES_MESSAGE.format(certificate=original_cert.name))

    original_cert.labels = labels_update.labels

    operation = client.projects_locations_certificateAuthorities_certificates.Patch(
        messages.
        PrivatecaProjectsLocationsCertificateAuthoritiesCertificatesPatchRequest(
            name=original_cert.name,
            certificate=original_cert,
            updateMask='labels',
            requestId=request_utils.GenerateRequestId()))

    return operations.Await(operation, 'Updating Certificate.')

  def Run(self, args):
    client = privateca_base.GetClientInstance()
    messages = privateca_base.GetMessagesModule()

    certificate_ref = args.CONCEPTS.certificate.Parse()
    # Attempt to get the certificate
    certificate = client.projects_locations_certificateAuthorities_certificates.Get(
        messages
        .PrivatecaProjectsLocationsCertificateAuthoritiesCertificatesGetRequest(
            name=certificate_ref.RelativeName()))

    # The certificate exists, update it
    return self._RunUpdate(client, messages, certificate, args)
