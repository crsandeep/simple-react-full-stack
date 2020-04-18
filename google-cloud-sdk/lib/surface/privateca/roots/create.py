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
"""Create a new root certificate authority."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.privateca import base as privateca_base
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


class Create(base.CreateCommand):
  r"""Create a new root certificate authority.

  ## EXAMPLES

  To create a root CA that supports one layer of subordinates:

      $ {command} prod-root \
        --kms-key-version "projects/joonix-pki/locations/us-west1/keyRings/kr1/cryptoKeys/k1/cryptoKeyVersions/1" \
        --subject "CN=Joonix Production Root CA" \
        --max-chain-length 1

  To create a root CA and restrict what it can issue:

      $ {command} prod-root \
        --kms-key-version "projects/joonix-pki/locations/us-west1/keyRings/kr1/cryptoKeys/k1/cryptoKeyVersions/1" \
        --subject "CN=Joonix Production Root CA" \
        --issuance-policy policy.yaml

  To create a root CA that doesn't publicly publish CA certificate and CRLs:

      $ {command} root-2 \
        --kms-key-version "projects/joonix-pki/locations/us-west1/keyRings/kr1/cryptoKeys/k1/cryptoKeyVersions/1" \
        --subject "CN=Joonix Production Root CA" \
        --issuance-policy policy.yaml \
        --no-publish-ca-cert \
        --no-publish-crl
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
    concept_parsers.ConceptParser(
        [
            presentation_specs.ResourcePresentationSpec(
                'CERTIFICATE_AUTHORITY',
                privateca_resource_args.CreateCertificateAuthorityResourceSpec(
                    'Certificate Authority'),
                'The name of the root CA to create.',
                required=True,
                # We'll get these from the KMS key resource.
                flag_name_overrides={
                    'location': '',
                    'project': '',
                }),
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

  @staticmethod
  def ParseResourceArgs(args):
    """Parse, validate and return the CA and KMS key version args from the CLI.

    Args:
      args: The parsed arguments from the command-line.

    Returns:
      Tuple containing the Resource objects for the KMS key version and CA,
      respectively.
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

    return (kms_key_version_ref, ca_ref)

  def Run(self, args):
    kms_key_version_ref, ca_ref = self.ParseResourceArgs(args)
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

    p4sa_email = p4sa.GetOrCreate(project_ref)
    bucket_ref = storage.CreateBucketForCertificateAuthority(ca_ref)

    p4sa.AddResourceRoleBindings(p4sa_email, kms_key_ref, bucket_ref)

    new_ca = self.messages.CertificateAuthority(
        type=self.messages.CertificateAuthority.TypeValueValuesEnum.SELF_SIGNED,
        lifetime=lifetime,
        config=self.messages.CertificateConfig(
            reusableConfig=reusable_config_wrapper,
            subjectConfig=subject_config),
        cloudKmsKeyVersion=kms_key_version_ref.RelativeName(),
        certificatePolicy=issuance_policy,
        issuingOptions=issuing_options,
        gcsBucket=bucket_ref.bucket,
        labels=labels)

    operation = self.client.projects_locations_certificateAuthorities.Create(
        self.messages
        .PrivatecaProjectsLocationsCertificateAuthoritiesCreateRequest(
            certificateAuthority=new_ca,
            certificateAuthorityId=ca_ref.Name(),
            parent=ca_ref.Parent().RelativeName(),
            requestId=request_utils.GenerateRequestId()))

    ca_response = operations.Await(operation, 'Creating Certificate Authority.')
    ca = operations.GetMessageFromResponse(ca_response,
                                           self.messages.CertificateAuthority)
    log.status.Print('Created Certificate Authority [{}].'.format(ca.name))
