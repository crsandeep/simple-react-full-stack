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
"""Org Policy command utilities."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import json
import re

from apitools.base.py import encoding
from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.labelmanager import service as labelmanager
from googlecloudsdk.api_lib.orgpolicy import service as org_policy_service
from googlecloudsdk.api_lib.orgpolicy import utils as org_policy_utils
from googlecloudsdk.command_lib.labelmanager import utils as label_manager_utils
from googlecloudsdk.command_lib.org_policies import exceptions
from googlecloudsdk.core import log as core_log
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files

CONSTRAINT_PREFIX = 'constraints/'


def GetConstraintFromArgs(args):
  """Returns the constraint from the user-specified arguments.

  A constraint has the following syntax: constraints/{constraint_name}.

  This handles both cases in which the user specifies and does not specify the
  constraint prefix.

  Args:
    args: argparse.Namespace, An object that contains the values for the
      arguments specified in the Args method.
  """
  if args.constraint.startswith(CONSTRAINT_PREFIX):
    return args.constraint

  return CONSTRAINT_PREFIX + args.constraint


def GetConstraintNameFromArgs(args):
  """Returns the constraint name from the user-specified arguments.

  This handles both cases in which the user specifies and does not specify the
  constraint prefix.

  Args:
    args: argparse.Namespace, An object that contains the values for the
      arguments specified in the Args method.
  """
  if args.constraint.startswith(CONSTRAINT_PREFIX):
    return args.constraint[len(CONSTRAINT_PREFIX):]

  return args.constraint


def GetResourceFromArgs(args):
  """Returns the resource from the user-specified arguments.

  A resource has the following syntax:
  [organizations|folders|projects]/{resource_id}.

  Args:
    args: argparse.Namespace, An object that contains the values for the
      arguments specified in the Args method.
  """
  resource_id = args.organization or args.folder or args.project

  if args.organization:
    resource_type = 'organizations'
  elif args.folder:
    resource_type = 'folders'
  else:
    resource_type = 'projects'

  return '{}/{}'.format(resource_type, resource_id)


def GetPolicyNameFromArgs(args):
  """Returns the policy name from the user-specified arguments.

  A policy name has the following syntax:
  [organizations|folders|projects]/{resource_id}/policies/{constraint_name}.

  Args:
    args: argparse.Namespace, An object that contains the values for the
      arguments specified in the Args method.
  """
  resource = GetResourceFromArgs(args)
  constraint_name = GetConstraintNameFromArgs(args)

  return '{}/policies/{}'.format(resource, constraint_name)


def GetLabelKeyAndLabelValueInputFromCondition(condition):
  """Parse label key and label value input from condition.

  The condition argument has the following syntax:
  resource.matchLabels("label_key_input", "label_value_input")

  Args:
    condition: str, A condition string to be parsed.

  Returns:
    Tuple of label key and label value inputs
  """

  matches = re.search(
      r"""resource\.matchLabels\(['"](.+?)['"], ['"](.+?)['"]\)""",
      condition)
  if matches:
    return matches.groups()
  raise exceptions.InvalidInputError(
      'Label condition must be of the form: resource.matchLabels('
      '"label_key_input", "label_value_input").'
  )


def TransformLabelDisplayNameConditionToLabelNameCondition(args):
  """Set the condition on the argument with label IDs.

  Args:
    args: argparse.Namespace, An object that contains the values for the
      arguments specified in the Args method.
  """
  display_names = GetLabelKeyAndLabelValueInputFromCondition(
      args.condition)
  try:
    label_key_name = label_manager_utils.GetLabelKeyFromDisplayName(
        display_names[0], args.label_parent)
    label_value_name = label_manager_utils.GetLabelValueFromDisplayName(
        display_names[1], label_key_name)
  except label_manager_utils.InvalidInputError as e:
    raise exceptions.InvalidInputError(
        '%s. Note that if you are using a LabelKey ID and LabelValue ID, '
        'do not set the --label-parent flag.' % e)
  args.condition = "resource.matchLabels('%s', '%s')" % (label_key_name,
                                                         label_value_name)


def UpdateLabelNamesInCondition(policy):
  """Set the condition on the policy with label display names.

  Args:
    policy: messages.GoogleCloudOrgpolicyV2alpha1Policy, The policy to be
      updated.
  """
  labelkeys_service = labelmanager.LabelKeysService()
  labelvalues_service = labelmanager.LabelValuesService()
  labelmanager_messages = labelmanager.LabelManagerMessages()

  for rule in policy.spec.rules:
    if rule.condition:
      label_key, label_value = GetLabelKeyAndLabelValueInputFromCondition(
          rule.condition.expression)
      try:
        label_key_display_name = labelkeys_service.Get(
            labelmanager_messages.LabelmanagerLabelKeysGetRequest(
                name=label_key)).displayName
        label_value_display_name = labelvalues_service.Get(
            labelmanager_messages.LabelmanagerLabelValuesGetRequest(
                name=label_value)).displayName
        rule.condition = org_policy_service.OrgPolicyMessages().GoogleTypeExpr(
            expression="resource.matchLabels('%s', '%s')" %
            (label_key_display_name, label_value_display_name))
      except apitools_exceptions.HttpForbiddenError:
        # return the label key ID and label value ID if we fail to get
        # display name
        core_log.status.Print('Permission denied accessing the label '
                              'display names, defaulting to the IDs.')
        continue


def GetMessageFromFile(filepath, message):
  """Returns a message populated from the JSON or YAML file on the specified filepath.

  Args:
    filepath: str, A local path to an object specification in JSON or YAML
      format.
    message: messages.Message, The message class to populate from the file.
  """
  file_contents = files.ReadFileContents(filepath)

  try:
    yaml_obj = yaml.load(file_contents)
    json_str = json.dumps(yaml_obj)
  except yaml.YAMLParseError:
    json_str = file_contents

  try:
    return encoding.JsonToMessage(message, json_str)
  except Exception as e:
    raise exceptions.InvalidInputError('Unable to parse file [{}]: {}.'.format(
        filepath, e))


def RemoveAllowedValuesFromPolicy(policy, args):
  """Removes the specified allowed values from all policy rules containing the specified condition.

  This first searches the policy for all rules that contain the specified
  condition. Then it searches for and removes the specified values from the
  lists of allowed values on those rules. Any modified rule with empty lists
  of allowed values and denied values after this operation is deleted.

  Args:
    policy: messages.GoogleCloudOrgpolicyV2alpha1Policy, The policy to be
      updated.
    args: argparse.Namespace, An object that contains the values for the
      arguments specified in the Args method.

  Returns:
    The updated policy.
  """
  new_policy = copy.deepcopy(policy)

  rules_to_update = org_policy_utils.GetMatchingRulesFromPolicy(
      new_policy, args.condition)
  if not rules_to_update:
    return policy

  # Remove the specified values from the list of allowed values for each rule.
  specified_values = set(args.value)
  for rule_to_update in rules_to_update:
    if rule_to_update.values is not None:
      rule_to_update.values.allowedValues = [
          value for value in rule_to_update.values.allowedValues
          if value not in specified_values
      ]

  return _DeleteRulesWithEmptyValues(new_policy, args)


def RemoveDeniedValuesFromPolicy(policy, args):
  """Removes the specified denied values from all policy rules containing the specified condition.

  This first searches the policy for all rules that contain the specified
  condition. Then it searches for and removes the specified values from the
  lists of denied values on those rules. Any modified rule with empty lists
  of allowed values and denied values after this operation is deleted.

  Args:
    policy: messages.GoogleCloudOrgpolicyV2alpha1Policy, The policy to be
      updated.
    args: argparse.Namespace, An object that contains the values for the
      arguments specified in the Args method.

  Returns:
    The updated policy.
  """
  new_policy = copy.deepcopy(policy)

  rules_to_update = org_policy_utils.GetMatchingRulesFromPolicy(
      new_policy, args.condition)
  if not rules_to_update:
    return policy

  # Remove the specified values from the list of denied values for each rule.
  specified_values = set(args.value)
  for rule_to_update in rules_to_update:
    if rule_to_update.values is not None:
      rule_to_update.values.deniedValues = [
          value for value in rule_to_update.values.deniedValues
          if value not in specified_values
      ]

  return _DeleteRulesWithEmptyValues(new_policy, args)


def _DeleteRulesWithEmptyValues(policy, args):
  """Delete any rule containing the specified condition with empty lists of allowed values and denied values and no other field set.

  Args:
    policy: messages.GoogleCloudOrgpolicyV2alpha1Policy, The policy to be
      updated.
    args: argparse.Namespace, An object that contains the values for the
      arguments specified in the Args method.

  Returns:
    The updated policy.
  """
  new_policy = copy.deepcopy(policy)

  org_policy_messages = org_policy_service.OrgPolicyMessages()

  condition = None
  if args.condition is not None:
    condition = org_policy_messages.GoogleTypeExpr(expression=args.condition)
  empty_values = org_policy_messages.GoogleCloudOrgpolicyV2alpha1PolicySpecPolicyRuleStringValues(
  )
  matching_empty_rule = org_policy_messages.GoogleCloudOrgpolicyV2alpha1PolicySpecPolicyRule(
      condition=condition, values=empty_values)
  new_policy.spec.rules = [
      rule for rule in new_policy.spec.rules if rule != matching_empty_rule
  ]

  return new_policy
