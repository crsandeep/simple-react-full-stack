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
"""This module holds exceptions raised by Cloud Run commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.util import text


class UnsupportedArgumentError(calliope_exceptions.ToolException):
  """When a given argument or argument value is not currently supported."""


class MissingRequiredEventTypeParameters(calliope_exceptions.ToolException):
  """When required parameters for the event type are not provided."""

  def __init__(self, parameters, event_type):
    super(MissingRequiredEventTypeParameters, self).__init__(
        'Missing at least one required parameter [{0}] for event type: {1}'
        .format(', '.join(parameters), event_type.type))


class UnknownEventTypeParameters(calliope_exceptions.ToolException):
  """When parameters unknown to the event type are specified."""

  def __init__(self, parameters, event_type):
    super(UnknownEventTypeParameters, self).__init__(
        'Unknown {plural} [{0}] for event type: {1}'.format(
            ', '.join(parameters),
            event_type.type,
            plural=text.Pluralize(len(parameters), 'parameter')))


class EventTypeNotFound(exceptions.Error):
  """When a specified event type is not found."""


class MultipleEventTypesFound(exceptions.Error):
  """When multiple event types match but only 1 was expected."""


class TriggerNotFound(exceptions.Error):
  """When a specified trigger is not found."""


class TriggerCreationError(exceptions.Error):
  """When trigger creation fails."""


class SourceNotFound(exceptions.Error):
  """When a specified source is not found."""


class SourceCreationError(exceptions.Error):
  """When source creation fails."""


class ServiceAccountMissingRequiredPermissions(exceptions.Error):
  """When a service account does not have the necessary permissions."""
