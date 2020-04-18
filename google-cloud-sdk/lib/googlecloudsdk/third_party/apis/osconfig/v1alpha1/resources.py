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


BASE_URL = 'https://osconfig.googleapis.com/v1alpha1/'
DOCS_URL = 'https://cloud.google.com/'


class Collections(enum.Enum):
  """Collections for all supported apis."""

  FOLDERS = (
      'folders',
      'folders/{foldersId}',
      {},
      [u'foldersId'],
      True
  )
  FOLDERS_ASSIGNMENTS = (
      'folders.assignments',
      '{+name}',
      {
          '':
              'folders/{foldersId}/assignments/{assignmentsId}',
      },
      [u'name'],
      True
  )
  FOLDERS_OSCONFIGS = (
      'folders.osConfigs',
      '{+name}',
      {
          '':
              'folders/{foldersId}/osConfigs/{osConfigsId}',
      },
      [u'name'],
      True
  )
  ORGANIZATIONS = (
      'organizations',
      'organizations/{organizationsId}',
      {},
      [u'organizationsId'],
      True
  )
  ORGANIZATIONS_ASSIGNMENTS = (
      'organizations.assignments',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/assignments/{assignmentsId}',
      },
      [u'name'],
      True
  )
  ORGANIZATIONS_OSCONFIGS = (
      'organizations.osConfigs',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/osConfigs/{osConfigsId}',
      },
      [u'name'],
      True
  )
  PROJECTS = (
      'projects',
      'projects/{projectsId}',
      {},
      [u'projectsId'],
      True
  )
  PROJECTS_ASSIGNMENTS = (
      'projects.assignments',
      '{+name}',
      {
          '':
              'projects/{projectsId}/assignments/{assignmentsId}',
      },
      [u'name'],
      True
  )
  PROJECTS_OSCONFIGS = (
      'projects.osConfigs',
      '{+name}',
      {
          '':
              'projects/{projectsId}/osConfigs/{osConfigsId}',
      },
      [u'name'],
      True
  )
  PROJECTS_PATCHJOBS = (
      'projects.patchJobs',
      '{+name}',
      {
          '':
              'projects/{projectsId}/patchJobs/{patchJobsId}',
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
