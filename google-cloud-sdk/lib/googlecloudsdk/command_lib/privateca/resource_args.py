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
"""Helpers for parsing resource arguments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.privateca import base
from googlecloudsdk.api_lib.privateca import constants as api_constants
from googlecloudsdk.api_lib.privateca import locations
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.privateca import exceptions as privateca_exceptions
from googlecloudsdk.command_lib.util.concepts import concept_parsers


def ReusableConfigAttributeConfig():
  # ReusableConfig is always an anchor attribute so help_text is unused.
  return concepts.ResourceParameterAttributeConfig(name='reusable_config')


def CertificateAttributeConfig(fallthroughs=None):
  # Certificate is always an anchor attribute so help_text is unused.
  return concepts.ResourceParameterAttributeConfig(
      name='certificate', fallthroughs=fallthroughs or [])


def CertificateAuthorityAttributeConfig(arg_name='certificate_authority'):
  return concepts.ResourceParameterAttributeConfig(
      name=arg_name,
      help_text='The issuing certificate authority of the {resource}.')


def LocationAttributeConfig(arg_name='location', fallthroughs=None):
  return concepts.ResourceParameterAttributeConfig(
      name=arg_name,
      help_text='The location of the {resource}.',
      fallthroughs=fallthroughs or [])


def ProjectAttributeConfig(fallthroughs=None):
  """DO NOT USE THIS for most flags.

  This config is only useful when you want to provide an explicit project
  fallthrough. For most cases, prefer concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG.

  Args:
    fallthroughs: List of deps.Fallthrough objects to provide project values.

  Returns:
    A concepts.ResourceParameterAttributeConfig for a project.
  """
  return concepts.ResourceParameterAttributeConfig(
      name='project',
      help_text='The project containing the {resource}.',
      fallthroughs=fallthroughs or [])


def CreateReusableConfigResourceSpec(associated_resource):
  """Create a resource spec for a ReusableConfig.

  Defaults to the predefined project for reusable configs.

  Args:
    associated_resource: The name of the resource that this reusable config
      is associated with. This will be used in the helptext.

  Returns:
    A concepts.ResourceSpec for a reusable config.
  """
  # For now, reusable configs exist in a single project.
  location_fallthrough = deps.Fallthrough(
      function=lambda: '',
      hint='location will default to the same location as the {}'.format(
          associated_resource),
      active=False,
      plural=False)
  project_fallthrough = deps.Fallthrough(
      function=lambda: api_constants.PREDEFINED_REUSABLE_CONFIG_PROJECT,
      hint='project will default to {}'.format(
          api_constants.PREDEFINED_REUSABLE_CONFIG_PROJECT),
      active=False,
      plural=False)
  return concepts.ResourceSpec(
      'privateca.projects.locations.reusableConfigs',
      resource_name='reusable config',
      reusableConfigsId=ReusableConfigAttributeConfig(),
      locationsId=LocationAttributeConfig(fallthroughs=[location_fallthrough]),
      projectsId=ProjectAttributeConfig(fallthroughs=[project_fallthrough]))


def CreateCertificateAuthorityResourceSpec(
    display_name,
    certificate_authority_attribute='certificate_authority',
    location_attribute='location'):
  return concepts.ResourceSpec(
      'privateca.projects.locations.certificateAuthorities',
      # This will be formatted and used as {resource} in the help text.
      resource_name=display_name,
      certificateAuthoritiesId=CertificateAuthorityAttributeConfig(
          certificate_authority_attribute),
      locationsId=LocationAttributeConfig(location_attribute),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)


def CreateCertificateResourceSpec(display_name, id_fallthroughs=None):
  return concepts.ResourceSpec(
      'privateca.projects.locations.certificateAuthorities.certificates',
      # This will be formatted and used as {resource} in the help text.
      resource_name=display_name,
      certificatesId=CertificateAttributeConfig(
          fallthroughs=id_fallthroughs or []),
      certificateAuthoritiesId=CertificateAuthorityAttributeConfig('issuer'),
      locationsId=LocationAttributeConfig('issuer-location'),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)


def AddCertificateAuthorityPositionalResourceArg(parser, verb):
  """Add a positional resource argument for a Certificate Authority.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
  """
  arg_name = 'CERTIFICATE_AUTHORITY'
  concept_parsers.ConceptParser.ForResource(
      arg_name,
      CreateCertificateAuthorityResourceSpec(arg_name),
      'The certificate authority {}.'.format(verb),
      required=True).AddToParser(parser)


def AddCertificatePositionalResourceArg(parser, verb):
  """Add a positional resource argument for a Certificate.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
  """
  arg_name = 'CERTIFICATE'
  concept_parsers.ConceptParser.ForResource(
      arg_name,
      CreateCertificateResourceSpec(arg_name),
      'The certificate {}.'.format(verb),
      required=True).AddToParser(parser)

# Resource validation.


def ValidateKmsKeyVersionLocation(version_ref):
  """Raises an exception if the key version is in an unsupported location."""
  supported_locations = locations.GetSupportedLocations()
  if version_ref.locationsId not in supported_locations:
    raise exceptions.InvalidArgumentException(
        '--kms-key-version',
        'Resource is in an unsupported location. Supported locations are: {}.'
        .format(', '.join(sorted(supported_locations))))


def CheckExpectedCAType(expected_type, ca):
  """Raises an exception if the Certificate Authority type is not expected_type.

  Args:
    expected_type: The expected type.
    ca: The ca object to check.
  """
  ca_type_enum = base.GetMessagesModule(
  ).CertificateAuthority.TypeValueValuesEnum
  if expected_type == ca_type_enum.SUBORDINATE and ca.type != expected_type:
    raise privateca_exceptions.InvalidCertificateAuthorityTypeError(
        'Cannot perform subordinates command on Root CA. Please use the `privateca roots` command group instead.'
    )
  elif expected_type == ca_type_enum.SELF_SIGNED and ca.type != expected_type:
    raise privateca_exceptions.InvalidCertificateAuthorityTypeError(
        'Cannot perform roots command on Subordinate CA. Please use the `privateca subordinates` command group instead.'
    )
