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
"""Deny command for the Org Policy CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import copy
import itertools

from googlecloudsdk.api_lib.orgpolicy import utils as org_policy_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.labelmanager import arguments as label_manager_arguments
from googlecloudsdk.command_lib.org_policies import arguments
from googlecloudsdk.command_lib.org_policies import exceptions
from googlecloudsdk.command_lib.org_policies import interfaces
from googlecloudsdk.command_lib.org_policies import utils


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Deny(interfaces.OrgPolicyGetAndUpdateCommand):
  r"""Add (or remove) values to the list of denied values for a list constraint, or optionally deny all values.

  Adds (or removes) values to the list of denied values for a list constraint,
  or optionally denies all values. Specify no values when calling this command
  to deny all values. A condition can optionally be specified to filter the
  resources the added (or removed) values apply to. If values are being added
  and the policy does not exist, the policy will be created.

  ## EXAMPLES
  To add 'us-east1' and 'us-west1' to the list of denied values on the policy
  associated with the constraint 'gcp.resourceLocations' and the Project
  'foo-project', run:

    $ {command} gcp.resourceLocations us-east1 us-west1 --project=foo-project

  To only add the values for resources that have the LabelValue '2222'
  associated with the LabelKey '1111', run:

    $ {command} gcp.resourceLocations us-east1 us-west1 --project=foo-project \
    --condition='resource.matchLabels("labelKeys/1111", "labelValues/2222")'

  To deny the policy behavior for the Project 'foo-project' conditioned on
  the LabelValue 'dev' under LabelKey 'env' that lives under
  'organizations/123' run:

    $ {command} gcp.resourceLocations us-east1 us-west1 --project=foo-project \
    --condition='resource.matchLabels("env", "dev")' \
    --label-parent='organizations/123'
  """

  @staticmethod
  def Args(parser):
    super(Deny, Deny).Args(parser)
    arguments.AddValueArgToParser(parser)
    arguments.AddConditionFlagToParser(parser)
    label_manager_arguments.AddLabelParentArgToParser(
        parser, False,
        ('This flag must be specified as the parent of the LabelKey when the '
         'input for a condition expression is set as the LabelKey and '
         'LabelValue display name.')
    )
    parser.add_argument(
        '--remove',
        action='store_true',
        help='Remove the specified values from the list of denied values instead of adding them.'
    )

  def Run(self, args):
    """Extends the superclass method to do validation and disable creation of a new policy if --remove is specified.

    Args:
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the Args method.
    """
    if not args.value and args.remove:
      raise exceptions.InvalidInputError(
          'One or more values need to be specified if --remove is specified.')

    if args.remove:
      self.disable_create = True

    if args.IsSpecified('condition') and args.IsSpecified('label_parent'):
      utils.TransformLabelDisplayNameConditionToLabelNameCondition(args)

    return super(Deny, self).Run(args)

  def UpdatePolicy(self, policy, args):
    """Adds (or removes) values to the list of denied values or denies all values on the policy.

    If one or more values are specified and --remove is specified, then a
    workflow for removing values is used. This workflow first searches the
    policy for all rules that contain the specified condition. Then it searches
    for and removes the specified values from the lists of denied values on the
    rules. Any modified rule with empty lists of allowed values and denied
    values after this operation is deleted.

    If one or more values are specified and --remove is not specified, then a
    workflow for adding values is used. This workflow first executes the remove
    workflow, except it removes values from the lists of allowed values instead
    of the lists of denied values. It then checks to see if the policy already
    has all the specified values. If not, it searches for all rules that contain
    the specified condition. In the case that the condition is not specified,
    the search is scoped to rules without conditions. If one of the rules has
    denyAll set to True, the policy is returned as is. If no such rule is found,
    a new rule with a matching condition is created. The list of denied values
    on the found or created rule is updated to include the missing values.
    Duplicate values specified by the user are pruned.

    If no values are specified, then a workflow for denying all values is used.
    This workflow first searches for and removes the rules that contain the
    specified condition from the policy. In the case that the condition is not
    specified, the search is scoped to rules without conditions set. A new rule
    with a matching condition is created. The denyAll field on the created rule
    is set to True.

    Args:
      policy: messages.GoogleCloudOrgpolicyV2alpha1Policy, The policy to be
        updated.
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the Args method.

    Returns:
      The updated policy.
    """
    if not args.value:
      return self._DenyAllValues(policy, args)

    if args.remove:
      return utils.RemoveDeniedValuesFromPolicy(policy, args)

    return self._AddValues(policy, args)

  def _AddValues(self, policy, args):
    """Adds values to an eligible policy rule containing the specified condition.

    This first searches the policy for all rules that contain the specified
    condition. Then it searches for and removes the specified values from the
    lists of allowed values on those rules. Any modified rule with empty lists
    of allowed values and denied values after this operation is deleted. This
    then checks to see if the policy already has all the specified values. If
    not, it searches for all rules that contain the specified condition. In the
    case that the condition is not specified, the search is scoped to rules
    without conditions. If one of the rules has denyAll set to True, the policy
    is returned as is. If no such rule is found, a new rule with a matching
    condition is created. The list of denied values on the found or created rule
    is updated to include the missing values. Duplicate values specified by the
    user are pruned.

    Args:
      policy: messages.GoogleCloudOrgpolicyV2alpha1Policy, The policy to be
        updated.
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the Args method.

    Returns:
      The updated policy.
    """
    new_policy = copy.deepcopy(policy)
    new_policy = utils.RemoveAllowedValuesFromPolicy(new_policy, args)

    rules = org_policy_utils.GetMatchingRulesFromPolicy(new_policy,
                                                        args.condition)

    missing_values = self._GetMissingDeniedValuesFromRules(rules, args.value)
    if not missing_values:
      return new_policy

    if not rules:
      rule_to_update, new_policy = org_policy_utils.CreateRuleOnPolicy(
          new_policy, args.condition)
    else:
      for rule in rules:
        if rule.denyAll:
          return new_policy

      rule_to_update = rules[0]
      # Unset allowAll and denyAll in case they are False.
      rule_to_update.allowAll = None
      rule_to_update.denyAll = None

    if rule_to_update.values is None:
      rule_to_update.values = self.org_policy_messages.GoogleCloudOrgpolicyV2alpha1PolicySpecPolicyRuleStringValues(
      )
    rule_to_update.values.deniedValues += list(missing_values)

    return new_policy

  def _DenyAllValues(self, policy, args):
    """Denies all values by removing old rules containing the specified condition and creating a new rule with denyAll set to True.

    This first searches for and removes the rules that contain the specified
    condition from the policy. In the case that the condition is not specified,
    the search is scoped to rules without conditions set. A new rule with a
    matching condition is created. The denyAll field on the created rule is set
    to True.

    Args:
      policy: messages.GoogleCloudOrgpolicyV2alpha1Policy, The policy to be
        updated.
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the Args method.

    Returns:
      The updated policy.
    """
    new_policy = copy.deepcopy(policy)
    new_policy.spec.rules = org_policy_utils.GetNonMatchingRulesFromPolicy(
        new_policy, args.condition)

    rule_to_update, new_policy = org_policy_utils.CreateRuleOnPolicy(
        new_policy, args.condition)
    rule_to_update.denyAll = True

    return new_policy

  def _GetMissingDeniedValuesFromRules(self, rules, values):
    """Returns a list of unique values missing from the set of denied values aggregated across the specified rules.

    Args:
      rules: [messages.GoogleCloudOrgpolicyV2alpha1PolicyPolicyRule], The list
        of policy rules to aggregate the missing denied values from.
      values: [str], The list of values to check the existence of.
    """
    if rules is None:
      rules = []

    # Create a set out of all the denied values on all the specified rules.
    existing_value_lists = [
        rule.values.deniedValues for rule in rules if rule.values
    ]
    existing_values = set(itertools.chain.from_iterable(existing_value_lists))

    # Aggregate the new values that are missing from the set of existing values.
    missing_values = collections.OrderedDict.fromkeys(
        value for value in values if value not in existing_values)
    return list(missing_values)
