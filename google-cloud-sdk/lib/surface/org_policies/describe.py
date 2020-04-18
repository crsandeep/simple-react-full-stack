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
"""Describe command for the Org Policy CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.orgpolicy import service as org_policy_service
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.org_policies import arguments
from googlecloudsdk.command_lib.org_policies import utils


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.DescribeCommand):
  r"""Describe an organization policy.

  Describes an organization policy.

  ## EXAMPLES

  To describe the policy associated with the constraint 'gcp.resourceLocations'
  and the Project 'foo-project', run:

    $ {command} gcp.resourceLocations --project=foo-project
  """

  @staticmethod
  def Args(parser):
    arguments.AddConstraintArgToParser(parser)
    arguments.AddResourceFlagsToParser(parser)
    parser.add_argument(
        '--effective',
        action='store_true',
        help='Describe the effective policy.')
    parser.add_argument(
        '--show-label-name',
        action='store_true',
        help=('Return label based conditions with the display name instead of '
              'ID.')
    )

  def Run(self, args):
    """Gets the (effective) organization policy.

    If --effective is not specified, then the policy is retrieved using
    GetPolicy.

    If --effective is specified, then the effective policy is retrieved using
    GetEffectivePolicy.

    Args:
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the Args method.

    Returns:
       The retrieved policy.
    """
    policy_service = org_policy_service.PolicyService()
    org_policy_messages = org_policy_service.OrgPolicyMessages()

    policy_name = utils.GetPolicyNameFromArgs(args)

    if args.effective:
      get_request = org_policy_messages.OrgpolicyPoliciesGetEffectivePolicyRequest(
          name=policy_name)
      return policy_service.GetEffectivePolicy(get_request)

    get_request = org_policy_messages.OrgpolicyPoliciesGetRequest(
        name=policy_name)
    policy = policy_service.Get(get_request)
    if args.show_label_name:
      utils.UpdateLabelNamesInCondition(policy)

    return policy
