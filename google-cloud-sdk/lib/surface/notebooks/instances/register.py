# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""'notebooks instances register' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.notebooks import instances as instance_util
from googlecloudsdk.api_lib.notebooks import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.notebooks import flags

DETAILED_HELP = {
    'DESCRIPTION':
        """
        Request for registering notbook instance.
    """,
    'EXAMPLES':
        """
    To register an old type instance, run:

        $ {command} /projects/example-project/locations/us-central1-b/instances/example-instance
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Register(base.Command):
  """Request for registering instances."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddRegisterInstanceFlags(parser)

  def Run(self, args):
    instance_service = util.GetClient().projects_locations_instances
    operation = instance_service.Register(
        instance_util.CreateInstanceRegisterRequest(args))
    return instance_util.HandleLRO(
        operation,
        args,
        instance_service,
        operation_type=instance_util.OperationType.UPDATE)


Register.detailed_help = DETAILED_HELP
