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
"""Utilities for defining Label Manager arguments on a parser."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.labelmanager import service as labelmanager
from googlecloudsdk.core import exceptions


class LabelManagerError(exceptions.Error):
  """Top-level exception for Label Manager errors."""


class InvalidInputError(LabelManagerError):
  """Exception for invalid input."""


def GetLabelKeyFromDisplayName(display_name, label_parent):
  """Returns the LabelKey with display_name under label_parent if it exists.

  Args:
    display_name: String, display name of the LabelKey
    label_parent: String, resource name of the parent of the LabelKey

  Raises:
    InvalidInputError: if the specified display_name does not exist under the
    label_parent

  Returns:
    The resource name of the LabelKey associated with the display_name
  """
  labelkeys_service = labelmanager.LabelKeysService()
  labelmanager_messages = labelmanager.LabelManagerMessages()

  list_request = labelmanager_messages.LabelmanagerLabelKeysListRequest(
      parent=label_parent, showDeleted=True)
  response = labelkeys_service.List(list_request)

  for key in response.keys:
    if key.displayName == display_name:
      return key.name

  raise InvalidInputError(
      'Invalid display_name for LabelKey [{}] in parent [{}]'.format(
          display_name, label_parent))


def GetLabelValueFromDisplayName(display_name, label_key):
  """Returns the LabelValue with display_name under label_key if it exists.

  Args:
    display_name: String, display name of the LabelValue
    label_key: String, resource name of the parent of the LabelKey

  Raises:
    InvalidInputError: if the specified display_name does not exist under the
    label_key

  Returns:
    The resource name of the LabelValue associated with the display_name
  """
  labelvalues_service = labelmanager.LabelValuesService()
  labelmanager_messages = labelmanager.LabelManagerMessages()

  list_request = labelmanager_messages.LabelmanagerLabelValuesListRequest(
      parent=label_key, showDeleted=True)
  response = labelvalues_service.List(list_request)

  for value in response.values:
    if value.displayName == display_name:
      return value.name

  raise InvalidInputError(
      'Invalid display_name for LabelValue [{}] in parent [{}]'.format(
          display_name, label_key))


def GetLabelBindingNameFromLabelValueAndResource(label_value, resource):
  """Returns the LabelBinding name for the LabelValue and resource if it exists.

  Args:
    label_value: String, numeric id of the LabelValue
    resource: String, full resource name of the resource

  Raises:
    InvalidInputError: if the specified LabelValue and resource are not bound.

  Returns:
    The LabelBinding name of the LabelValue bound to the resource.
  """
  labelbindings_service = labelmanager.LabelBindingsService()
  labelmanager_messages = labelmanager.LabelManagerMessages()

  list_request = (
      labelmanager_messages.LabelmanagerLabelBindingsListRequest(
          filter='resource:'+resource))
  response = labelbindings_service.List(list_request)

  for binding in response.bindings:
    if binding.labelValue == label_value:
      return binding.name

  raise InvalidInputError(
      'Invalid LabelBinding for LabelValue [{}] and resource [{}]'.format(
          label_value, resource))


def GetLabelValueIfArgsAreValid(args):
  """Returns the LabelValue if valid arguments are passed and it exists.

  Args:
    args: Command line arguments for a gcloud LabelValue command.

  Raises:
    InvalidInputError: - if --label-parent is given but --label-key is not
                         given
                       - if the specified --label-key as a display name does not
                         exist under the --label-parent
                       - if LABEL_VALUE_ID as a display_name does not exist
                         under --label-key.

  Returns:
    The resource name of the LabelValue associated with the LABEL_VALUE_ID
    determined from args in the form labelValues/{numeric_id}.
  """
  label_value_id = args.LABEL_VALUE_ID

  if args.IsSpecified('label_parent') and not args.IsSpecified('label_key'):
    raise InvalidInputError(
        '--label-key must be specified if --label-parent is set.')

  if args.IsSpecified('label_key'):
    if args.IsSpecified('label_parent'):
      label_key = GetLabelKeyFromDisplayName(args.label_key, args.label_parent)
    else:
      label_key = args.label_key
    return GetLabelValueFromDisplayName(label_value_id, label_key)

  return label_value_id
