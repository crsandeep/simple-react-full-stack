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
"""Base classes for [enable|disable|describe] commands for Feature resource."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from apitools.base.py import encoding
from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.api_lib.util import exceptions as core_api_exceptions
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


class EnableCommand(base.CreateCommand):
  """Base class for the command that enables a Feature."""

  def RunCommand(self, args, **kwargs):
    try:
      project = properties.VALUES.core.project.GetOrFail()
      return CreateFeature(project, self.FEATURE_NAME,
                           self.FEATURE_DISPLAY_NAME, **kwargs)
    except apitools_exceptions.HttpUnauthorizedError as e:
      raise exceptions.Error(
          'You are not authorized to enable {} Feature from project [{}]. '
          'Underlying error: {}'.format(self.FEATURE_DISPLAY_NAME, project, e))
    except properties.RequiredPropertyError as e:
      raise exceptions.Error('Failed to retrieve the project ID.')
    except apitools_exceptions.HttpConflictError as e:
      # If the error is not due to the object already existing, re-raise.
      error = core_api_exceptions.HttpErrorPayload(e)
      if error.status_description != 'ALREADY_EXISTS':
        raise
      else:
        log.status.Print(
            '{} Feature for project [{}] is already enabled'.format(
                self.FEATURE_DISPLAY_NAME, project))
    except apitools_exceptions.HttpBadRequestError as e:
      error = core_api_exceptions.HttpErrorPayload(e)
      if error.status_description != 'FAILED_PRECONDITION':
        raise
      else:
        log.status.Print(error.status_message)


class DisableCommand(base.DeleteCommand):
  """Base class for the command that disables a Feature."""

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        '--force',
        action='store_true',
        help='Completely disable this feature, even if it is currently in use. '
        'Force disablement may result in unexpected behavior.')

  def RunCommand(self, args):
    try:
      project_id = properties.VALUES.core.project.GetOrFail()
      name = 'projects/{0}/locations/global/features/{1}'.format(
          project_id, self.FEATURE_NAME)
      DeleteFeature(name, self.FEATURE_DISPLAY_NAME, force=args.force)
    except apitools_exceptions.HttpUnauthorizedError as e:
      raise exceptions.Error(
          'You are not authorized to disable {} Feature from project [{}]. '
          'Underlying error: {}'.format(self.FEATURE_DISPLAY_NAME, project_id,
                                        e))
    except properties.RequiredPropertyError as e:
      raise exceptions.Error('Failed to retrieve the project ID.')


class DescribeCommand(base.DescribeCommand):
  """Base class for the command that describes the status of a Feature."""

  def RunCommand(self, args):
    try:
      project_id = properties.VALUES.core.project.GetOrFail()
      name = 'projects/{0}/locations/global/features/{1}'.format(
          project_id, self.FEATURE_NAME)
      return GetFeature(name)
    except apitools_exceptions.HttpUnauthorizedError as e:
      raise exceptions.Error(
          'You are not authorized to see the status of {} '
          'Feature from project [{}]. Underlying error: {}'.format(
              self.FEATURE_DISPLAY_NAME, project_id, e))


class UpdateCommand(base.UpdateCommand):
  """Base class for the command that updates a Feature."""

  def RunCommand(self, mask, **kwargs):
    try:
      project = properties.VALUES.core.project.GetOrFail()
      return UpdateFeature(project, self.FEATURE_NAME,
                           self.FEATURE_DISPLAY_NAME, mask, **kwargs)
    except apitools_exceptions.HttpUnauthorizedError as e:
      raise exceptions.Error(
          'You are not authorized to update {} Feature from project [{}]. '
          'Underlying error: {}'.format(self.FEATURE_DISPLAY_NAME, project, e))
    except properties.RequiredPropertyError as e:
      raise exceptions.Error('Failed to retrieve the project ID.')


def CreateMultiClusterIngressFeatureSpec(config_membership):
  client = core_apis.GetClientInstance('gkehub', 'v1alpha1')
  messages = client.MESSAGES_MODULE
  return messages.MultiClusterIngressFeatureSpec(
      configMembership=config_membership)


def CreateMultiClusterServiceDiscoveryFeatureSpec():
  client = core_apis.GetClientInstance('gkehub', 'v1alpha1')
  messages = client.MESSAGES_MODULE
  return messages.MultiClusterServiceDiscoveryFeatureSpec()


def CreateConfigManagementFeatureSpec():
  client = core_apis.GetClientInstance('gkehub', 'v1alpha1')
  messages = client.MESSAGES_MODULE
  empty_config_map = messages.ConfigManagementFeatureSpec.MembershipConfigsValue(
      additionalProperties=[])
  return messages.ConfigManagementFeatureSpec(
      membershipConfigs=empty_config_map)


def CreateFeature(project, feature_id, feature_display_name, **kwargs):
  """Creates a Feature resource in Hub.

  Args:
    project: the project in which to create the Feature
    feature_id: the value to use for the feature_id
    feature_display_name: the FEATURE_DISPLAY_NAME of this Feature
    **kwargs: arguments for Feature object. For eg, multiclusterFeatureSpec

  Returns:
    the created Feature resource.

  Raises:
    - apitools.base.py.HttpError: if the request returns an HTTP error
    - exceptions raised by waiter.WaitFor()
  """
  client = core_apis.GetClientInstance('gkehub', 'v1alpha1')
  messages = client.MESSAGES_MODULE
  request = messages.GkehubProjectsLocationsGlobalFeaturesCreateRequest(
      feature=messages.Feature(**kwargs),
      parent='projects/{}/locations/global'.format(project),
      featureId=feature_id,
  )

  op = client.projects_locations_global_features.Create(request)
  op_resource = resources.REGISTRY.ParseRelativeName(
      op.name, collection='gkehub.projects.locations.operations')
  result = waiter.WaitFor(
      waiter.CloudOperationPoller(client.projects_locations_global_features,
                                  client.projects_locations_operations),
      op_resource,
      'Waiting for Feature {} to be created'.format(feature_display_name))

  # This allows us pass warning messages returned from OnePlatform backends.
  request_type = client.projects_locations_operations.GetRequestType('Get')
  op = client.projects_locations_operations.Get(
      request_type(name=op_resource.RelativeName()))
  metadata_dict = encoding.MessageToPyValue(op.metadata)
  if 'statusDetail' in metadata_dict:
    log.warning(metadata_dict['statusDetail'])

  return result


def GetFeature(name):
  """Gets a Feature resource from Hub.

  Args:
    name: the full resource name of the Feature to get, e.g.,
      projects/foo/locations/global/features/name.

  Returns:
    a Feature resource

  Raises:
    apitools.base.py.HttpError: if the request returns an HTTP error
  """

  client = core_apis.GetClientInstance('gkehub', 'v1alpha1')
  return client.projects_locations_global_features.Get(
      client.MESSAGES_MODULE.GkehubProjectsLocationsGlobalFeaturesGetRequest(
          name=name))


def DeleteFeature(name, feature_display_name, force=False):
  """Deletes a Feature resource in Hub.

  Args:
    name: the full resource name of the Feature to delete, e.g.,
      projects/foo/locations/global/features/name.
    feature_display_name: the FEATURE_DISPLAY_NAME of this Feature
    force: flag to trigger force deletion of the Feature.

  Raises:
    apitools.base.py.HttpError: if the request returns an HTTP error
  """

  client = core_apis.GetClientInstance('gkehub', 'v1alpha1')
  op = client.projects_locations_global_features.Delete(
      client.MESSAGES_MODULE.GkehubProjectsLocationsGlobalFeaturesDeleteRequest(
          name=name, force=force))
  op_resource = resources.REGISTRY.ParseRelativeName(
      op.name, collection='gkehub.projects.locations.operations')
  waiter.WaitFor(
      waiter.CloudOperationPollerNoResources(
          client.projects_locations_operations), op_resource,
      'Waiting for Feature {} to be deleted'.format(feature_display_name))


def UpdateFeature(project, feature_id, feature_display_name, mask, **kwargs):
  """Updates a Feature resource in Hub.

  Args:
    project: the project in which to update the Feature
    feature_id: the value to use for the feature_id
    feature_display_name: the FEATURE_DISPLAY_NAME of this Feature
    mask: resource fields to be updated. For eg. multiclusterFeatureSpec
    **kwargs: arguments for Feature object. For eg, multiclusterFeatureSpec

  Returns:
    the updated Feature resource.

  Raises:
    - apitools.base.py.HttpError: if the request returns an HTTP error
    - exceptions raised by waiter.WaitFor()
  """
  client = core_apis.GetClientInstance('gkehub', 'v1alpha1')
  messages = client.MESSAGES_MODULE
  request = messages.GkehubProjectsLocationsGlobalFeaturesPatchRequest(
      name='projects/{0}/locations/global/features/{1}'.format(project,
                                                               feature_id),
      updateMask=mask,
      feature=messages.Feature(**kwargs),
  )
  try:
    op = client.projects_locations_global_features.Patch(request)
  except apitools_exceptions.HttpUnauthorizedError as e:
    raise exceptions.Error(
        'You are not authorized to see the status of {} '
        'feature from project [{}]. Underlying error: {}'.format(
            feature_display_name, project, e))
  except apitools_exceptions.HttpNotFoundError as e:
    raise exceptions.Error(
        '{} Feature for project [{}] is not enabled'.format(
            feature_display_name, project))
  op_resource = resources.REGISTRY.ParseRelativeName(
      op.name, collection='gkehub.projects.locations.operations')
  result = waiter.WaitFor(
      waiter.CloudOperationPoller(client.projects_locations_global_features,
                                  client.projects_locations_operations),
      op_resource,
      'Waiting for Feature {} to be updated'.format(feature_display_name))

  return result


def ListMemberships(project):
  """Lists Membership IDs in Hub.

  Args:
    project: the project in which Membership resources exist.

  Returns:
    a list of Membership resource IDs in Hub.

  Raises:
    apitools.base.py.HttpError: if the request returns an HTTP error
  """
  parent = 'projects/{}/locations/global'.format(project)
  client = core_apis.GetClientInstance('gkehub', 'v1beta1')
  response = client.projects_locations_memberships.List(
      client.MESSAGES_MODULE.GkehubProjectsLocationsMembershipsListRequest(
          parent=parent))

  return [
      os.path.basename(membership.name) for membership in response.resources
  ]
