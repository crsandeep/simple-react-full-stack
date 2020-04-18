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
"""Revoke a certificate."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.api_lib.privateca import certificate_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.privateca import flags
from googlecloudsdk.command_lib.privateca import operations
from googlecloudsdk.command_lib.privateca import resource_args
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import log
from googlecloudsdk.core import resources
from googlecloudsdk.core.util import times

_CERTIFICATE_COLLECTION_NAME = 'privateca.projects.locations.certificateAuthorities.certificates'


def _ParseCertificateResource(args):
  """Gets the certificate resource to be revoked based on the specified args."""
  # Option 1: user specified full resource name for the certificate.
  cert_ref = args.CONCEPTS.certificate.Parse()
  if cert_ref:
    return cert_ref

  if not args.IsSpecified('issuer'):
    raise exceptions.RequiredArgumentException(
        '--issuer',
        ('The issuing CA is required if a full resource name is not provided '
         'for --certificate.'))

  issuer_ref = args.CONCEPTS.issuer.Parse()
  if not issuer_ref:
    raise exceptions.RequiredArgumentException(
        '--issuer',
        ('The issuer flag is not fully specified. Please add the '
         "--issuer-location flag or specify the issuer's full resource name."))

  # Option 2: user specified certificate ID + issuer.
  if args.IsSpecified('certificate'):
    return resources.REGISTRY.Parse(
        args.certificate,
        collection=_CERTIFICATE_COLLECTION_NAME,
        params={
            'projectsId': issuer_ref.projectsId,
            'locationsId': issuer_ref.locationsId,
            'certificateAuthoritiesId': issuer_ref.certificateAuthoritiesId,
        })

  # Option 3: user specified serial number + issuer.
  if args.IsSpecified('serial_number'):
    certificate = certificate_utils.GetCertificateBySerialNum(
        issuer_ref, args.serial_number)
    return resources.REGISTRY.Parse(
        certificate.name, collection=_CERTIFICATE_COLLECTION_NAME)

  raise exceptions.OneOfArgumentsRequiredException(
      ['--certificate', '--serial-number'],
      ('To revoke a Certificate, please provide either its resource ID or '
       'serial number.'))


class Revoke(base.SilentCommand):
  r"""Revoke a certificate.

  Revokes the given certificate for the given reason.

  ## EXAMPLES

  To revoke the 'frontend-server-tls' certificate due to key compromise:

    $ {command} \
      --certificate frontend-server-tls \
      --issuer server-tls-1 --issuer-location us-west1 \
      --reason key_compromise

  To revoke the a certificate with the serial number
  '7dc1d9186372de2e1f4824abb1c4c9e5e43cbb40' due to a newer one being issued:

    $ {command} \
      --serial-number 7dc1d9186372de2e1f4824abb1c4c9e5e43cbb40 \
      --issuer server-tls-1 --issuer-location us-west1 \
      --reason superseded
  """

  @staticmethod
  def Args(parser):
    id_group = parser.add_group(
        mutex=True, required=True, help='The certificate identifier.')
    base.Argument(
        '--serial-number',
        help='The serial number of the certificate.').AddToParser(id_group)
    concept_parsers.ConceptParser([
        presentation_specs.ResourcePresentationSpec(
            '--certificate',
            resource_args.CreateCertificateResourceSpec('certificate'),
            'The certificate to revoke.',
            flag_name_overrides={
                'issuer': '',
                'issuer-location': '',
                'project': '',
            },
            group=id_group),
        presentation_specs.ResourcePresentationSpec(
            '--issuer',
            resource_args.CreateCertificateAuthorityResourceSpec(
                'Issuing CA', 'issuer', 'issuer-location'),
            'The issuing certificate authority of the certificate to revoke.',
            required=False),
    ]).AddToParser(parser)

    flags.AddRevocationReasonFlag(parser)

  def Run(self, args):
    cert_ref = _ParseCertificateResource(args)

    reason = flags.ParseRevocationChoiceToEnum(args.reason)

    client = privateca_base.GetClientInstance()
    messages = privateca_base.GetMessagesModule()

    operation = client.projects_locations_certificateAuthorities_certificates.Revoke(
        messages.
        PrivatecaProjectsLocationsCertificateAuthoritiesCertificatesRevokeRequest(
            name=cert_ref.RelativeName(),
            revokeCertificateRequest=messages.RevokeCertificateRequest(
                reason=reason)))

    response = operations.Await(operation, 'Revoking Certificate.')
    certificate = operations.GetMessageFromResponse(response,
                                                    messages.Certificate)

    revoke_time = times.ParseDateTime(
        certificate.revocationDetails.revocationTime)
    log.Print('Revoked certificate [{}] at {}.'.format(
        certificate.name, times.FormatDateTime(revoke_time,
                                               tzinfo=times.LOCAL)))
