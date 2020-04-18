# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""services helper functions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py import list_pager
from googlecloudsdk.api_lib.services import exceptions
from googlecloudsdk.api_lib.util import apis_internal
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import http as http_creds

_PROJECT_RESOURCE = 'projects/%s'
_PROJECT_SERVICE_RESOURCE = 'projects/%s/services/%s'
_V1_VERSION = 'v1'
_V1BETA1_VERSION = 'v1beta1'
_V1ALPHA_VERSION = 'v1alpha'

# Map of services which should be protected from being disabled by
# prompting the user for  confirmation
_PROTECTED_SERVICES = {
    'anthos.googleapis.com': ('Warning: Disabling this service will '
                              'also automatically disable any running '
                              'Anthos clusters.')
}


def GetProtectedServiceWarning(service_name):
  """Return the warning message associated with a protected service."""
  return _PROTECTED_SERVICES.get(service_name)


def EnableApiCall(project, service):
  """Make API call to enable a specific service.

  Args:
    project: The project for which to enable the service.
    service: The identifier of the service to enable, for example
      'serviceusage.googleapis.com'.

  Raises:
    exceptions.EnableServicePermissionDeniedException: when enabling API fails.
    apitools_exceptions.HttpError: Another miscellaneous error with the service.

  Returns:
    The result of the operation
  """
  client = _GetClientInstance()
  messages = client.MESSAGES_MODULE

  # TODO(b/78464430): use resource argument.
  request = messages.ServiceusageServicesEnableRequest(
      name=_PROJECT_SERVICE_RESOURCE % (project, service))
  try:
    return client.services.Enable(request)
  except (apitools_exceptions.HttpForbiddenError,
          apitools_exceptions.HttpNotFoundError) as e:
    exceptions.ReraiseError(e,
                            exceptions.EnableServicePermissionDeniedException)


def BatchEnableApiCall(project, services):
  """Make API call to batch enable services.

  Args:
    project: The project for which to enable the services.
    services: Iterable of identifiers of services to enable.

  Raises:
    exceptions.EnableServicePermissionDeniedException: when enabling API fails.
    apitools_exceptions.HttpError: Another miscellaneous error with the service.

  Returns:
    The result of the operation
  """
  client = _GetClientInstance()
  messages = client.MESSAGES_MODULE

  request = messages.ServiceusageServicesBatchEnableRequest(
      batchEnableServicesRequest=messages.BatchEnableServicesRequest(
          serviceIds=services),
      parent=_PROJECT_RESOURCE % project)
  try:
    return client.services.BatchEnable(request)
  except (apitools_exceptions.HttpForbiddenError,
          apitools_exceptions.HttpNotFoundError) as e:
    exceptions.ReraiseError(e,
                            exceptions.EnableServicePermissionDeniedException)


def DisableApiCall(project, service, force=False):
  """Make API call to disable a specific service.

  Args:
    project: The project for which to enable the service.
    service: The identifier of the service to disable, for example
      'serviceusage.googleapis.com'.
    force: disable the service even if there are enabled services which depend
      on it. This also disables the services which depend on the service to be
      disabled.

  Raises:
    exceptions.EnableServicePermissionDeniedException: when disabling API fails.
    apitools_exceptions.HttpError: Another miscellaneous error with the service.

  Returns:
    The result of the operation
  """
  client = _GetClientInstance()
  messages = client.MESSAGES_MODULE

  request = messages.ServiceusageServicesDisableRequest(
      name=_PROJECT_SERVICE_RESOURCE % (project, service),
      disableServiceRequest=messages.DisableServiceRequest(
          disableDependentServices=force,),
  )
  try:
    return client.services.Disable(request)
  except (apitools_exceptions.HttpForbiddenError,
          apitools_exceptions.HttpNotFoundError) as e:
    exceptions.ReraiseError(e,
                            exceptions.EnableServicePermissionDeniedException)
  except apitools_exceptions.HttpBadRequestError as e:
    log.status.Print('Provide the --force flag if you wish to disable '
                     'dependent services.')
    exceptions.ReraiseError(e, exceptions.Error)


def GetService(project, service):
  """Get a service.

  Args:
    project: The project for which to get the service.
    service: The service to get.

  Raises:
    exceptions.GetServicePermissionDeniedException: when getting service fails.
    apitools_exceptions.HttpError: Another miscellaneous error with the service.

  Returns:
    The service configuration.
  """
  client = _GetClientInstance()
  messages = client.MESSAGES_MODULE

  request = messages.ServiceusageServicesGetRequest(
      name=_PROJECT_SERVICE_RESOURCE % (project, service))
  try:
    return client.services.Get(request)
  except (apitools_exceptions.HttpForbiddenError,
          apitools_exceptions.HttpNotFoundError) as e:
    exceptions.ReraiseError(e, exceptions.GetServicePermissionDeniedException)


def IsServiceEnabled(service):
  client = _GetClientInstance()
  messages = client.MESSAGES_MODULE
  return service.state == messages.GoogleApiServiceusageV1Service.StateValueValuesEnum.ENABLED


def ListServices(project, enabled, page_size, limit):
  """Make API call to list services.

  Args:
    project: The project for which to list services.
    enabled: List only enabled services.
    page_size: The page size to list.
    limit: The max number of services to display.

  Raises:
    exceptions.ListServicesPermissionDeniedException: when listing services
    fails.
    apitools_exceptions.HttpError: Another miscellaneous error with the service.

  Returns:
    The list of services
  """
  client = _GetClientInstance()
  messages = client.MESSAGES_MODULE

  if enabled:
    service_filter = 'state:ENABLED'
  else:
    service_filter = None
  request = messages.ServiceusageServicesListRequest(
      filter=service_filter, parent=_PROJECT_RESOURCE % project)
  try:
    return list_pager.YieldFromList(
        client.services,
        request,
        limit=limit,
        batch_size_attribute='pageSize',
        batch_size=page_size,
        field='services')
  except (apitools_exceptions.HttpForbiddenError,
          apitools_exceptions.HttpNotFoundError) as e:
    exceptions.ReraiseError(e,
                            exceptions.EnableServicePermissionDeniedException)


def GetOperation(name):
  """Make API call to get an operation.

  Args:
    name: The name of operation.

  Raises:
    exceptions.OperationErrorException: when the getting operation API fails.
    apitools_exceptions.HttpError: Another miscellaneous error with the service.

  Returns:
    The result of the operation
  """
  client = _GetClientInstance()
  messages = client.MESSAGES_MODULE
  request = messages.ServiceusageOperationsGetRequest(name=name)
  try:
    return client.operations.Get(request)
  except (apitools_exceptions.HttpForbiddenError,
          apitools_exceptions.HttpNotFoundError) as e:
    exceptions.ReraiseError(e, exceptions.OperationErrorException)


def GenerateServiceIdentity(project, service):
  """Generate a service identity.

  Args:
    project: The project to generate a service identity for.
    service: The service to generate a service identity for.

  Raises:
    exceptions.GenerateServiceIdentityPermissionDeniedException: when generating
    service identity fails.
    apitools_exceptions.HttpError: Another miscellaneous error with the service.

  Returns:
    The email and uid of the generated service identity.
  """
  client = _GetClientInstance(version=_V1BETA1_VERSION)
  messages = client.MESSAGES_MODULE

  request = messages.ServiceusageServicesGenerateServiceIdentityRequest(
      parent=_PROJECT_SERVICE_RESOURCE % (project, service))
  try:
    op = client.services.GenerateServiceIdentity(request)
    return _GetOperationResponseProperty(
        op, 'email'), _GetOperationResponseProperty(op, 'unique_id')
  except (apitools_exceptions.HttpForbiddenError,
          apitools_exceptions.HttpNotFoundError) as e:
    exceptions.ReraiseError(
        e, exceptions.GenerateServiceIdentityPermissionDeniedException)


def _GetOperationResponseProperty(op, key):
  return next((p.value.string_value
               for p in op.response.additionalProperties
               if p.key == key), None)


def _GetClientInstance(version='v1'):
  """Get a client instance for service usage."""
  # pylint:disable=protected-access
  # Specifically disable resource quota in all cases for service management.
  # We need to use this API to turn on APIs and sometimes the user doesn't have
  # this API turned on. We should always use the shared project to do this
  # so we can bootstrap users getting the appropriate APIs enabled. If the user
  # has explicitly set the quota project, then respect that.
  enable_resource_quota = (
      properties.VALUES.billing.quota_project.IsExplicitlySet())
  http_client = http_creds.Http(
      response_encoding=http_creds.ENCODING,
      enable_resource_quota=enable_resource_quota)
  return apis_internal._GetClientInstance(
      'serviceusage', version, http_client=http_client)
