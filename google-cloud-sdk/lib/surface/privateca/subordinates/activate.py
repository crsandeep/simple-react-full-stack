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
"""Activate a pending Certificate Authority."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.privateca import operations
from googlecloudsdk.command_lib.privateca import pem_utils
from googlecloudsdk.command_lib.privateca import resource_args
from googlecloudsdk.core.util import files


class Activate(base.SilentCommand):
  r"""Activate a subordinate certificate authority in a pending state.

  ## EXAMPLES

  To activate a subordinate CA named 'server-tls-1' in the location 'us' using
  a PEM certificate
  chain in 'chain.crt':

    $ {command} server-tls-1 \
      --location us \
      --pem-chain ./chain.crt
  """

  @staticmethod
  def Args(parser):
    resource_args.AddCertificateAuthorityPositionalResourceArg(
        parser, 'to activate')
    base.Argument(
        '--pem-chain',
        required=True,
        help='A file containing a list of PEM-encoded certificates, starting '
        'with the current CA certificate and ending with the root CA '
        'certificate.').AddToParser(parser)

  def _ParsePemChainFromFile(self, pem_chain_file):
    """Parses a pem chain from a file, splitting the leaf cert and chain.

    Args:
      pem_chain_file: file containing the pem_chain.

    Raises:
      exceptions.InvalidArgumentException if not enough certificates are
      included.

    Returns:
      A tuple with (leaf_cert, rest_of_chain)
    """
    try:
      pem_chain_input = files.ReadFileContents(pem_chain_file)
    except (files.Error, OSError, IOError):
      raise exceptions.BadFileException(
          "Could not read provided PEM chain file '{}'.".format(pem_chain_file))

    certs = pem_utils.ValidateAndParsePemChain(pem_chain_input)
    if len(certs) < 2:
      raise exceptions.InvalidArgumentException(
          'pem-chain',
          'The pem_chain must include at least two certificates - the subordinate CA certificate and an issuer certificate.'
      )

    return certs[0], certs[1:]

  def Run(self, args):
    client = privateca_base.GetClientInstance()
    messages = privateca_base.GetMessagesModule()
    ca_ref = args.CONCEPTS.certificate_authority.Parse()

    pem_cert, pem_chain = self._ParsePemChainFromFile(args.pem_chain)

    operation = client.projects_locations_certificateAuthorities.Activate(
        messages
        .PrivatecaProjectsLocationsCertificateAuthoritiesActivateRequest(
            name=ca_ref.RelativeName(),
            activateCertificateAuthorityRequest=messages
            .ActivateCertificateAuthorityRequest(
                pemCaCertificate=pem_cert, pemCaCertificateChain=pem_chain)))

    operations.Await(operation, 'Activating Certificate Authority.')
