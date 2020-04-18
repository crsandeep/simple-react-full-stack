# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Spanner database API helper."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.iam import iam_util


# The list of pre-defined IAM roles in Spanner.
KNOWN_ROLES = [
    'roles/spanner.admin', 'roles/spanner.databaseAdmin',
    'roles/spanner.databaseReader', 'roles/spanner.databaseUser',
    'roles/spanner.viewer'
]


def Create(instance_ref, database, ddl):
  """Create a new database."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  req = msgs.SpannerProjectsInstancesDatabasesCreateRequest(
      parent=instance_ref.RelativeName(),
      createDatabaseRequest=msgs.CreateDatabaseRequest(
          createStatement='CREATE DATABASE `'+database+'`',
          extraStatements=ddl))
  return client.projects_instances_databases.Create(req)


def SetPolicy(database_ref, policy):
  """Saves the given policy on the database, overwriting whatever exists."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  policy.version = iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION
  req = msgs.SpannerProjectsInstancesDatabasesSetIamPolicyRequest(
      resource=database_ref.RelativeName(),
      setIamPolicyRequest=msgs.SetIamPolicyRequest(policy=policy))
  return client.projects_instances_databases.SetIamPolicy(req)


def Delete(database_ref):
  """Delete a database."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  req = msgs.SpannerProjectsInstancesDatabasesDropDatabaseRequest(
      database=database_ref.RelativeName())
  return client.projects_instances_databases.DropDatabase(req)


def GetIamPolicy(database_ref):
  """Gets the IAM policy on a database."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  req = msgs.SpannerProjectsInstancesDatabasesGetIamPolicyRequest(
      getIamPolicyRequest=msgs.GetIamPolicyRequest(
          options=msgs.GetPolicyOptions(
              requestedPolicyVersion=
              iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION)),
      resource=database_ref.RelativeName())
  return client.projects_instances_databases.GetIamPolicy(req)


def Get(database_ref):
  """Get a database by name."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  req = msgs.SpannerProjectsInstancesDatabasesGetRequest(
      name=database_ref.RelativeName())
  return client.projects_instances_databases.Get(req)


def GetDdl(database_ref):
  """Get a database's DDL description."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  req = msgs.SpannerProjectsInstancesDatabasesGetDdlRequest(
      database=database_ref.RelativeName())
  return client.projects_instances_databases.GetDdl(req).statements


def List(instance_ref):
  """List databases in the instance."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  req = msgs.SpannerProjectsInstancesDatabasesListRequest(
      parent=instance_ref.RelativeName())
  return list_pager.YieldFromList(
      client.projects_instances_databases,
      req,
      field='databases',
      batch_size_attribute='pageSize')


def UpdateDdl(database_ref, ddl):
  """Update a database via DDL commands."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  req = msgs.SpannerProjectsInstancesDatabasesUpdateDdlRequest(
      database=database_ref.RelativeName(),
      updateDatabaseDdlRequest=msgs.UpdateDatabaseDdlRequest(statements=ddl))
  return client.projects_instances_databases.UpdateDdl(req)


def Restore(database_ref, backup_ref):
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  req = msgs.SpannerProjectsInstancesDatabasesRestoreRequest(
      parent=database_ref.Parent().RelativeName(),
      restoreDatabaseRequest=msgs.RestoreDatabaseRequest(
          backup=backup_ref.RelativeName(),
          databaseId=database_ref.Name()))
  return client.projects_instances_databases.Restore(req)
