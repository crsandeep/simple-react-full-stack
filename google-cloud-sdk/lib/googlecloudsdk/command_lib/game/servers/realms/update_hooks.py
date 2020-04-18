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
"""Update hooks for Cloud Game Servers Realm."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

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
  # Try to reenable the log output which was disabled in the request hook
  log.SetUserOutputEnabled(args.user_output_enabled != 'false')
  if not args.dry_run:
    utils.WaitForOperation(response, utils.GetApiVersionFromArgs(args))
    log.status.Print('Updated realm: [{}]'.format(args.realm))
    return GetExistingResource(args)

  return response


def GetResourceRef(args):
  project = properties.VALUES.core.project.Get(required=True)
  ref = resources.REGISTRY.Create(
      'gameservices.projects.locations.realms',
      projectsId=project,
      locationsId=args.location,
      realmsId=args.realm)
  return ref


def GetExistingResource(args):
  resource_ref = GetResourceRef(args)
  api_version = utils.GetApiVersionFromArgs(args)
  get_request_message = GetRequestMessage(resource_ref, api_version)
  orig_resource = utils.GetClient(
      api_version).projects_locations_realms.Get(
          get_request_message)
  return orig_resource


def GetRequestMessage(resource_ref, api_version):
  return utils.GetApiMessage(
      api_version).GameservicesProjectsLocationsRealmsGetRequest(
          name=resource_ref.RelativeName())


def ChooseUpdateOrPreviewMethod(unused_instance_ref, args):
  if args.dry_run:
    log.SetUserOutputEnabled(False)
    return 'previewUpdate'
  if args.preview_time:
    raise PreviewTimeFieldNotRelevantError(
        '`--preview-time` is only relevant if `--dry-run` is set to true.')
  log.status.Print('Update request issued for: [{}]'.format(args.realm))
  log.SetUserOutputEnabled(False)
  return 'patch'


def SetUpdateMask(ref, args, request):
  """Python hook that computes the update mask for a patch request.

  Args:
    ref: Resource reference.
    args: The parsed args namespace.
    request: The update request.
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
  if args.IsSpecified('time_zone'):
    update_mask.append('timeZone')

  if not args.dry_run and not update_mask:
    raise NoFieldsSpecifiedError(
        'Must specify at least one parameter to update.')

  request.updateMask = ','.join(update_mask)
  return request
