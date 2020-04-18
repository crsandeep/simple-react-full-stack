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
"""Utilities for Cloud Workflows API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from apitools.base.py import encoding
from apitools.base.py import exceptions as api_exceptions
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.workflows import flags
from googlecloudsdk.core import resources

import six


def GetClientInstance(no_http=False):
  """Returns the default client instance for Workflows API."""
  return apis.GetClientInstance('workflows', 'v1alpha1', no_http=no_http)


def GetMessagesModule(client=None):
  """Returns the messages module for the given client."""
  client = client or GetClientInstance()
  return client.MESSAGES_MODULE


class WorkflowsClient(object):
  """Client for Workflows service in the Cloud Workflows API."""

  def __init__(self, client=None, messages=None):
    self.client = client or GetClientInstance()
    self.messages = messages or GetMessagesModule(client)
    self._service = self.client.projects_locations_workflows

  def Get(self, workflow_ref):
    """Gets a Workflow.

    Args:
      workflow_ref: Resource reference to the Workflow to get.

    Returns:
      Workflow: The workflow if it exists, None otherwise.
    """
    get_req = self.messages.WorkflowsProjectsLocationsWorkflowsGetRequest(
        name=workflow_ref.RelativeName())
    try:
      return self._service.Get(get_req)
    except api_exceptions.HttpNotFoundError:
      return None

  def Create(self, workflow_ref, workflow):
    """Creates a Workflow.

    Args:
      workflow_ref: Resource reference to the Workflow to create.
      workflow: Workflow resource message to create.

    Returns:
      Long-running operation for create.
    """
    create_req = self.messages.WorkflowsProjectsLocationsWorkflowsCreateRequest(
        parent=workflow_ref.Parent().RelativeName(),
        workflow=workflow,
        workflowId=workflow_ref.Name())
    return self._service.Create(create_req)

  def Patch(self, workflow_ref, workflow, updated_fields):
    """Updates a Workflow.

    If updated fields are specified it uses patch semantics.

    Args:
      workflow_ref: Resource reference to the Workflow to update.
      workflow: Workflow resource message to update.
      updated_fields: List of the updated fields used in a patch request.

    Returns:
      Long-running operation for update.
    """
    update_mask = ','.join(sorted(updated_fields))
    patch_req = self.messages.WorkflowsProjectsLocationsWorkflowsPatchRequest(
        name=workflow_ref.RelativeName(),
        updateMask=update_mask,
        workflow=workflow)
    return self._service.Patch(patch_req)

  def BuildWorkflowFromArgs(self, args):
    """Create a workflow from command-line arguments."""
    workflow = self.messages.Workflow()
    updated_fields = []
    flags.SetSource(args, workflow, updated_fields)
    flags.SetDescription(args, workflow, updated_fields)
    flags.SetServiceAccount(args, workflow, updated_fields)
    labels = labels_util.ParseCreateArgs(args,
                                         self.messages.Workflow.LabelsValue)
    flags.SetLabels(labels, workflow, updated_fields)
    return workflow, updated_fields

  def WaitForOperation(self, operation, workflow_ref):
    """Waits until the given long-running operation is complete."""
    operation_ref = resources.REGISTRY.Parse(
        operation.name, collection='workflows.projects.locations.operations')
    operations = OperationsClient()
    poller = _OperationPoller(
        workflows=self, operations=operations, workflow_ref=workflow_ref)
    progress_string = 'Waiting for operation [{}] to complete'.format(
        operation_ref.Name())
    return waiter.WaitFor(poller, operation_ref, progress_string)


class OperationsClient(object):
  """Client for Operations service in the Cloud Workflows API."""

  def __init__(self, client=None, messages=None):
    self.client = client or GetClientInstance()
    self.messages = messages or GetMessagesModule(client)
    self._service = self.client.projects_locations_operations

  def Get(self, operation_ref):
    """Gets an Operation.

    Args:
      operation_ref: Resource reference to the Operation to get.

    Returns:
      Operation: The operation if it exists, None otherwise.
    """
    get_req = self.messages.WorkflowsProjectsLocationsOperationsGetRequest(
        name=operation_ref.RelativeName())
    try:
      return self._service.Get(get_req)
    except api_exceptions.HttpNotFoundError:
      return None


class _OperationPoller(waiter.OperationPoller):
  """Implementation of OperationPoller for Workflows Operations."""

  def __init__(self, workflows, operations, workflow_ref):
    """Creates the poller.

    Args:
      workflows: the Workflows API client used to get the resource after
        operation is complete.
      operations: the Operations API client used to poll for the operation.
      workflow_ref: a reference to a workflow that is the subject of this
        operation.
    """
    self.workflows = workflows
    self.operations = operations
    self.workflow_ref = workflow_ref

  def IsDone(self, operation):
    """Overrides."""
    if operation.done:
      if operation.error:
        raise waiter.OperationError(_SerializeError(operation.error))
      return True
    return False

  def Poll(self, operation_ref):
    """Overrides."""
    return self.operations.Get(operation_ref)

  def GetResult(self, operation):
    """Overrides."""
    return self.workflows.Get(self.workflow_ref)


def _SerializeError(error):
  """Serializes the error message for better format."""
  if isinstance(error, six.string_types):
    return error
  try:
    return json.dumps(
        encoding.MessageToDict(error),
        indent=2,
        sort_keys=True,
        separators=(',', ': '))
  except Exception:  # pylint: disable=broad-except
    # try the best, fall back to return error
    return error
