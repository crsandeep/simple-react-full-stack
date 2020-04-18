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
"""Set-policy command for the Org Policy CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as api_exceptions
from argcomplete import completers
from googlecloudsdk.api_lib.orgpolicy import service as org_policy_service
from googlecloudsdk.api_lib.orgpolicy import utils as org_policy_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.org_policies import exceptions
from googlecloudsdk.command_lib.org_policies import utils as utils
from googlecloudsdk.core import log


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class SetPolicy(base.Command):
  r"""Set an organization policy from a JSON or YAML file.

  Sets an organization policy from a JSON or YAML file. The policy will be
  created if it does not exist, or updated if it already exists.

  ## EXAMPLES

  To set the policy from the file on the path './sample_path', run:

    $ {command} ./sample_path
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'policy_file',
        metavar='POLICY_FILE',
        completer=completers.FilesCompleter,
        help='Path to JSON or YAML file that contains the organization policy.')

  def Run(self, args):
    """Creates or updates a policy from a JSON or YAML file.

    This first converts the contents of the specified file into a policy object.
    It then fetches the current policy using GetPolicy. If it does not exist,
    the policy is created using CreatePolicy. If it does, the retrieved policy
    is checked to see if it needs to be updated. If so, the policy is updated
    using UpdatePolicy.

    Args:
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the Args method.

    Returns:
      The created or updated policy.
    """
    policy_service = org_policy_service.PolicyService()
    org_policy_messages = org_policy_service.OrgPolicyMessages()

    input_policy = utils.GetMessageFromFile(
        args.policy_file,
        org_policy_messages.GoogleCloudOrgpolicyV2alpha1Policy)

    if not input_policy.name:
      raise exceptions.InvalidInputError(
          'Name field not present in the organization policy.')

    get_request = org_policy_messages.OrgpolicyPoliciesGetRequest(
        name=input_policy.name)
    try:
      policy = policy_service.Get(get_request)
    except api_exceptions.HttpNotFoundError:
      constraint = org_policy_utils.GetConstraintFromPolicyName(
          input_policy.name)
      parent = org_policy_utils.GetResourceFromPolicyName(input_policy.name)

      create_request = org_policy_messages.OrgpolicyPoliciesCreateRequest(
          constraint=constraint,
          parent=parent,
          googleCloudOrgpolicyV2alpha1Policy=input_policy)
      create_response = policy_service.Create(create_request)
      log.CreatedResource(input_policy.name, 'policy')
      return create_response

    if policy == input_policy:
      return policy

    update_request = org_policy_messages.OrgpolicyPoliciesPatchRequest(
        name=input_policy.name,
        forceUnconditionalWrite=False,
        googleCloudOrgpolicyV2alpha1Policy=input_policy)
    update_response = policy_service.Patch(update_request)
    log.UpdatedResource(input_policy.name, 'policy')
    return update_response
