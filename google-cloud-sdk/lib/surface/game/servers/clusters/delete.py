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

"""Deletes a Game Server Cluster instance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.game.servers import utils
from googlecloudsdk.command_lib.game.servers.clusters import flags
from googlecloudsdk.command_lib.game.servers.clusters import resource_args
from googlecloudsdk.command_lib.game.servers.clusters import update_hooks
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


class PreviewTimeFieldNotRelevantError(exceptions.Error):
  """Error if preview-time is specified with dry-run false."""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA,
                    base.ReleaseTrack.BETA)
class Delete(base.DeleteCommand):
  """Delete a Game Server Cluster."""

  @staticmethod
  def CommonArgs(parser):
    resource_args.AddClusterResourceArg(parser, 'delete')
    flags.AddDryrunArg(parser)
    flags.AddPreviewTimeArg(parser)

  @staticmethod
  def Args(parser):
    Delete.CommonArgs(parser)

  def Run(self, args):
    """Delete a Game server cluster."""
    if not args.dry_run:
      if args.preview_time:
        raise PreviewTimeFieldNotRelevantError(
            '`--preview-time` is only relevant if `--dry-run` is set to true.')

      delete_warning = ('You are about to delete game server cluster {}. '
                        'Do you want to continue?'.format(args.cluster))
      if not console_io.PromptContinue(message=delete_warning):
        return None
      log.status.Print('Delete request issued for: [{}]'.format(args.cluster))
      op = update_hooks.DeleteInstance(args)
      resp = utils.WaitForOperation(op, utils.GetApiVersionFromArgs(args))
      log.status.Print('Deleted game server cluster : [{}]'.format(
          args.cluster))
      return resp

    if not args.format:
      args.format = 'json'
    return update_hooks.PreviewDeleteInstance(args)


Delete.detailed_help = {
    'DESCRIPTION':
        'Delete a Game Server Cluster.',
    'API REFERENCE':
        """\
    This command uses the gameservices API. The full documentation for
    this API can be found at: https://cloud.google.com/solutions/gaming/
        """,
    'EXAMPLES':
        """\
To delete Game Server Cluster 'my-cluster' in project 'my-project', realm 'my-realm', and location 'my-location' run:

  $ {command} my-cluster --project=my-project --realm=my-realm --location=my-location --no-dry-run

To preview deletion of Game Server Cluster 'my-cluster' in project 'my-project', realm 'my-realm', and location 'my-location' run:

  $ {command} my-cluster --project=my-project --realm=my-realm --location=my-location --dry-run
"""
}
