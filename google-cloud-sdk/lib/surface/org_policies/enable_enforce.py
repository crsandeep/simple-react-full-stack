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
"""Enable-enforce command for the Org Policy CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.api_lib.orgpolicy import utils as org_policy_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.labelmanager import arguments as label_manager_arguments
from googlecloudsdk.command_lib.org_policies import arguments
from googlecloudsdk.command_lib.org_policies import exceptions
from googlecloudsdk.command_lib.org_policies import interfaces
from googlecloudsdk.command_lib.org_policies import utils


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class EnableEnforce(interfaces.OrgPolicyGetAndUpdateCommand):
  r"""Enable enforcement of a boolean constraint.

  Enables enforcement of a boolean constraint. A condition can optionally be
  specified to filter the resources the enforcement applies to. The policy will
  be created if it does not exist.

  ## EXAMPLES

  To enable enforcement of the constraint 'iam.disableServiceAccountCreation' on
  the Project 'foo-project', run:

    $ {command} iam.disableServiceAccountCreation --project=foo-project

  To only enable enforcement for resources that have the LabelValue '2222'
  associated with the LabelKey '1111', run:

    $ {command} iam.disableServiceAccountCreation --project=foo-project \
    --condition='resource.matchLabels("labelKeys/1111", "labelValues/2222")'

  To enable enforcement of the policy behavior for the Project 'foo-project'
  conditioned on the LabelValue 'dev' under LabelKey 'env' that lives under
  'organizations/123' run:

    $ {command} iam.disableServiceAccountCreation --project=foo-project \
    --condition='resource.matchLabels("env", "dev")' \
    --label-parent='organizations/123'
  """

  @staticmethod
  def Args(parser):
    super(EnableEnforce, EnableEnforce).Args(parser)
    arguments.AddConditionFlagToParser(parser)
    label_manager_arguments.AddLabelParentArgToParser(
        parser, False,
        ('This flag must be specified as the parent of the LabelKey when the '
         'input for a condition expression is set as the LabelKey and '
         'LabelValue display names.')
    )

  def Run(self, args):
    """Extends the superclass method to process label aliasing.

    Args:
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the Args method.
    """

    if args.IsSpecified('condition') and args.IsSpecified('label_parent'):
      utils.TransformLabelDisplayNameConditionToLabelNameCondition(args)

    return super(EnableEnforce, self).Run(args)

  def UpdatePolicy(self, policy, args):
    """Enables enforcement by removing old rules containing the specified condition and creating a new rule with enforce set to True.

    This first does validation to ensure the specified action can be carried out
    according to the boolean policy contract. This contract states that exactly
    one unconditional rule has to exist on nonempty boolean policies, and that
    every conditional rule that exists on a boolean policy has to take the
    opposite enforcement value as that of the unconditional rule.

    This then searches for and removes the rules that contain the specified
    condition from the policy. In the case that the condition is not specified,
    the search is scoped to rules without conditions set. A new rule with a
    matching condition is created. The enforce field on the created rule is set
    to True.

    If the policy is empty and the condition is specified, then a new rule
    containing the specified condition is created. In order to comply with the
    boolean policy contract, a new unconditional rule is created as well with
    enforce set to False.

    Args:
      policy: messages.GoogleCloudOrgpolicyV2alpha1Policy, The policy to be
        updated.
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the Args method.

    Returns:
      The updated policy.
    """
    if policy.spec.rules:
      unconditional_rules = org_policy_utils.GetMatchingRulesFromPolicy(
          policy, None)
      if not unconditional_rules:
        raise exceptions.BooleanPolicyValidationError(
            'An unconditional enforce value does not exist on the nonempty policy.'
        )
      unconditional_rule = unconditional_rules[0]

      if args.condition is None and len(policy.spec.rules) > 1:
        # Unconditional enforce value cannot be changed on policies with more
        # than one rule.

        if not unconditional_rule.enforce:
          raise exceptions.BooleanPolicyValidationError(
              'Unconditional enforce value cannot be the same as a conditional enforce value on the policy.'
          )

        # No changes needed.
        return policy

      if args.condition is not None and unconditional_rule.enforce:
        raise exceptions.BooleanPolicyValidationError(
            'Conditional enforce value cannot be the same as the unconditional enforce value on the policy.'
        )

    new_policy = copy.deepcopy(policy)

    if not new_policy.spec.rules and args.condition is not None:
      unconditional_rule, new_policy = org_policy_utils.CreateRuleOnPolicy(
          new_policy, None)
      unconditional_rule.enforce = False

    new_policy.spec.rules = org_policy_utils.GetNonMatchingRulesFromPolicy(
        new_policy, args.condition)

    rule_to_update, new_policy = org_policy_utils.CreateRuleOnPolicy(
        new_policy, args.condition)
    rule_to_update.enforce = True

    return new_policy
