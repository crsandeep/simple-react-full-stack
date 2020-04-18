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
"""API client library for Cloud IAM Simulator Replay Operations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.core import resources

_MAX_WAIT_TIME_MS = 60 * 60 * 1000  # 60 minutes.


class Client(object):
  """API client for Cloud IAM Simulator Replay Operations."""

  def __init__(self, client, messages=None):
    self._client = client
    self._service = self._client.operations
    self._messages = messages or client.MESSAGES_MODULE

  @classmethod
  def FromApiVersion(cls, version):
    return cls(apis.GetClientInstance('iamassist', version))

  def Get(self, operation_ref):
    request = self._messages.IamassistOperationsGetRequest(
        name=operation_ref.RelativeName())
    return self._service.Get(request)

  def List(self, parent_ref, limit=None, page_size=None, list_filter=None):
    request = self._messages.IamassistReplaysListRequest(
        name=parent_ref.RelativeName(), filter=list_filter)
    return list_pager.YieldFromList(
        self._service,
        request,
        batch_size=page_size,
        limit=limit,
        field='operations',
        batch_size_attribute='pageSize')

  def WaitForOperation(self, operation, message):
    registry = resources.REGISTRY.Clone()
    registry.RegisterApiByName('iamassist', 'v1alpha3')
    operation_ref = registry.Parse(
        operation.name, collection='iamassist.operations')
    poller = waiter.CloudOperationPollerNoResources(self._service)
    return waiter.WaitFor(
        poller,
        operation_ref,
        message,
        wait_ceiling_ms=_MAX_WAIT_TIME_MS)
