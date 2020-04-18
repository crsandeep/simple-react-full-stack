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
"""Create hooks for Cloud Game Servers Config."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.game.servers import utils


def ProcessConfigsFiles(ref, args, request):
  """Reads the fleet/scaling configs into FleetConfig/ScalingConfig protos and updates the request."""
  del ref
  if args.fleet_configs_file:
    if not request.gameServerConfig:
      messages = utils.GetMessages(utils.GetApiVersionFromArgs(args))
      gsc = messages.GameServerConfig()
      request.gameServerConfig = gsc
    request.gameServerConfig.fleetConfigs = utils.ProcessFleetConfigsFile(
        args.fleet_configs_file, utils.GetApiVersionFromArgs(args))

  if args.scaling_configs_file:
    if not request.gameServerConfig:
      messages = utils.GetMessages(utils.GetApiVersionFromArgs(args))
      gsc = messages.GameServerConfig()
      request.gameServerConfig = gsc
    request.gameServerConfig.scalingConfigs = utils.ProcessScalingConfigsFile(
        args.scaling_configs_file, utils.GetApiVersionFromArgs(args))

  return request
