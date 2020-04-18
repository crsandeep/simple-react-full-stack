# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""The gcloud run group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import resource_args
from googlecloudsdk.command_lib.util.concepts import concept_parsers


DETAILED_HELP = {
    'brief': 'Manage your Cloud Run applications.',
    'DESCRIPTION': """
        The gcloud run command group lets you deploy container images
        to Google Cloud Run.
        """,
    'EXAMPLES': """\
        To deploy your container, use the `gcloud run deploy` command:

          $ gcloud run deploy <service-name> --image <image_name>

        For more information, run:
          $ gcloud run deploy --help
        """
}


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA,
    base.ReleaseTrack.BETA,
    base.ReleaseTrack.GA)
class Serverless(base.Group):
  """Manage your Cloud Run resources."""
  category = base.COMPUTE_CATEGORY
  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Adds --platform and the various related args."""
    # Add --platform
    flags.AddPlatformArg(parser)

    platform_helpers_group = parser.add_mutually_exclusive_group(
        help='Arguments to locate resources, depending on the platform used.')

    # Add --region flag
    managed_group = flags.GetManagedArgGroup(platform_helpers_group)
    flags.AddRegionArg(managed_group)

    # Add --cluster and --cluster-location (plus properties)
    gke_group = flags.GetGkeArgGroup(platform_helpers_group)
    concept_parsers.ConceptParser(
        [resource_args.CLUSTER_PRESENTATION]).AddToParser(gke_group)

    # Add --kubeconfig and --context
    kubernetes_group = flags.GetKubernetesArgGroup(platform_helpers_group)
    flags.AddKubeconfigFlags(kubernetes_group)

  def Filter(self, context, args):
    """Runs before command.Run and validates platform with passed args."""
    # Ensures a platform is set on the run/platform property and
    # all other passed args are valid for this platform and release track.
    flags.GetAndValidatePlatform(args, self.ReleaseTrack(), flags.Product.RUN)
    return context
