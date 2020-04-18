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
"""Delete command for the Org Policy CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.api_lib.orgpolicy import service as org_policy_service
from googlecloudsdk.api_lib.orgpolicy import utils as org_policy_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.labelmanager import arguments as label_manager_arguments
from googlecloudsdk.command_lib.org_policies import arguments
from googlecloudsdk.command_lib.org_policies import utils
from googlecloudsdk.core import log


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Delete(base.Command):
  r"""Delete an organization policy, or optionally only delete policy behavior defined under a condition.

  Deletes an organization policy, or optionally only deletes policy behavior
  defined under a condition. Specify the condition when calling the command to
  delete the policy behavior defined under that condition instead of the whole
  policy.

  ## EXAMPLES

  To delete the policy associated with the constraint 'gcp.resourceLocations'
  and the Project 'foo-project', run:

   $ {command} gcp.resourceLocations --project=foo-project

  To only delete the policy behavior defined for resources that have the
  LabelValue '2222' associated with the LabelKey '1111', run:

   $ {command} gcp.resourceLocations --project=foo-project \
   --condition='resource.matchLabels("labelKeys/1111", "labelValues/2222")'

  To delete the policy behavior for the Project 'foo-project' conditioned on
  the LabelValue 'dev' under LabelKey 'env' that lives under
  'organizations/123' run:

   $ {command} gcp.resourceLocations --project=foo-project \
   --condition='resource.matchLabels("env", "dev")' \
   --label-parent='organizations/123'
  """

  @staticmethod
  def Args(parser):
    arguments.AddConstraintArgToParser(parser)
    arguments.AddResourceFlagsToParser(parser)
    arguments.AddConditionFlagToParser(parser)
    label_manager_arguments.AddLabelParentArgToParser(
        parser, False,
        ('This flag must be specified as the parent of the LabelKey when the '
         'input for a condition expression is set as the LabelKey and '
         'LabelValue display name.')
    )

  def Run(self, args):
    """Deletes a whole policy or removes rules containing the specified condition from the policy.

    If --condition is not specified, then the policy is deleted using
    DeletePolicy.

    If --condition is specified, then the policy is fetched using GetPolicy. It
    then searches for and removes the rules that contain the specified condition
    from the policy. If the policy is empty after this operation and
    inheritFromParent is False, the policy is deleted using DeletePolicy. If
    not, the policy is updated using UpdatePolicy.

    Args:
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the Args method.

    Returns:
       If the policy is deleted, then messages.GoogleProtobufEmpty. If only
       a partial delete is issued, then the updated policy.
    """
    policy_service = org_policy_service.PolicyService()
    org_policy_messages = org_policy_service.OrgPolicyMessages()

    policy_name = utils.GetPolicyNameFromArgs(args)

    if args.IsSpecified('condition') and args.IsSpecified('label_parent'):
      utils.TransformLabelDisplayNameConditionToLabelNameCondition(args)

    if args.condition is not None:
      get_request = org_policy_messages.OrgpolicyPoliciesGetRequest(
          name=policy_name)
      policy = policy_service.Get(get_request)

      new_policy = copy.deepcopy(policy)
      new_policy.spec.rules = org_policy_utils.GetNonMatchingRulesFromPolicy(
          policy, args.condition)

      if policy == new_policy:
        return policy

      if new_policy.spec.rules or new_policy.spec.inheritFromParent:
        update_request = org_policy_messages.OrgpolicyPoliciesPatchRequest(
            name=policy_name,
            forceUnconditionalWrite=False,
            googleCloudOrgpolicyV2alpha1Policy=new_policy)
        update_response = policy_service.Patch(update_request)
        log.UpdatedResource(policy_name, 'policy')
        return update_response

    delete_request = org_policy_messages.OrgpolicyPoliciesDeleteRequest(
        name=policy_name)
    delete_response = policy_service.Delete(delete_request)
    log.DeletedResource(policy_name, 'policy')
    return delete_response
