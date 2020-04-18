# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Utilities for Cloud Datastore index management commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

from googlecloudsdk.api_lib.datastore import util
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.third_party.appengine.datastore import datastore_index


def GetIndexesService():
  """Returns the service for interacting with the Datastore Admin Service.

  This is used to manage the datastore indexes (create/delete).
  """
  return util.GetClient().projects_indexes


ASCENDING = (
    util.GetMessages().GoogleDatastoreAdminV1IndexedProperty
    .DirectionValueValuesEnum.ASCENDING)

DESCENDING = (
    util.GetMessages().GoogleDatastoreAdminV1IndexedProperty
    .DirectionValueValuesEnum.DESCENDING)

NO_ANCESTOR = (
    util.GetMessages().GoogleDatastoreAdminV1Index.AncestorValueValuesEnum.NONE)

ALL_ANCESTORS = (
    util.GetMessages().GoogleDatastoreAdminV1Index.AncestorValueValuesEnum
    .ALL_ANCESTORS)

CREATING = (
    util.GetMessages().GoogleDatastoreAdminV1Index.StateValueValuesEnum.CREATING
)


def ApiMessageToIndexDefinition(proto):
  """Converts a GoogleDatastoreAdminV1Index to an index definition structure."""
  properties = []
  for prop_proto in proto.properties:
    prop_definition = datastore_index.Property(name=str(prop_proto.name))
    if prop_proto.direction == DESCENDING:
      prop_definition.direction = 'desc'
    else:
      prop_definition.direction = 'asc'
    properties.append(prop_definition)
  index = datastore_index.Index(kind=str(proto.kind), properties=properties)
  if proto.ancestor is not NO_ANCESTOR:
    index.ancestor = True
  return proto.indexId, index


def BuildIndexProto(ancestor, kind, project_id, properties):
  """Builds and returns a GoogleDatastoreAdminV1Index."""
  messages = util.GetMessages()
  proto = messages.GoogleDatastoreAdminV1Index()
  proto.projectId = project_id
  proto.kind = kind
  proto.ancestor = ancestor
  proto.state = CREATING
  props = []
  for prop in properties:
    prop_proto = messages.GoogleDatastoreAdminV1IndexedProperty()
    prop_proto.name = prop.name
    if prop.direction == 'asc':
      prop_proto.direction = ASCENDING
    else:
      prop_proto.direction = DESCENDING
    props.append(prop_proto)
  proto.properties = props
  return proto


def BuildIndex(is_ancestor, kind, properties):
  index = datastore_index.Index(
      kind=str(kind),
      properties=[
          datastore_index.Property(name=str(prop[0]), direction=prop[1])
          for prop in properties
      ])
  index.ancestor = is_ancestor
  return index


def NormalizeIndexes(indexes):
  """Removes the last index property if it is __key__:asc which is redundant."""
  for index in indexes:
    if (index.properties and index.properties[-1].name == '__key__' and
        index.properties[-1].direction == 'asc'):
      index.properties.pop()
  return set(indexes)


def ListIndexes(project_id):
  response = GetIndexesService().List(
      util.GetMessages().DatastoreProjectsIndexesListRequest(
          projectId=project_id))
  return {ApiMessageToIndexDefinition(index) for index in response.indexes}


def CreateIndexes(project_id, indexes_to_create):
  """Sends the index creation requests."""
  cnt = 0
  detail_message = None
  with progress_tracker.ProgressTracker(
      '.',
      autotick=False,
      detail_message_callback=lambda: detail_message) as pt:
    for index in indexes_to_create:
      GetIndexesService().Create(
          BuildIndexProto(
              ALL_ANCESTORS if index.ancestor else NO_ANCESTOR,
              kind=index.kind,
              project_id=project_id,
              properties=index.properties))
      cnt = cnt + 1
      detail_message = '{0:.0%}'.format(cnt / len(indexes_to_create))
      pt.Tick()


def DeleteIndexes(project_id, indexes_to_delete_ids):
  """Sends the index deletion requests."""
  cnt = 0
  detail_message = None
  with progress_tracker.ProgressTracker(
      '.',
      autotick=True,
      detail_message_callback=lambda: detail_message,
      tick_delay=3):
    for index_id in indexes_to_delete_ids:
      GetIndexesService().Delete(
          util.GetMessages().DatastoreProjectsIndexesDeleteRequest(
              projectId=project_id, indexId=index_id))
      cnt = cnt + 1
      detail_message = '{0:.0%}'.format(cnt / len(indexes_to_delete_ids))
      sys.stderr.flush()


def CreateMissingIndexes(project_id, index_definitions):
  indexes = ListIndexes(project_id)
  normalized_indexes = NormalizeIndexes(index_definitions.indexes)
  new_indexes = normalized_indexes - {index for _, index in indexes}
  CreateIndexes(project_id, new_indexes)
