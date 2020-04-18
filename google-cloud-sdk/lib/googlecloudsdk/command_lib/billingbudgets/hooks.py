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
"""hooks for billing budgets surface."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


import re
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import messages as messages_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import yaml

import six


def GetMessagesModule():
  return apis.GetMessagesModule('billingbudgets', 'v1beta1')


def GetApiMessage(message_name):
  """Return apitools message object for give message name."""
  messages = GetMessagesModule()
  return getattr(messages, message_name)


def ParseToMoneyType(money):
  """Convert the input to Money Type."""
  CheckMoneyRegex(money)
  currency_code = ''
  if re.match(r'[A-Za-z]{3}', money[-3:]):
    currency_code = money[-3:]
  messages = GetMessagesModule()
  money_array = (re.split(r'\.', money[:-3], 1) if currency_code
                 else re.split(r'\.', money))
  units = int(money_array[0]) if money_array[0] else 0
  if len(money_array) > 1:
    nanos = int(money_array[1])
  else:
    nanos = 0
  return messages.GoogleTypeMoney(
      units=units, nanos=nanos, currencyCode=currency_code)


def UpdateThresholdRules(ref, args, req):
  """Add threshold rule to budget."""
  messages = GetMessagesModule()
  client = apis.GetClientInstance('billingbudgets', 'v1beta1')
  budgets = client.billingAccounts_budgets
  get_request_type = messages.BillingbudgetsBillingAccountsBudgetsGetRequest
  get_request = get_request_type(name=six.text_type(ref.RelativeName()))
  old_threshold_rules = budgets.Get(get_request).thresholdRules
  if args.IsSpecified('clear_threshold_rules'):
    old_threshold_rules = []
    req.googleCloudBillingBudgetsV1beta1UpdateBudgetRequest.budget.thresholdRules = old_threshold_rules
  if args.IsSpecified('add_threshold_rule'):
    added_threshold_rules = args.add_threshold_rule
    final_rules = AddRules(old_threshold_rules, added_threshold_rules)
    req.googleCloudBillingBudgetsV1beta1UpdateBudgetRequest.budget.thresholdRules = final_rules
    return req
  if args.IsSpecified('threshold_rules_from_file'):
    rules_from_file = yaml.load(args.threshold_rules_from_file)
    # create a mock budget with updated threshold rules
    budget = messages_util.DictToMessageWithErrorCheck(
        {'thresholdRules': rules_from_file},
        messages.GoogleCloudBillingBudgetsV1beta1Budget)
    # update the request with the new threshold rules
    req.googleCloudBillingBudgetsV1beta1UpdateBudgetRequest.budget.thresholdRules = budget.thresholdRules
    req.googleCloudBillingBudgetsV1beta1UpdateBudgetRequest.updateMask += ',thresholdRules'
  return req


def AddRules(old_rules, rules_to_add):
  all_threshold_rules = old_rules
  for rule in rules_to_add:
    if rule not in old_rules:
      all_threshold_rules.append(rule)
  return all_threshold_rules


def LastPeriodAmount(bool_value):
  messages = GetMessagesModule(
      ).GoogleCloudBillingBudgetsV1beta1LastPeriodAmount
  if bool_value:
    return messages()


def CreateAllUpdatesRule(ref, args, req):
  del ref
  if args.IsSpecified('all_updates_rule_pubsub_topic'):
    req.googleCloudBillingBudgetsV1beta1CreateBudgetRequest.budget.allUpdatesRule.schemaVersion = '1.0'
  return req


def UpdateAllUpdatesRule(ref, args, req):
  del ref
  if args.IsSpecified('all_updates_rule_pubsub_topic'):
    req.googleCloudBillingBudgetsV1beta1UpdateBudgetRequest.budget.allUpdatesRule.schemaVersion = '1.0'
  return req


class InvalidBudgetAmountInput(exceptions.Error):
  """Error to raise when user input does not match regex."""
  pass


def CheckMoneyRegex(input_string):
  accepted_regex = re.compile(r'^[0-9]*.?[0-9]+([a-zA-Z]{3})?$')
  if not re.match(accepted_regex, input_string):
    raise InvalidBudgetAmountInput(
        'The input is not valid for --budget-amount. '
        'It must be an int or float with an optional 3-letter currency code.')
