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
"""Utilities for waiting on Compute Engine operations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.compute import batch_helper
from googlecloudsdk.api_lib.compute import path_simplifier
from googlecloudsdk.api_lib.util import exceptions as http_exceptions
from googlecloudsdk.command_lib.util import time_util
from googlecloudsdk.core import log

_POLLING_TIMEOUT_SEC = 60 * 30
_MAX_TIME_BETWEEN_POLLS_SEC = 5

# The set of possible operation types is {insert, delete, update,
# *.insert, *.delete, *.update} + all verbs. For example,
#
#        verb                    op type
#   Instances.setMedata        setMetdata
#   Instances.insert           insert
#   InsetanceTempalte.delete   compute.instanceTemplates.delete
# In our status reporting, we use the following
# mapping. Anything not in the map is reported as "Updated".
_HUMAN_FRIENDLY_OPERATION_TYPE_SUFFIXES = {
    'createSnapshot': {
        'past': 'created',
        'present': 'create'
    },
    'recreateInstancesInstanceGroupManager': {
        'past': 'recreated',
        'present': 'recreate'
    },
    'createFirewallSecurityPolicy': {
        'past': 'created',
        'present': 'create'
    },
    'deleteFirewallSecurityPolicy': {
        'past': 'deleted',
        'present': 'delete'
    },
    'insert': {
        'past': 'created',
        'present': 'create'
    },
    'delete': {
        'past': 'deleted',
        'present': 'delete'
    },
    'update': {
        'past': 'updated',
        'present': 'update'
    },
    'invalidateCache': {
        'past': 'completed invalidation for',
        'present': 'complete invalidation for'
    }
}


def _HumanFriendlyNamesForOp(op_type):
  for s in _HUMAN_FRIENDLY_OPERATION_TYPE_SUFFIXES:
    if op_type.endswith(s):
      return _HUMAN_FRIENDLY_OPERATION_TYPE_SUFFIXES.get(s)

  return {'past': 'updated', 'present': 'update'}


def _HumanFriendlyNameForOpPastTense(op_type):
  return _HumanFriendlyNamesForOp(op_type)['past']


def _HumanFriendlyNameForOpPresentTense(op_type):
  return _HumanFriendlyNamesForOp(op_type)['present']


def _IsDeleteOp(op_type):
  return _HumanFriendlyNameForOpPastTense(op_type) == 'deleted'


def _RecordProblems(operation, warnings, errors):
  """Records any warnings and errors into the given lists."""
  for warning in operation.warnings or []:
    warnings.append(warning.message)
  if operation.error:
    for error in operation.error.errors or []:
      errors.append((operation.httpErrorStatusCode, error.message))


def _RecordUnfinishedOperations(operations, errors):
  """Adds error messages stating that the given operations timed out."""
  pending_resources = [operation.targetLink for operation in operations]
  errors.append(
      (None, ('Did not {action} the following resources within '
              '{timeout}s: {links}. These operations may still be '
              'underway remotely and may still succeed; use gcloud list '
              'and describe commands or '
              'https://console.developers.google.com/ to '
              'check resource state').format(
                  action=_HumanFriendlyNameForOpPresentTense(
                      operations[0].operationType),
                  timeout=_POLLING_TIMEOUT_SEC,
                  links=', '.join(pending_resources))))


class OperationData(object):
  """Holds all information necessary to poll given operation.

  Attributes:
    operation: An Operation object to poll.
    operation_service: The service that can be used to get operation
      object.
    resource_service: The service of the collection being mutated by
      the operation. If the operation type is not delete, this service
      is used to fetch the mutated object after the operation is done.
    project: str, The project to which the resource belong.
    followup_override: str, Overrides the target resource name when
      it is different from the resource name which is used to poll.
    errors: An output parameter for capturing errors.
    warnings: An output parameter for capturing warnings.
  """

  def __init__(self,
               operation,
               operation_service,
               resource_service,
               project=None,
               followup_override=None):
    self.operation = operation
    self.operation_service = operation_service
    self.resource_service = resource_service
    self.project = project
    self.followup_override = followup_override

    self.errors = []
    self.warnings = []

  def __eq__(self, o):
    if not isinstance(o, OperationData):
      return False
    return (self.operation == o.operation and self.project == o.project and
            self.operation_service == o.operation_service and
            self.resource_service == o.resource_service and
            self.followup_override == o.followup_override)

  def __hash__(self):
    return (hash(self.operation.selfLink) ^ hash(self.project)
            ^ hash(self.operation_service) ^ hash(self.resource_service)
            ^ hash(self.followup_override))

  def __ne__(self, o):
    return not self == o

  def SetOperation(self, operation):
    """"Updates the operation.

    Args:
      operation: Operation to be assigned.
    """
    self.operation = operation

  def IsGlobalOrganizationOperation(self):
    if not hasattr(self.operation_service.client,
                   'globalOrganizationOperations'):
      return False
    return (self.operation_service ==
            self.operation_service.client.globalOrganizationOperations)

  def IsDone(self):
    """Returns true if the operation is done."""
    operation_type = self.operation_service.GetResponseType('Get')
    done = operation_type.StatusValueValuesEnum.DONE
    return self.operation.status == done

  def _SupportOperationWait(self):
    return 'Wait' in self.operation_service.GetMethodsList()

  def ResourceGetRequest(self):
    """"Generates apitools request message to get the resource."""

    target_link = self.operation.targetLink

    if self.project:
      request = self.resource_service.GetRequestType('Get')(
          project=self.project)
    else:
      # Gets the flexible resource ID.
      if target_link is None:
        log.status.write('{0}.\n'.format(
            _HumanFriendlyNameForOpPastTense(
                self.operation.operationType).capitalize()))
        return
      token_list = target_link.split('/')
      flexible_resource_id = token_list[-1]
      request = self.resource_service.GetRequestType('Get')(
          securityPolicy=flexible_resource_id)
    if self.operation.zone:
      request.zone = path_simplifier.Name(self.operation.zone)
    elif self.operation.region:
      request.region = path_simplifier.Name(self.operation.region)
    name_field = self.resource_service.GetMethodConfig('Get').ordered_params[-1]

    resource_name = self.followup_override or path_simplifier.Name(
        self.operation.targetLink)

    setattr(request, name_field, resource_name)
    return request

  def _OperationRequest(self, verb):
    """Generates apitools request message to poll the operation."""

    if self.project:
      request = self.operation_service.GetRequestType(verb)(
          operation=self.operation.name, project=self.project)
    else:
      # Fetches the parent ID from the operation name.
      token_list = self.operation.name.split('-')
      parent_id = 'organizations/' + token_list[1]
      request = self.operation_service.GetRequestType(verb)(
          operation=self.operation.name, parentId=parent_id)
    if self.operation.zone:
      request.zone = path_simplifier.Name(self.operation.zone)
    elif self.operation.region:
      request.region = path_simplifier.Name(self.operation.region)
    return request

  def OperationGetRequest(self):
    """Generates apitools request message for operations.get method."""
    return self._OperationRequest('Get')

  def OperationWaitRequest(self):
    """Generates apitools request message for operations.wait method."""
    return self._OperationRequest('Wait')

  def _CallService(self, method, request):
    try:
      return method(request)
    except apitools_exceptions.HttpError as e:
      http_err = http_exceptions.HttpException(e)
      self.errors.append((http_err.error.status_code, http_err.message))
      _RecordProblems(self.operation, self.warnings, self.errors)
      raise

  def _PollUntilDoneUsingOperationGet(self, timeout_sec=_POLLING_TIMEOUT_SEC):
    """Polls the operation with operation Get method."""
    get_request = self.OperationGetRequest()
    start = time_util.CurrentTimeSec()
    poll_time_interval = 0
    max_poll_interval = 5  # 5 seconds

    while True:
      if time_util.CurrentTimeSec() - start > timeout_sec:
        self.errors.append(
            (None, 'operation {} timed out'.format(self.operation.name)))
        _RecordProblems(self.operation, self.warnings, self.errors)
        return

      try:
        self.operation = self._CallService(self.operation_service.Get,
                                           get_request)
      except apitools_exceptions.HttpError:
        return

      if self.IsDone():
        _RecordProblems(self.operation, self.warnings, self.errors)
        return
      poll_time_interval = min(poll_time_interval + 1, max_poll_interval)
      time_util.Sleep(poll_time_interval)

  def _PollUntilDoneUsingOperationWait(self, timeout_sec=_POLLING_TIMEOUT_SEC):
    """Polls the operation with operation method."""
    wait_request = self.OperationWaitRequest()
    start = time_util.CurrentTimeSec()

    while not self.IsDone():
      if time_util.CurrentTimeSec() - start > timeout_sec:
        self.errors.append(
            (None, 'operation {} timed out'.format(self.operation.name)))
        _RecordProblems(self.operation, self.warnings, self.errors)
        return
      try:
        self.operation = self._CallService(self.operation_service.Wait,
                                           wait_request)
      except apitools_exceptions.HttpError:
        return

    _RecordProblems(self.operation, self.warnings, self.errors)

  def PollUntilDone(self, timeout_sec=_POLLING_TIMEOUT_SEC):
    """Polls the operation until it is done."""
    if self.IsDone():
      return

    if self._SupportOperationWait():
      self._PollUntilDoneUsingOperationWait(timeout_sec)
    else:
      self._PollUntilDoneUsingOperationGet(timeout_sec)

  def GetResult(self, timeout_sec=_POLLING_TIMEOUT_SEC):
    """Get the resource which is touched by the operation."""
    self.PollUntilDone(timeout_sec)
    if not self.operation.error and not _IsDeleteOp(
        self.operation.operationType):
      resource_get_request = self.ResourceGetRequest()
      try:
        return self._CallService(self.resource_service.Get,
                                 resource_get_request)
      except apitools_exceptions.HttpError:
        pass


def WaitForOperations(
    operations_data, http, batch_url, warnings, errors,
    progress_tracker=None, timeout=None, log_result=True):
  """Blocks until the given operations are done or until a timeout is reached.

  Args:
    operations_data: A list of OperationData objects holding Operations to poll.
    http: An HTTP object.
    batch_url: The URL to which batch requests should be sent.
    warnings: An output parameter for capturing warnings.
    errors: An output parameter for capturing errors.
    progress_tracker: progress tracker to tick while waiting for operations to
                      finish.
    timeout: The maximum amount of time, in seconds, to wait for the
      operations to reach the DONE state.
    log_result: Whether the Operation Waiter should print the result in past
      tense of each request.

  Yields:
    The resources pointed to by the operations' targetLink fields if
    the operation type is not delete. Only resources whose
    corresponding operations reach done are yielded.
  """
  if not operations_data:
    return
  timeout = timeout or _POLLING_TIMEOUT_SEC

  # Operation -> OperationData mapping will be used to reify operation_service
  # and resource_service from operation_service.Get(operation) response.
  # It is necessary because poll operation is returning only response, but we
  # also need to get operation details to know the service to poll for all
  # unprocessed_operations.
  operation_details = {}
  unprocessed_operations = []
  for operation in operations_data:
    operation_details[operation.operation.selfLink] = operation
    unprocessed_operations.append(operation.operation)

  start = time_util.CurrentTimeSec()
  sleep_sec = 0
  # There is only one type of operation in compute API.
  # We pick the type of the first operation in the list.
  operation_type = operations_data[0].operation_service.GetResponseType('Get')

  while unprocessed_operations:
    if progress_tracker:
      progress_tracker.Tick()
    resource_requests = []
    operation_requests = []

    log.debug('Operations to inspect: %s', unprocessed_operations)
    for operation in unprocessed_operations:
      # Reify operation
      data = operation_details[operation.selfLink]
      # Need to update the operation since old operation may not have all the
      # required information.
      data.SetOperation(operation)

      operation_service = data.operation_service
      resource_service = data.resource_service

      if operation.status == operation_type.StatusValueValuesEnum.DONE:
        # The operation has reached the DONE state, so we record any
        # problems it contains (if any) and proceed to get the target
        # resource if there were no problems and the operation is not
        # a deletion.
        _RecordProblems(operation, warnings, errors)

        # We shouldn't attempt to get the target resource if there was
        # anything wrong with the operation. Note that
        # httpErrorStatusCode is set only when the operation is not
        # successful.
        if (operation.httpErrorStatusCode and
            operation.httpErrorStatusCode != 200):  # httplib.OK
          continue

        # Just in case the server did not set httpErrorStatusCode but
        # the operation did fail, we check the "error" field.
        if operation.error:
          continue

        # We shouldn't get the target resource if the operation type
        # is delete because there will be no resource left.
        if not _IsDeleteOp(operation.operationType):
          request = data.ResourceGetRequest()
          # Some operations do not have target and should not send get request.
          if request:
            resource_requests.append((resource_service, 'Get', request))

        # Only log when there is target link in the operation.
        if operation.targetLink and log_result:
          log.status.write('{0} [{1}].\n'.format(
              _HumanFriendlyNameForOpPastTense(
                  operation.operationType).capitalize(), operation.targetLink))

      else:
        # The operation has not reached the DONE state, so we add a request
        # to poll the operation.
        # TODO(b/129413862): Global org operation service supports wait API.
        if data.IsGlobalOrganizationOperation():
          request = data.OperationGetRequest()
          operation_requests.append((operation_service, 'Get', request))
        else:
          request = data.OperationWaitRequest()
          operation_requests.append((operation_service, 'Wait', request))

    requests = resource_requests + operation_requests
    if not requests:
      break

    responses, request_errors = batch_helper.MakeRequests(
        requests=requests,
        http=http,
        batch_url=batch_url)

    errors.extend(request_errors)

    all_done = True
    unprocessed_operations = []
    for response in responses:
      if isinstance(response, operation_type):
        unprocessed_operations.append(response)
        if response.status != operation_type.StatusValueValuesEnum.DONE:
          all_done = False
      else:
        yield response

    # If there are no more operations, we are done.
    if not unprocessed_operations:
      break

    # If all of the operations are done, we should ignore the timeout and ignore
    # the sleep.
    if all_done:
      continue

    # Did we time out? If so, record the operations that timed out so
    # they can be reported to the user.
    if time_util.CurrentTimeSec() - start > timeout:
      log.debug('Timeout of %ss reached.', timeout)
      _RecordUnfinishedOperations(unprocessed_operations, errors)
      break

    # Sleeps before trying to poll the operations again.
    sleep_sec = min(sleep_sec + 1, _MAX_TIME_BETWEEN_POLLS_SEC)
    log.debug('Sleeping for %ss.', sleep_sec)
    time_util.Sleep(sleep_sec)
