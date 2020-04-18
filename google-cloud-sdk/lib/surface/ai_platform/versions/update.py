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
"""ai-platform versions update command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ml_engine import operations
from googlecloudsdk.api_lib.ml_engine import versions_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ml_engine import endpoint_util
from googlecloudsdk.command_lib.ml_engine import flags
from googlecloudsdk.command_lib.ml_engine import versions_util
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


def _AddUpdateArgs(parser, hide_region_arg=True):
  """Get arguments for the `ai-platform versions update` command."""
  flags.AddVersionResourceArg(parser, 'to update')
  flags.GetDescriptionFlag('version').AddToParser(parser)
  flags.GetRegionArg(hidden=hide_region_arg).AddToParser(parser)
  labels_util.AddUpdateLabelsFlags(parser)


def _Run(args):
  with endpoint_util.MlEndpointOverrides(region=args.region):
    versions_client = versions_api.VersionsClient()
    operations_client = operations.OperationsClient()
    version_ref = args.CONCEPTS.version.Parse()
    versions_util.Update(versions_client, operations_client, version_ref, args)
    log.UpdatedResource(args.version, kind='AI Platform version')


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update an AI Platform version."""

  @staticmethod
  def Args(parser):
    _AddUpdateArgs(parser)

  def Run(self, args):
    return _Run(args)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class UpdateBeta(base.UpdateCommand):
  """Update an AI Platform version."""

  @staticmethod
  def Args(parser):
    _AddUpdateArgs(parser, hide_region_arg=False)

  def Run(self, args):
    return _Run(args)
