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
"""Helpers for update commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.privateca import exceptions as privateca_exceptions
from googlecloudsdk.command_lib.privateca import flags
from googlecloudsdk.command_lib.privateca import pem_utils
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core.util import files


def _ParsePemChainFromFile(pem_chain_file):
  """Parses a pem chain from a file.

  Args:
    pem_chain_file: file containing the pem_chain.

  Returns:
    The string list of certs in the chain.
  """
  try:
    pem_chain_input = files.ReadFileContents(pem_chain_file)
    return pem_utils.ValidateAndParsePemChain(pem_chain_input)

  except (files.Error, OSError, IOError):
    raise exceptions.InvalidArgumentException(
        'pem-chain',
        "Could not read provided PEM chain file '{}'.".format(pem_chain_file))


def UpdateCAFromArgs(args, current_labels):
  """Creates a CA object and update mask from CA update flags.

  Requires that args has 'pem-chain', 'publish-crl', 'publish-ca-cert', and
  update labels flags registered.

  Args:
    args: The parser that contains the flag values.
    current_labels: The current set of labels for the CA.

  Returns:
    A tuple with the CA object to update with and the list of strings
    representing the update mask, respectively.
  """
  messages = privateca_base.GetMessagesModule()
  ca_to_update = messages.CertificateAuthority()
  update_mask = []

  if 'pem_chain' in vars(args) and args.IsSpecified('pem_chain'):
    ca_to_update.pemIssuerCertChain = _ParsePemChainFromFile(args.pem_chain)
    update_mask.append('pem_issuer_cert_chain')

  if args.IsSpecified('publish_crl') or args.IsSpecified('publish_ca_cert'):
    ca_to_update.issuingOptions = messages.IssuingOptions()
    if args.IsSpecified('publish_crl'):
      ca_to_update.issuingOptions.includeCrlAccessUrl = args.publish_crl
      update_mask.append('issuing_options.include_crl_access_url')
    if args.IsSpecified('publish_ca_cert'):
      ca_to_update.issuingOptions.includeCaCertUrl = args.publish_ca_cert
      update_mask.append('issuing_options.include_ca_cert_url')

  labels_diff = labels_util.Diff.FromUpdateArgs(args)
  labels_update = labels_diff.Apply(messages.CertificateAuthority.LabelsValue,
                                    current_labels)
  if labels_update.needs_update:
    ca_to_update.labels = labels_update.labels
    update_mask.append('labels')

  if args.IsSpecified('issuance_policy'):
    ca_to_update.certificatePolicy = flags.ParseIssuancePolicy(args)
    update_mask.append('certificate_policy')

  if not update_mask:
    raise privateca_exceptions.NoUpdateExceptions(
        'No updates found for the requested CA.')

  return ca_to_update, update_mask
