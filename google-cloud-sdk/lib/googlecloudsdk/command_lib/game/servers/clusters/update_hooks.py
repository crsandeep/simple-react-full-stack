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
"""Update hooks for Cloud Game Servers Cluster."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.game.servers import hooks
from googlecloudsdk.command_lib.game.servers import utils
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


class NoFieldsSpecifiedError(exceptions.Error):
  """Error if no fields are specified for a patch request."""


class PreviewTimeFieldNotRelevantError(exceptions.Error):
  """Error if preview-time is specified with dry-run false."""


def ConvertOutput(response, args):
  """Python hook that converts the output depending on preview or not both create and update api calls.

  Args:
    response: The reference to response instace.
    args: The parsed args namespace.
  Returns:
    Output response.
  """
  # Try to reenable the log output which was disabled in the request hook
  log.SetUserOutputEnabled(args.user_output_enabled != 'false')
  if not args.dry_run:
    utils.WaitForOperation(response, utils.GetApiVersionFromArgs(args))
    if 'update' in args.command_path:
      log.status.Print('Updated game server cluster: [{}]'.format(
          args.cluster))
    else:
      log.status.Print('Created game server cluster: [{}]'.format(
          args.cluster))
    return GetExistingResource(args)
  return response


def GetResourceRef(args):
  """Method to retrive the mofified resource.

  Args:
   args: The parsed args namespace.
  Returns:
   Resource reference.
  """
  project = properties.VALUES.core.project.Get(required=True)
  # If location is not provided, we fall back to the default location for
  # clusters.
  location = args.location or hooks.DEFAULT_LOCATION
  ref = resources.REGISTRY.Create(
      'gameservices.projects.locations.realms.gameServerClusters',
      projectsId=project,
      locationsId=location,
      realmsId=args.realm,
      gameServerClustersId=args.cluster)
  return ref


def GetExistingResource(args):
  resource_ref = GetResourceRef(args)
  api_version = utils.GetApiVersionFromArgs(args)
  get_request_message = GetRequestMessage(resource_ref, api_version)
  orig_resource = utils.GetClient(
      api_version).projects_locations_realms_gameServerClusters.Get(
          get_request_message)
  return orig_resource


def GetRequestMessage(resource_ref, api_version):
  return utils.GetApiMessage(
      api_version
  ).GameservicesProjectsLocationsRealmsGameServerClustersGetRequest(
      name=resource_ref.RelativeName())


def DeleteRequestMessage(resource_ref, api_version):
  return utils.GetApiMessage(
      api_version
  ).GameservicesProjectsLocationsRealmsGameServerClustersDeleteRequest(
      name=resource_ref.RelativeName())


def DeleteInstance(args):
  resource_ref = GetResourceRef(args)
  api_version = utils.GetApiVersionFromArgs(args)
  delete_request_message = DeleteRequestMessage(resource_ref, api_version)
  delete_op = utils.GetClient(
      api_version).projects_locations_realms_gameServerClusters.Delete(
          delete_request_message)
  return delete_op


def PreviewDeleteRequestMessage(resource_ref, preview_time, api_version):
  return utils.GetApiMessage(
      api_version
  ).GameservicesProjectsLocationsRealmsGameServerClustersPreviewDeleteRequest(
      name=resource_ref.RelativeName(), previewTime=preview_time)


def PreviewDeleteInstance(args):
  resource_ref = GetResourceRef(args)
  api_version = utils.GetApiVersionFromArgs(args)
  preview_time = args.preview_time if args.preview_time else None
  preview_delete_request_message = PreviewDeleteRequestMessage(
      resource_ref, preview_time, api_version)
  preview_resp = utils.GetClient(
      api_version).projects_locations_realms_gameServerClusters.PreviewDelete(
          preview_delete_request_message)
  return preview_resp


def ChooseUpdateOrPreviewMethod(unused_instance_ref, args):
  """Python hook that decides to call previewUpdate or update api.

  Args:
    unused_instance_ref: The unused instace reference.
    args: The parsed args namespace.
  Returns:
    Method to be called.
  Raises:
    PreviewTimeFieldNotRelevantError: If preview-time provided when `--dry-run`
    is set to false.
  """
  if args.dry_run:
    log.SetUserOutputEnabled(False)
    return 'previewUpdate'
  if args.preview_time:
    raise PreviewTimeFieldNotRelevantError(
        '`--preview-time` is only relevant if `--dry-run` is set to true.')
  log.status.Print('Update request issued for: [{}]'.format(args.cluster))
  log.SetUserOutputEnabled(False)
  return 'patch'


def ChooseCreateOrPreviewMethod(unused_instance_ref, args):
  """Python hook that decides to call previewCreate or create api.

  Args:
    unused_instance_ref: The unused instace reference.
    args: The parsed args namespace.
  Returns:
    Method to be called.
  Raises:
    PreviewTimeFieldNotRelevantError: If preview-time provided when `--dry-run`
    is set to false.
  """
  if args.dry_run:
    log.SetUserOutputEnabled(False)
    if not args.format:
      args.format = 'json'
    return 'previewCreate'
  if args.preview_time:
    raise PreviewTimeFieldNotRelevantError(
        '`--preview-time` is only relevant if `--dry-run` is set to true.')
  log.status.Print('Create request issued for: [{}]'.format(args.cluster))
  log.SetUserOutputEnabled(False)
  return 'create'


def SetUpdateMask(ref, args, request):
  """Python hook that computes the update mask for a patch request.

  Args:
    ref: The game server cluster resource reference.
    args: The parsed args namespace.
    request: The update game server cluster request.
  Returns:
    Request with update mask set appropriately.
  Raises:
    NoFieldsSpecifiedError: If no fields were provided for updating.
  """
  del ref
  update_mask = []

  if (args.IsSpecified('update_labels') or
      args.IsSpecified('remove_labels') or
      args.IsSpecified('clear_labels')):
    update_mask.append('labels')

  if not args.dry_run and not update_mask:
    raise NoFieldsSpecifiedError(
        'Must specify at least one parameter to update.')

  request.updateMask = ','.join(update_mask)
  return request
