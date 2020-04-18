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


BASE_URL = 'https://recommender.googleapis.com/v1alpha1/'
DOCS_URL = 'https://cloud.google.com/recommender/docs/'


class Collections(enum.Enum):
  """Collections for all supported apis."""

  OPERATIONS = (
      'operations',
      'operations/{+operationId}',
      {},
      [u'operationId'],
      True
  )
  PROJECTS = (
      'projects',
      'projects/{projectsId}',
      {},
      [u'projectsId'],
      True
  )
  PROJECTS_LOCATIONS = (
      'projects.locations',
      'projects/{projectsId}/locations/{locationsId}',
      {},
      [u'projectsId', u'locationsId'],
      False
  )
  PROJECTS_LOCATIONS_RECOMMENDERS = (
      'projects.locations.recommenders',
      'projects/{projectsId}/locations/{locationsId}/recommenders/'
      '{recommendersId}',
      {},
      [u'projectsId', u'locationsId', u'recommendersId'],
      False
  )
  PROJECTS_LOCATIONS_RECOMMENDERS_RECOMMENDATIONS = (
      'projects.locations.recommenders.recommendations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/recommenders/'
              '{recommendersId}/recommendations/{recommendationsId}',
      },
      [u'name'],
      True
  )
  PROJECTS_RULES = (
      'projects.rules',
      '{+name}',
      {
          '':
              'projects/{projectsId}/rules/{rulesId}',
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
