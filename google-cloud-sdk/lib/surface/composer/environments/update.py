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
"""Command that updates scalar properties of an environment."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.composer import environments_util as environments_api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.composer import environment_patch_util as patch_util
from googlecloudsdk.command_lib.composer import flags
from googlecloudsdk.command_lib.composer import image_versions_util as image_versions_command_util
from googlecloudsdk.command_lib.composer import resource_args
from googlecloudsdk.command_lib.composer import util as command_util


DETAILED_HELP = {
    'EXAMPLES':
        """\
          To update the Cloud Composer environment named ``env-1'' to have 8
          Airflow workers, and not have the ``production'' label, run:

            $ {command} env-1 --node-count=8 --remove-labels=production
        """
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.Command):
  """Update properties of a Cloud Composer environment."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    resource_args.AddEnvironmentResourceArg(parser, 'to update')
    base.ASYNC_FLAG.AddToParser(parser)

    Update.update_type_group = parser.add_mutually_exclusive_group(
        required=True, help='The update type.')
    flags.AddNodeCountUpdateFlagToGroup(Update.update_type_group)
    flags.AddPypiUpdateFlagsToGroup(Update.update_type_group)
    flags.AddEnvVariableUpdateFlagsToGroup(Update.update_type_group)
    flags.AddAirflowConfigUpdateFlagsToGroup(Update.update_type_group)
    flags.AddLabelsUpdateFlagsToGroup(Update.update_type_group)

  def _ConstructPatch(self,
                      env_ref,
                      args,
                      support_environment_upgrades=False,
                      support_web_server_access_control=False):

    params = dict(
        env_ref=env_ref,
        node_count=args.node_count,
        update_pypi_packages_from_file=args.update_pypi_packages_from_file,
        clear_pypi_packages=args.clear_pypi_packages,
        remove_pypi_packages=args.remove_pypi_packages,
        update_pypi_packages=dict(
            command_util.SplitRequirementSpecifier(r)
            for r in args.update_pypi_package),
        clear_labels=args.clear_labels,
        remove_labels=args.remove_labels,
        update_labels=args.update_labels,
        clear_airflow_configs=args.clear_airflow_configs,
        remove_airflow_configs=args.remove_airflow_configs,
        update_airflow_configs=args.update_airflow_configs,
        clear_env_variables=args.clear_env_variables,
        remove_env_variables=args.remove_env_variables,
        update_env_variables=args.update_env_variables,
        release_track=self.ReleaseTrack())

    if support_environment_upgrades:
      params['update_image_version'] = args.image_version
    if support_web_server_access_control:
      params['update_web_server_access_control'] = (
          environments_api_util.BuildWebServerAllowedIps(
              args.update_web_server_allow_ip, args.web_server_allow_all,
              args.web_server_deny_all))

    return patch_util.ConstructPatch(**params)

  def Run(self, args):
    env_ref = args.CONCEPTS.environment.Parse()
    field_mask, patch = self._ConstructPatch(env_ref, args)
    return patch_util.Patch(
        env_ref,
        field_mask,
        patch,
        args.async_,
        release_track=self.ReleaseTrack())


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBeta(Update):
  """Update properties of a Cloud Composer environment."""

  @staticmethod
  def AlphaAndBetaArgs(parser):
    Update.Args(parser)

    # Environment upgrade arguments
    UpdateBeta.support_environment_upgrades = True
    flags.AddEnvUpgradeFlagsToGroup(Update.update_type_group)
    UpdateBeta.support_web_server_access_control = False

  @staticmethod
  def Args(parser):
    UpdateBeta.AlphaAndBetaArgs(parser)
    UpdateBeta.support_web_server_access_control = True
    web_server_group = Update.update_type_group.add_mutually_exclusive_group()
    flags.UPDATE_WEB_SERVER_ALLOW_IP.AddToParser(web_server_group)
    flags.WEB_SERVER_ALLOW_ALL.AddToParser(web_server_group)
    flags.WEB_SERVER_DENY_ALL.AddToParser(web_server_group)

  def Run(self, args):
    env_ref = args.CONCEPTS.environment.Parse()

    if args.airflow_version:
      # Converts airflow_version arg to image_version arg
      args.image_version = (
          image_versions_command_util.ImageVersionFromAirflowVersion(
              args.airflow_version))

    # Checks validity of image_version upgrade request.
    if (args.image_version and
        not image_versions_command_util.IsValidImageVersionUpgrade(
            env_ref, args.image_version, self.ReleaseTrack())):
      raise command_util.InvalidUserInputError(
          'Invalid environment upgrade. [Requested: {}]'.format(
              args.image_version))

    # Checks validity of update_web_server_allow_ip
    if (self.ReleaseTrack() == base.ReleaseTrack.BETA and
        args.update_web_server_allow_ip):
      flags.ValidateIpRanges(
          [acl['ip_range'] for acl in args.update_web_server_allow_ip])

    field_mask, patch = self._ConstructPatch(
        env_ref, args, UpdateBeta.support_environment_upgrades,
        UpdateBeta.support_web_server_access_control)

    return patch_util.Patch(
        env_ref,
        field_mask,
        patch,
        args.async_,
        release_track=self.ReleaseTrack())


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(UpdateBeta):
  """Update properties of a Cloud Composer environment."""

  @staticmethod
  def Args(parser):
    UpdateBeta.AlphaAndBetaArgs(parser)
