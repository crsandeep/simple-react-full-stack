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
"""Create a new subordinate certificate authority."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.api_lib.privateca import certificate_utils
from googlecloudsdk.api_lib.privateca import request_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.kms import resource_args as kms_resource_args
from googlecloudsdk.command_lib.privateca import flags
from googlecloudsdk.command_lib.privateca import iam
from googlecloudsdk.command_lib.privateca import operations
from googlecloudsdk.command_lib.privateca import p4sa
from googlecloudsdk.command_lib.privateca import resource_args as privateca_resource_args
from googlecloudsdk.command_lib.privateca import storage
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import log
from googlecloudsdk.core import resources
from googlecloudsdk.core.util import files


def _ParseResourceArgs(args):
  """Parses, validates and returns the resource args from the CLI.

  Args:
    args: The parsed arguments from the command-line.

  Returns:
    Tuple containing the Resource objects for (KMS key version, CA, issuer).
  """
  kms_key_version_ref = args.CONCEPTS.kms_key_version.Parse()
  # TODO(b/149316889): Use concepts library once attribute fallthroughs work.
  ca_ref = resources.REGISTRY.Parse(
      args.CERTIFICATE_AUTHORITY,
      collection='privateca.projects.locations.certificateAuthorities',
      params={
          'projectsId': kms_key_version_ref.projectsId,
          'locationsId': kms_key_version_ref.locationsId,
      })
  issuer_ref = None if args.create_csr else args.CONCEPTS.issuer.Parse()

  if ca_ref.projectsId != kms_key_version_ref.projectsId:
    raise exceptions.InvalidArgumentException(
        'CERTIFICATE_AUTHORITY',
        'Certificate Authority must be in the same project as the KMS key '
        'version.')

  if ca_ref.locationsId != kms_key_version_ref.locationsId:
    raise exceptions.InvalidArgumentException(
        'CERTIFICATE_AUTHORITY',
        'Certificate Authority must be in the same location as the KMS key '
        'version.')

  privateca_resource_args.ValidateKmsKeyVersionLocation(kms_key_version_ref)

  return (kms_key_version_ref, ca_ref, issuer_ref)


class Create(base.CreateCommand):
  r"""Create a new subordinate certificate authority.

  ## EXAMPLES
  To create a subordinate CA named 'server-tls-1' whose issuer is on Private CA:

    $ {command} server-tls-1 \
      --subject "CN=Joonix TLS CA" \
      --issuer prod-root --issuer-location us-west1 \
      --kms-crypto-key-version "projects/joonix-pki/locations/us-west1/keyRings/kr1/cryptoKeys/key2/cryptoKeyVersions/1"

  To create a subordinate CA named 'server-tls-1' whose issuer is located
  elsewhere:

    $ {command} server-tls-1 \
      --subject "CN=Joonix TLS CA" \
      --create-csr \
      --csr-output-file "./csr.pem" \
      --kms-crypto-key-version "projects/joonix-pki/locations/us-west1/keyRings/kr1/cryptoKeys/key2/cryptoKeyVersions/1"
  """

  def __init__(self, *args, **kwargs):
    super(Create, self).__init__(*args, **kwargs)
    self.client = privateca_base.GetClientInstance()
    self.messages = privateca_base.GetMessagesModule()

  @staticmethod
  def Args(parser):
    reusable_config_group = parser.add_group(
        mutex=True, required=False,
        help='The X.509 configuration used for the CA certificate.')
    issuer_configuration_group = parser.add_group(
        mutex=True, required=True,
        help='The issuer configuration used for this CA certificate.')

    concept_parsers.ConceptParser([
        presentation_specs.ResourcePresentationSpec(
            'CERTIFICATE_AUTHORITY',
            privateca_resource_args.CreateCertificateAuthorityResourceSpec(
                'Certificate Authority'),
            'The name of the subordinate CA to create.',
            required=True,
            # We'll get these from the KMS key resource.
            flag_name_overrides={
                'location': '',
                'project': '',
            }),
        presentation_specs.ResourcePresentationSpec(
            '--issuer',
            privateca_resource_args.CreateCertificateAuthorityResourceSpec(
                'Issuer'),
            'The issuing certificate authority to use, if it is on Private CA.',
            prefixes=True,
            group=issuer_configuration_group),
        presentation_specs.ResourcePresentationSpec(
            '--kms-key-version',
            kms_resource_args.GetKmsKeyVersionResourceSpec(),
            'The KMS key version backing this CA.',
            required=True),
        presentation_specs.ResourcePresentationSpec(
            '--reusable-config',
            privateca_resource_args.CreateReusableConfigResourceSpec('CA'),
            'The Reusable Config containing X.509 values for this CA.',
            flag_name_overrides={
                'location': '',
                'project': '',
            },
            group=reusable_config_group)
    ]).AddToParser(parser)
    flags.AddSubjectFlags(parser, subject_required=True)
    flags.AddPublishCaCertFlag(parser, use_update_help_text=False)
    flags.AddPublishCrlFlag(parser, use_update_help_text=False)
    flags.AddInlineReusableConfigFlags(reusable_config_group, is_ca=True)
    flags.AddValidityFlag(
        parser,
        resource_name='CA',
        default_value='P10Y',
        default_value_text='10 years')
    flags.AddCertificateAuthorityIssuancePolicyFlag(parser)
    labels_util.AddCreateLabelsFlags(parser)

    offline_issuer_group = issuer_configuration_group.add_group(
        help=('If the issuing CA is not hosted on Private CA, you must provide '
              'these settings:'))
    base.Argument(
        '--create-csr',
        help=('Indicates that a CSR should be generated which can be signed by '
              'the issuing CA. This must be set if --issuer is not provided.'),
        action='store_const',
        const=True,
        default=False,
        required=True).AddToParser(offline_issuer_group)
    base.Argument(
        '--csr-output-file',
        help=('The path where the resulting PEM-encoded CSR file should be '
              'written.'),
        required=True).AddToParser(offline_issuer_group)

  def _SignCsr(self, issuer_ref, csr, lifetime):
    """Issues a certificate under the given issuer with the given settings."""
    certificate_id = 'subordinate-{}'.format(certificate_utils.GenerateCertId())
    certificate_name = '{}/certificates/{}'.format(issuer_ref.RelativeName(),
                                                   certificate_id)
    cert_request = self.messages.PrivatecaProjectsLocationsCertificateAuthoritiesCertificatesCreateRequest(
        certificateId=certificate_id,
        parent=issuer_ref.RelativeName(),
        requestId=request_utils.GenerateRequestId(),
        certificate=self.messages.Certificate(
            name=certificate_name, lifetime=lifetime, pemCsr=csr))

    operation = self.client.projects_locations_certificateAuthorities_certificates.Create(
        cert_request)
    cert_response = operations.Await(operation, 'Signing CA cert.')
    return operations.GetMessageFromResponse(cert_response,
                                             self.messages.Certificate)

  def _ActivateCertificateAuthority(self, ca_ref, certificate):
    """Activates the given CA using the given certificate."""
    activate_request = self.messages.PrivatecaProjectsLocationsCertificateAuthoritiesActivateRequest(
        name=ca_ref.RelativeName(),
        activateCertificateAuthorityRequest=self.messages
        .ActivateCertificateAuthorityRequest(
            pemCaCertificate=certificate.pemCertificate,
            pemCaCertificateChain=certificate.pemCertificateChain))
    operation = self.client.projects_locations_certificateAuthorities.Activate(
        activate_request)
    return operations.Await(operation, 'Activating CA.')

  def Run(self, args):
    kms_key_version_ref, ca_ref, issuer_ref = _ParseResourceArgs(args)
    kms_key_ref = kms_key_version_ref.Parent()
    project_ref = ca_ref.Parent().Parent()

    subject_config = flags.ParseSubjectFlags(args, is_ca=True)
    issuing_options = flags.ParseIssuingOptions(args)
    issuance_policy = flags.ParseIssuancePolicy(args)
    reusable_config_wrapper = flags.ParseReusableConfig(args,
                                                        ca_ref.locationsId,
                                                        is_ca=True)
    lifetime = flags.ParseValidityFlag(args)
    labels = labels_util.ParseCreateArgs(
        args, self.messages.CertificateAuthority.LabelsValue)

    iam.CheckCreateCertificateAuthorityPermissions(project_ref, kms_key_ref)
    if issuer_ref:
      iam.CheckCreateCertificatePermissions(issuer_ref)

    p4sa_email = p4sa.GetOrCreate(project_ref)
    bucket_ref = storage.CreateBucketForCertificateAuthority(ca_ref)

    p4sa.AddResourceRoleBindings(p4sa_email, kms_key_ref, bucket_ref)

    new_ca = self.messages.CertificateAuthority(
        type=self.messages.CertificateAuthority.TypeValueValuesEnum.SUBORDINATE,
        lifetime=lifetime,
        config=self.messages.CertificateConfig(
            reusableConfig=reusable_config_wrapper,
            subjectConfig=subject_config),
        cloudKmsKeyVersion=kms_key_version_ref.RelativeName(),
        certificatePolicy=issuance_policy,
        issuingOptions=issuing_options,
        gcsBucket=bucket_ref.bucket,
        labels=labels)

    operations.Await(
        self.client.projects_locations_certificateAuthorities.Create(
            self.messages
            .PrivatecaProjectsLocationsCertificateAuthoritiesCreateRequest(
                certificateAuthority=new_ca,
                certificateAuthorityId=ca_ref.Name(),
                parent=ca_ref.Parent().RelativeName(),
                requestId=request_utils.GenerateRequestId())),
        'Creating Certificate Authority.')

    csr_response = self.client.projects_locations_certificateAuthorities.GetCsr(
        self.messages
        .PrivatecaProjectsLocationsCertificateAuthoritiesGetCsrRequest(
            name=ca_ref.RelativeName()))
    csr = csr_response.pemCsr

    if args.create_csr:
      files.WriteFileContents(args.csr_output_file, csr)
      log.status.Print(
          "Created Certificate Authority [{}] and saved CSR to '{}'.".format(
              ca_ref.RelativeName(), args.csr_output_file))
      return

    if issuer_ref:
      ca_certificate = self._SignCsr(issuer_ref, csr, lifetime)
      self._ActivateCertificateAuthority(ca_ref, ca_certificate)
      log.status.Print('Created Certificate Authority [{}].'.format(
          ca_ref.RelativeName()))
      return

    # This should not happen because of the required arg group, but it protects
    # us in case of future additions.
    raise exceptions.OneOfArgumentsRequiredException(
        ['--issuer', '--create-csr'],
        ('To create a subordinate CA, please provide either an issuer or the '
         '--create-csr flag to output a CSR to be signed by another issuer.'))
