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
"""Shared resource arguments and flags."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.secrets import completers as secrets_completers
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import resources

# Args


def AddCreateIfMissing(parser, resource, positional=False, **kwargs):
  parser.add_argument(
      _ArgOrFlag('create-if-missing', positional),
      action='store_true',
      help=('Create the {resource} if it does not exist. If this flag is not '
            'set, the command will return an error when attempting to update a '
            '{resource} that does not exist.').format(resource=resource),
      **kwargs)


def AddDataFile(parser, positional=False, **kwargs):
  parser.add_argument(
      _ArgOrFlag('data-file', positional),
      metavar='PATH',
      help=('File path from which to read secret data. Set this to "-" to read '
            'the secret data from stdin.'),
      **kwargs)


def AddPolicy(parser, positional=False, **kwargs):
  parser.add_argument(
      _ArgOrFlag('replication-policy', positional),
      metavar='POLICY',
      help=('The type of replication policy to apply to this secret. Allowed '
            'values are "automatic" and "user-managed". If user-managed then '
            '--locations must also be provided.'),
      **kwargs)


def AddProject(parser, positional=False, **kwargs):
  concept_parsers.ConceptParser.ForResource(
      name=_ArgOrFlag('project', positional),
      resource_spec=GetProjectResourceSpec(),
      group_help='The project ID.',
      **kwargs).AddToParser(parser)


def AddLocation(parser, purpose, positional=False, **kwargs):
  concept_parsers.ConceptParser.ForResource(
      name=_ArgOrFlag('location', positional),
      resource_spec=GetLocationResourceSpec(),
      group_help='The location {}.'.format(purpose),
      **kwargs).AddToParser(parser)


def AddLocations(parser, resource, positional=False, **kwargs):
  parser.add_argument(
      _ArgOrFlag('locations', positional),
      action=arg_parsers.UpdateAction,
      metavar='LOCATION',
      type=arg_parsers.ArgList(),
      help=('Comma-separated list of locations in which the {resource} should '
            'be replicated.').format(resource=resource),
      **kwargs)


def AddSecret(parser, purpose, positional=False, **kwargs):
  concept_parsers.ConceptParser.ForResource(
      name=_ArgOrFlag('secret', positional),
      resource_spec=GetSecretResourceSpec(),
      group_help='The secret {}.'.format(purpose),
      **kwargs).AddToParser(parser)


def AddBetaSecret(parser, purpose, positional=False, **kwargs):
  concept_parsers.ConceptParser.ForResource(
      name=_ArgOrFlag('secret', positional),
      resource_spec=GetBetaSecretResourceSpec(),
      group_help='The secret {}.'.format(purpose),
      **kwargs).AddToParser(parser)


def AddVersion(parser, purpose, positional=False, **kwargs):
  concept_parsers.ConceptParser.ForResource(
      name=_ArgOrFlag('version', positional),
      resource_spec=GetVersionResourceSpec(),
      group_help=('Numeric secret version {} or `latest` to use the latest '
                  'version.').format(purpose),
      **kwargs).AddToParser(parser)


def AddBetaVersion(parser, purpose, positional=False, **kwargs):
  # Adds a SecretVersion parser using the beta Secrets completer
  concept_parsers.ConceptParser.ForResource(
      name=_ArgOrFlag('version', positional),
      resource_spec=GetBetaVersionResourceSpec(),
      group_help=('Numeric secret version {} or `latest` to use the '
                  'latest version.').format(purpose),
      **kwargs).AddToParser(parser)


def _ArgOrFlag(name, positional):
  """Returns the argument name in resource argument format or flag format.

  Args:
      name (str): name of the argument
      positional (bool): whether the argument is positional

  Returns:
      arg (str): the argument or flag
  """
  if positional:
    return name.upper().replace('-', '_')
  return '--{}'.format(name)


### Attribute configurations


def GetProjectAttributeConfig():
  return concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG


def GetLocationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='location',
      help_text='The location of the {resource}.',
      completion_request_params={'fieldMask': 'name'},
      completion_id_field='name')


def GetSecretAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='secret',
      help_text='The secret of the {resource}.',
      completer=secrets_completers.SecretsCompleter)


def GetBetaSecretAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='secret',
      help_text='The secret of the {resource}.',
      completer=secrets_completers.BetaSecretsCompleter)


def GetVersionAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='version',
      help_text='The version of the {resource}.',
      completion_request_params={'fieldMask': 'name'},
      completion_id_field='name')

# Resource specs


def GetProjectResourceSpec():
  return concepts.ResourceSpec(
      resource_collection='secretmanager.projects',
      resource_name='project',
      plural_name='projects',
      disable_auto_completers=False,
      projectsId=GetProjectAttributeConfig())


def GetLocationResourceSpec():
  return concepts.ResourceSpec(
      resource_collection='secretmanager.projects.locations',
      resource_name='location',
      plural_name='locations',
      disable_auto_completers=False,
      locationsId=GetLocationAttributeConfig(),
      projectsId=GetProjectAttributeConfig())


def GetSecretResourceSpec():
  return concepts.ResourceSpec(
      resource_collection='secretmanager.projects.secrets',
      resource_name='secret',
      plural_name='secrets',
      disable_auto_completers=False,
      secretsId=GetSecretAttributeConfig(),
      projectsId=GetProjectAttributeConfig())


def GetBetaSecretResourceSpec():
  return concepts.ResourceSpec(
      resource_collection='secretmanager.projects.secrets',
      resource_name='secret',
      plural_name='secrets',
      disable_auto_completers=False,
      secretsId=GetBetaSecretAttributeConfig(),
      projectsId=GetProjectAttributeConfig())


def GetVersionResourceSpec():
  return concepts.ResourceSpec(
      'secretmanager.projects.secrets.versions',
      resource_name='version',
      plural_name='version',
      disable_auto_completers=False,
      versionsId=GetVersionAttributeConfig(),
      secretsId=GetSecretAttributeConfig(),
      projectsId=GetProjectAttributeConfig())


def GetBetaVersionResourceSpec():
  return concepts.ResourceSpec(
      'secretmanager.projects.secrets.versions',
      resource_name='version',
      plural_name='version',
      disable_auto_completers=False,
      versionsId=GetVersionAttributeConfig(),
      secretsId=GetBetaSecretAttributeConfig(),
      projectsId=GetProjectAttributeConfig())


# Resource parsers


def ParseProjectRef(ref, version=None, **kwargs):
  kwargs['collection'] = 'secretmanager.projects'
  return resources.REGISTRY.Parse(ref, api_version=version, **kwargs)


def ParseLocationRef(ref, version=None, **kwargs):
  kwargs['collection'] = 'secretmanager.projects.locations'
  return resources.REGISTRY.Parse(ref, api_version=version, **kwargs)


def ParseSecretRef(ref, version=None, **kwargs):
  kwargs['collection'] = 'secretmanager.projects.secrets'
  return resources.REGISTRY.Parse(ref, api_version=version, **kwargs)


def ParseVersionRef(ref, version=None, **kwargs):
  kwargs['collection'] = 'secretmanager.projects.secrets.versions'
  return resources.REGISTRY.Parse(ref, api_version=version, **kwargs)
