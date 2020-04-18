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
"""Update hooks for Cloud Game Servers Deployment."""

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
  if not args.dry_run:
    utils.WaitForOperation(response, utils.GetApiVersionFromArgs(args))
    log.status.Print('Updated rollout for: [{}]'.format(args.deployment))
    return GetExistingResource(args)

  return response


def GetResourceRef(args):
  project = properties.VALUES.core.project.Get(required=True)
  location = args.location or hooks.DEFAULT_LOCATION
  ref = resources.REGISTRY.Create(
      'gameservices.projects.locations.gameServerDeployments',
      projectsId=project,
      locationsId=location,
      gameServerDeploymentsId=args.deployment)
  return ref


def GetExistingResource(args):
  resource_ref = GetResourceRef(args)
  api_version = utils.GetApiVersionFromArgs(args)
  get_request_message = GetRequestMessage(resource_ref, api_version)
  orig_resource = utils.GetClient(
      api_version).projects_locations_gameServerDeployments.GetRollout(
          get_request_message)
  return orig_resource


def GetRequestMessage(resource_ref, api_version):
  return utils.GetApiMessage(
      api_version
  ).GameservicesProjectsLocationsGameServerDeploymentsGetRolloutRequest(
      name=resource_ref.RelativeName())


def ChooseUpdateOrPreviewMethod(unused_instance_ref, args):
  if args.dry_run:
    return 'previewRollout'

  if args.preview_time:
    raise PreviewTimeFieldNotRelevantError(
        '`--preview-time` is only relevant if `--dry-run` is set to true.')
  log.status.Print('Update rollout request issued for: [{}]'.format(
      args.deployment))
  return 'updateRollout'


def SetUpdateMaskForDeployment(ref, args, request):
  """Python hook that computes the update mask for a patch request.

  Args:
    ref: The deployment resource reference.
    args: The parsed args namespace.
    request: The update deployment request.

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
  if not update_mask:
    raise NoFieldsSpecifiedError(
        'Must specify at least one parameter to update.')
  request.updateMask = ','.join(update_mask)
  return request


def SetUpdateMaskForRollout(ref, args, request):
  """Python hook that computes the update mask for a patch request.

  Args:
    ref: The rollout resource reference.
    args: The parsed args namespace.
    request: The update rollout request.

  Returns:
    Request with update mask set appropriately.
  Raises:
    NoFieldsSpecifiedError: If no fields were provided for updating.
  """
  del ref
  update_mask = []

  if args.IsSpecified('default_config') or args.clear_default_config:
    update_mask.append('defaultGameServerConfig')
  if args.config_overrides_file or args.clear_config_overrides:
    update_mask.append('gameServerConfigOverrides')

  if not args.dry_run and not update_mask:
    raise NoFieldsSpecifiedError(
        'Must specify at least one parameter to update.')

  request.updateMask = ','.join(update_mask)
  return request


def ClearConfigOverrides(ref, args, request):
  del ref
  if args.clear_config_overrides:
    if not request.gameServerDeploymentRollout:
      messages = utils.GetMessages(utils.GetApiVersionFromArgs(args))
      gsd = messages.GameServerDeploymentRollout()
      request.gameServerDeploymentRollout = gsd
    request.gameServerDeploymentRollout.gameServerConfigOverrides = []
  return request


def ClearDefaultConfig(ref, args, request):
  del ref
  if args.clear_default_config:
    if not request.gameServerDeploymentRollout:
      messages = utils.GetMessages(utils.GetApiVersionFromArgs(args))
      gsd = messages.GameServerDeploymentRollout()
      request.gameServerDeploymentRollout = gsd
    request.gameServerDeploymentRollout.defaultGameServerConfig = ''
  return request


def ProcessConfigsFiles(ref, args, request):
  """Reads the config into GameServerConfig proto and updates the request."""
  del ref
  if args.config_overrides_file:
    if not request.gameServerDeploymentRollout:
      messages = utils.GetMessages(utils.GetApiVersionFromArgs(args))
      gsd = messages.GameServerDeploymentRollout()
      request.gameServerDeploymentRollout = gsd
    request.gameServerDeploymentRollout.gameServerConfigOverrides = utils.ProcessConfigOverrideFile(
        args.config_overrides_file, utils.GetApiVersionFromArgs(args))
  return request
