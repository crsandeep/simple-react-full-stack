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
"""'notebooks instances create' command."""

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
        Request for creating notebook instances.
    """,
    'EXAMPLES':
        """
    To create an instance from an environment, run:

      $ {command} example-instance --location=us-central1-b --environment=example-env --environment-location=us-central1-a --machine-type=n1-standard-4

    To create an instance from a VmImage family, run:

      $ {command} example-instance --vm-image-project=deeplearning-platform-release --vm-image-family=caffe1-latest-cpu-experimental --machine-type=n1-standard-4 --location=us-central1-b

    To create an instance from a VmImage name, run:

      $ {command} example-instance --vm-image-project=deeplearning-platform-release --vm-image-name=tf2-2-1-cu101-notebooks-20200110 --machine-type=n1-standard-4 --location=us-central1-b

    To create an instance from a Container Repository, run:

      $ {command} example-instance --container-repository=gcr.io/deeplearning-platform-release/base-cpu --container-tag=test-tag --machine-type=n1-standard-4
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Create(base.CreateCommand):
  """Request for creating an instance."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddCreateInstanceFlags(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command."""
    instance_service = util.GetClient().projects_locations_instances
    operation = instance_service.Create(
        instance_util.CreateInstanceCreateRequest(args))
    return instance_util.HandleLRO(
        operation,
        args,
        instance_service,
        operation_type=instance_util.OperationType.CREATE)


Create.detailed_help = DETAILED_HELP
