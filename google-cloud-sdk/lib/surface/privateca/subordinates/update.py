# Lint as: python3
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
"""Update a subordinate certificate authority."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.api_lib.privateca import request_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.privateca import flags
from googlecloudsdk.command_lib.privateca import operations
from googlecloudsdk.command_lib.privateca import resource_args
from googlecloudsdk.command_lib.privateca import update_utils
from googlecloudsdk.command_lib.util.args import labels_util


class Update(base.UpdateCommand):
  r"""Update an existing subordinate certificate authority.

  ## EXAMPLES
    To update labels on a subordinate CA:

      $ {command} server-tls-1 \
        --location us-west1 \
        --update-labels foo=bar

    To disable publishing CRLs for a subordinate CA:

      $ {command} server-tls-1 \
        --location us-west1 \
        --no-publish-crl
  """

  @staticmethod
  def Args(parser):
    resource_args.AddCertificateAuthorityPositionalResourceArg(
        parser, 'to update')
    flags.AddPublishCrlFlag(parser, use_update_help_text=True)
    flags.AddPublishCaCertFlag(parser, use_update_help_text=True)
    base.Argument(
        '--pem-chain',
        required=False,
        help='A file containing a list of PEM-encoded certificates that represent the issuing chain of this CA.'
    ).AddToParser(parser)
    flags.AddCertificateAuthorityIssuancePolicyFlag(parser)
    labels_util.AddUpdateLabelsFlags(parser)

  def Run(self, args):
    client = privateca_base.GetClientInstance()
    messages = privateca_base.GetMessagesModule()

    ca_ref = args.CONCEPTS.certificate_authority.Parse()

    current_ca = client.projects_locations_certificateAuthorities.Get(
        messages.PrivatecaProjectsLocationsCertificateAuthoritiesGetRequest(
            name=ca_ref.RelativeName()))

    resource_args.CheckExpectedCAType(
        messages.CertificateAuthority.TypeValueValuesEnum.SUBORDINATE,
        current_ca)

    ca_to_update, update_mask = update_utils.UpdateCAFromArgs(
        args, current_ca.labels)

    operation = client.projects_locations_certificateAuthorities.Patch(
        messages.PrivatecaProjectsLocationsCertificateAuthoritiesPatchRequest(
            name=ca_ref.RelativeName(),
            certificateAuthority=ca_to_update,
            updateMask=','.join(update_mask),
            requestId=request_utils.GenerateRequestId()))

    return operations.Await(operation, 'Updating Subordinate CA.')
