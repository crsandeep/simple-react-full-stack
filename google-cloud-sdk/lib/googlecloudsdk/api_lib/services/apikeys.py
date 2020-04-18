# -*- coding: utf-8 -*- #
# Copyright 2020 Google Inc. All Rights Reserved.
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
"""API Keys API helper functions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py import list_pager
from googlecloudsdk.api_lib.services import exceptions
from googlecloudsdk.api_lib.util import apis as core_apis

_PROJECT_RESOURCE = 'projects/%s'


def ListKeys(project, deleted=None, page_size=None, limit=None):
  """List API Keys for a given project.

  Args:
    project: The project for which to list keys.
    deleted: List deleted keys.
    page_size: The page size to list.
    limit: The max number of metrics to return.

  Raises:
    exceptions.PermissionDeniedException: when listing keys fails.

  Returns:
    The list of keys
  """
  client = GetClientInstance()
  messages = client.MESSAGES_MODULE

  if deleted:
    key_filter = 'state:DELETED'
  else:
    key_filter = None
  request = messages.ApikeysProjectsKeysListRequest(
      parent=GetParentResourceName(project), filter=key_filter)
  return list_pager.YieldFromList(
      client.projects_keys,
      request,
      limit=limit,
      batch_size_attribute='pageSize',
      batch_size=page_size,
      field='keys')


def GetClientInstance():
  return core_apis.GetClientInstance('apikeys', 'v2alpha1')


def GetOperation(name):
  """Make API call to get an operation.

  Args:
    name: The name of the operation.

  Raises:
    exceptions.OperationErrorException: when the getting operation API fails.
    apitools_exceptions.HttpError: Another miscellaneous error with the service.

  Returns:
    The result of the operation
  """
  client = GetClientInstance()
  messages = client.MESSAGES_MODULE
  request = messages.ApikeysOperationsGetRequest(name=name)
  try:
    return client.operations.Get(request)
  except (apitools_exceptions.HttpForbiddenError,
          apitools_exceptions.HttpNotFoundError) as e:
    exceptions.ReraiseError(e, exceptions.OperationErrorException)


def GetAllowedAndroidApplications(args, messages):
  """Create list of allowed android applications."""
  allowed_applications = []
  for application in getattr(args, 'allowed_application', []) or []:
    android_application = messages.V2alpha1AndroidApplication(
        sha1Fingerprint=application['sha1_fingerprint'],
        packageName=application['package_name'])
    allowed_applications.append(android_application)
  return allowed_applications


def GetApiTargets(args, messages):
  """Create list of target apis."""
  api_targets = []
  for api_target in getattr(args, 'api_target', []) or []:
    api_targets.append(
        messages.V2alpha1ApiTarget(
            service=api_target.get('service'),
            methods=api_target.get('methods', [])))
  return api_targets


def GetParentResourceName(project):
  return _PROJECT_RESOURCE % (project)
