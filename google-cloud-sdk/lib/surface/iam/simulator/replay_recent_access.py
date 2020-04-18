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
"""Command to simulate the IAM policy changes."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.iam import assist
from googlecloudsdk.api_lib.iam.simulator import operations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import iam_util

_DETAILED_HELP = {
    'brief': """Determine affected recent access attempts before IAM policy
                change deployment.""",
    'DESCRIPTION': """\
      Replay the most recent 5,000 access logs from the past 60 days using the
      simulated policy. For each log entry, the replay determines if setting the
      provided policy on the given resource would result in a change in the access
      state, e.g. a previously granted access becoming denied. Any differences found
      are returned.""",
    'EXAMPLES': """\
      To simulate a permission change of a member on a resource, run:

        $ {command} projects/project-id path/to/policy_file.json

      See https://cloud.google.com/iam/docs/managing-policies for details of policy
      role and member types."""
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ReplayRecentAccesses(base.Command):
  """Determine affected recent access attempts before IAM policy change deployment.
  """

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'resource',
        metavar='RESOURCE',
        help="""
        Full resource name to simulate the IAM policy for.

        See: https://cloud.google.com/apis/design/resource_names#full_resource_name.
        """)
    parser.add_argument(
        'policy_file',
        metavar='POLICY_FILE',
        help="""
        Path to a local JSON or YAML formatted file containing a valid policy.

        The output of the `get-iam-policy` command is a valid file, as is any
        JSON or YAML file conforming to the structure of a
        [Policy](https://cloud.google.com/iam/reference/rest/v1/Policy).
        """)

  def Run(self, args):
    client, messages = assist.GetClientAndMessages()
    policy = iam_util.ParsePolicyFile(args.policy_file,
                                      messages.GoogleIamV1Policy)
    policy.version = iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION
    additional_property = messages.GoogleIamAssistV1alpha3ReplayConfig.PolicyOverlayValue.AdditionalProperty(
        key=args.resource, value=policy)
    overlay = messages.GoogleIamAssistV1alpha3ReplayConfig.PolicyOverlayValue(
        additionalProperties=[additional_property])
    config = messages.GoogleIamAssistV1alpha3ReplayConfig(
        policyOverlay=overlay)
    request = messages.GoogleIamAssistV1alpha3Replay(
        config=config)
    response = client.ReplaysService.Create(
        client.ReplaysService(client), request)

    operations_client = operations.Client.FromApiVersion('v1alpha3')
    operation_response = operations_client.WaitForOperation(
        response,
        'Waiting for replay [{}] to complete'.format(response.name))
    return operation_response
