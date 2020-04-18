# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Resource definitions for cloud platform apis."""

import enum


BASE_URL = 'https://gameservices.googleapis.com/v1beta/'
DOCS_URL = 'https://cloud.google.com/solutions/gaming/'


class Collections(enum.Enum):
  """Collections for all supported apis."""

  PROJECTS = (
      'projects',
      'projects/{projectsId}',
      {},
      [u'projectsId'],
      True
  )
  PROJECTS_LOCATIONS = (
      'projects.locations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}',
      },
      [u'name'],
      True
  )
  PROJECTS_LOCATIONS_GAMESERVERDEPLOYMENTS = (
      'projects.locations.gameServerDeployments',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'gameServerDeployments/{gameServerDeploymentsId}',
      },
      [u'name'],
      True
  )
  PROJECTS_LOCATIONS_GAMESERVERDEPLOYMENTS_CONFIGS = (
      'projects.locations.gameServerDeployments.configs',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'gameServerDeployments/{gameServerDeploymentsId}/configs/'
              '{configsId}',
      },
      [u'name'],
      True
  )
  PROJECTS_LOCATIONS_OPERATIONS = (
      'projects.locations.operations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/operations/'
              '{operationsId}',
      },
      [u'name'],
      True
  )
  PROJECTS_LOCATIONS_REALMS = (
      'projects.locations.realms',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/realms/'
              '{realmsId}',
      },
      [u'name'],
      True
  )
  PROJECTS_LOCATIONS_REALMS_GAMESERVERCLUSTERS = (
      'projects.locations.realms.gameServerClusters',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/realms/'
              '{realmsId}/gameServerClusters/{gameServerClustersId}',
      },
      [u'name'],
      True
  )

  def __init__(self, collection_name, path, flat_paths, params,
               enable_uri_parsing):
    self.collection_name = collection_name
    self.path = path
    self.flat_paths = flat_paths
    self.params = params
    self.enable_uri_parsing = enable_uri_parsing
