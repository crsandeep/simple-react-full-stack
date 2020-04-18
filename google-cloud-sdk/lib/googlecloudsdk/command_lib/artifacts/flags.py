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
"""Common flags for artifacts print-settings commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.concepts import concept_parsers


def RepoAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='repository', help_text='Repository of the {resource}.')


def LocationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='location', help_text='Location of the {resource}.')


def GetRepoResourceSpec():
  return concepts.ResourceSpec(
      'artifactregistry.projects.locations.repositories',
      resource_name='repository',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=LocationAttributeConfig(),
      repositoriesId=RepoAttributeConfig())


def GetLocationResourceSpec():
  return concepts.ResourceSpec(
      'artifactregistry.projects.locations',
      resource_name='location',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=LocationAttributeConfig())


def GetScopeFlag():
  return base.Argument(
      '--scope',
      help=('The scope to associate with the Artifact Registry registry. '
            'If not specified, Artifact Registry is set as the default '
            'registry.'))


def GetImagePathOptionalArg():
  """Gets IMAGE_PATH optional positional argument."""
  help_txt = textwrap.dedent("""\
  An Artifact Registry repository or a container image.
  If not specified, default config values are used.

  A valid docker repository has the format of
    LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY-ID

  A valid image has the format of
    LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY-ID/IMAGE_PATH
""")
  return base.Argument('IMAGE_PATH', help=help_txt, nargs='?')


def GetImageRequiredArg():
  """Gets IMAGE required positional argument."""
  help_txt = textwrap.dedent("""\
  A container image.

  A valid container image has the format of
    LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY-ID/IMAGE

  A valid container image that can be referenced by tag or digest, has the format of
    LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY-ID/IMAGE:tag
    LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY-ID/IMAGE@sha256:digest
""")
  return base.Argument('IMAGE', help=help_txt)


def GetDockerImageRequiredArg():
  help_txt = textwrap.dedent("""\
  Docker image - The container image that you want to tag.

A valid container image can be referenced by tag or digest, has the format of
  LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY-ID/IMAGE:tag
  LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY-ID/IMAGE@sha256:digest
""")
  return base.Argument('DOCKER_IMAGE', help=help_txt)


def GetTagRequiredArg():
  help_txt = textwrap.dedent("""\
  Image tag - The container image tag.

A valid Docker tag has the format of
  LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY-ID/IMAGE:tag
""")
  return base.Argument('DOCKER_TAG', help=help_txt)


def GetRepoFlag():
  return concept_parsers.ConceptParser.ForResource(
      '--repository',
      GetRepoResourceSpec(),
      ('The Artifact Registry repository. If not specified, '
       'the current artifacts/repository is used.'),
      required=False)


def GetLocationFlag():
  return concept_parsers.ConceptParser.ForResource(
      '--location',
      GetLocationResourceSpec(),
      ('The Artifact Registry repository location. If not specified, '
       'the current artifacts/location is used.'),
      required=True)


def GetOptionalLocationFlag():
  return concept_parsers.ConceptParser.ForResource(
      '--location',
      GetLocationResourceSpec(),
      ('The Artifact Registry repository location. You can also set '
       '--location=all to list repositories across all locations. '
       'If you omit this flag, the default location is used if you set the '
       'artifacts/location property. Otherwise, omitting this flag '
       'lists repositories across all locations.'),
      required=False)


def GetIncludeTagsFlag():
  return base.Argument(
      '--include-tags',
      help=('If specified, all tags associated with each image digest are '
            'displayed.'),
      action='store_true',
      required=False)


def GetDeleteTagsFlag():
  return base.Argument(
      '--delete-tags',
      help='If specified, all tags associated with the image are deleted.',
      action='store_true',
      required=False)
