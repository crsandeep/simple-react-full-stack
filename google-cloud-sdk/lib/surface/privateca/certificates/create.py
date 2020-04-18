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
"""Create a certificate."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.api_lib.privateca import certificate_utils
from googlecloudsdk.api_lib.privateca import request_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.privateca import flags
from googlecloudsdk.command_lib.privateca import key_generation
from googlecloudsdk.command_lib.privateca import operations
from googlecloudsdk.command_lib.privateca import resource_args
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files


KEY_OUTPUT_HELP = """The path where the generated private key file should be written (in PEM format).

Note: possession of this key file could allow anybody to act as this certificate's
subject. Please make sure that you store this key file in a secure location at all
times, and ensure that only authorized users have access to it."""


class Create(base.CreateCommand):
  r"""Create a new certificate.

  ## EXAMPLES

  To create a certificate using a CSR:

      $ {command} frontend-server-tls \
        --issuer server-tls-1 --issuer-location us \
        --csr ./csr.pem \
        --cert-out ./cert.pem \
        --validity P30D

    To create a certificate using a client-generated key:

      $ {command} frontend-server-tls \
        --issuer server-tls-1 --issuer-location us \
        --generate-key \
        --key-output-file ./key \
        --cert-output-file ./cert.pem \
        --dns-san www.joonix.net \
        --reusable-config server-tls
  """

  @staticmethod
  def Args(parser):
    base.Argument(
        '--cert-output-file',
        help='The path where the resulting PEM-encoded certificate chain file should be written (ordered from leaf to root).',
        required=False).AddToParser(parser)
    flags.AddValidityFlag(parser, 'certificate', 'P30D', '30 days')
    labels_util.AddCreateLabelsFlags(parser)

    cert_generation_group = parser.add_group(
        mutex=True, required=True, help='Certificate generation method.')
    base.Argument(
        '--csr', help='A PEM-encoded certificate signing request file path.'
    ).AddToParser(cert_generation_group)

    key_generation_group = cert_generation_group.add_group(
        help='Alternatively, to generate a new key pair, use the following:')
    base.Argument(
        '--generate-key',
        help='Use this flag to have a new RSA-2048 private key securely generated on your machine.',
        action='store_const',
        const=True,
        default=False,
        required=True).AddToParser(key_generation_group)
    base.Argument(
        '--key-output-file', help=KEY_OUTPUT_HELP,
        required=True).AddToParser(key_generation_group)

    subject_group = key_generation_group.add_group(
        help='The subject names for the certificate.', required=True)
    flags.AddSubjectFlags(subject_group)
    reusable_config_group = key_generation_group.add_group(
        mutex=True, help='The x509 configuration used for this certificate.')
    flags.AddInlineReusableConfigFlags(reusable_config_group, is_ca=False)

    cert_arg = 'CERTIFICATE'
    id_fallthrough = deps.Fallthrough(
        function=certificate_utils.GenerateCertId,
        hint='certificate id will default to an automatically generated id',
        active=False,
        plural=False)
    concept_parsers.ConceptParser([
        presentation_specs.ResourcePresentationSpec(
            cert_arg,
            resource_args.CreateCertificateResourceSpec(cert_arg,
                                                        [id_fallthrough]),
            'The name of the certificate to issue. If the name is omitted, a '
            'random name will be generated according to the following format'
            ': {YYYYMMDD}-{3 random alphanumeric characters}-{3 random alph'
            'anumeric characters}.',
            required=True)
    ]).AddToParser(parser)

    concept_parsers.ConceptParser([
        presentation_specs.ResourcePresentationSpec(
            '--reusable-config',
            resource_args.CreateReusableConfigResourceSpec('certificate'),
            'The Reusable Config containing X.509 values for this certificate.',
            flag_name_overrides={
                'location': '',
                'project': '',
            },
            group=reusable_config_group)
    ]).AddToParser(reusable_config_group)

  def _ReadCsr(self, request, csr_file):
    try:
      return files.ReadFileContents(csr_file)
    except (files.Error, OSError, IOError):
      raise exceptions.BadFileException(
          "Could not read provided CSR file '{}'.".format(csr_file))

  def _WritePemChain(self, pem_cert, issuing_chain, cert_file):
    try:
      pem_chain = [pem_cert] + issuing_chain
      files.WriteFileContents(cert_file, '\n'.join(pem_chain))
    except (files.Error, OSError, IOError):
      raise exceptions.BadFileException(
          "Could not write certificate to '{}'.".format(cert_file))

  def _GenerateCertificateConfig(self, request, args, location):
    messages = privateca_base.GetMessagesModule()
    private_key, public_key = key_generation.RSAKeyGen(2048)
    key_generation.ExportPrivateKey(args.key_output_file, private_key)

    config = messages.CertificateConfig()
    config.publicKey = messages.PublicKey()
    config.publicKey.key = public_key
    config.publicKey.type = messages.PublicKey.TypeValueValuesEnum.PEM_RSA_KEY
    config.reusableConfig = flags.ParseReusableConfig(
        args, location, is_ca=args.is_ca_cert)
    config.subjectConfig = flags.ParseSubjectFlags(args, is_ca=args.is_ca_cert)

    return config

  def Run(self, args):
    client = privateca_base.GetClientInstance()
    messages = privateca_base.GetMessagesModule()

    cert_ref = args.CONCEPTS.certificate.Parse()
    if not cert_ref:
      raise exceptions.InvalidArgumentException(
          'CERTIFICATE', 'A certificate resource must be specified.')

    labels = labels_util.ParseCreateArgs(args, messages.Certificate.LabelsValue)

    request = messages.PrivatecaProjectsLocationsCertificateAuthoritiesCertificatesCreateRequest(
    )
    request.certificate = messages.Certificate()
    request.certificateId = cert_ref.Name()
    request.certificate.name = cert_ref.RelativeName()
    request.certificate.lifetime = flags.ParseValidityFlag(args)
    request.certificate.labels = labels
    request.parent = cert_ref.Parent().RelativeName()
    request.requestId = request_utils.GenerateRequestId()

    if args.csr:
      request.certificate.pemCsr = self._ReadCsr(request, args.csr)
    elif args.generate_key:
      request.certificate.config = self._GenerateCertificateConfig(
          request, args, cert_ref.locationsId)
    else:
      # This should not happen because of the required arg group, but protects
      # in case of future additions.
      raise exceptions.OneOfArgumentsRequiredException(
          ['--csr', '--generate-key'],
          ('To create a certificate, please specify either a CSR or the '
           '--generate-key flag to create a new key.'))

    operation = client.projects_locations_certificateAuthorities_certificates.Create(
        request)
    cert_response = operations.Await(operation, 'Creating Certificate.')
    certificate = operations.GetMessageFromResponse(cert_response,
                                                    messages.Certificate)

    if args.IsSpecified('cert_output_file'):
      self._WritePemChain(certificate.pemCertificate,
                          certificate.pemCertificateChain,
                          args.cert_output_file)

    log.status.Print('Created Certificate [{}].'.format(certificate.name))
