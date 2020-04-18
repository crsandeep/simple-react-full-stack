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
"""Shared resource flags for Cloud Game Server Cluster commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.concepts import concept_parsers


def AddClusterResourceArg(parser, verb):
  """Add a resource argument for a Cloud Game Server Cluster.

  Args:
    parser: the argparse parser for the command.
    verb: str, the verb to describe the resource, such as 'update'.
  """
  concept_parsers.ConceptParser.ForResource(
      'cluster',
      GetClusterResourceSpec(),
      'Cloud Game Server Cluster to {}.'.format(verb),
      required=True).AddToParser(parser)


def GetClusterResourceSpec():
  return concepts.ResourceSpec(
      'gameservices.projects.locations.realms.gameServerClusters',
      resource_name='Game Server Cluster',
      locationsId=LocationAttributeConfig(),
      realmsId=RealmAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)


def LocationAttributeConfig():
  """Get location attribute."""
  return concepts.ResourceParameterAttributeConfig(
      name='location',
      help_text='Google Cloud location.')


def RealmAttributeConfig():
  """Get realm resource attribute."""
  return concepts.ResourceParameterAttributeConfig(
      name='realm',
      help_text=' Cloud Game Server Realm.')
