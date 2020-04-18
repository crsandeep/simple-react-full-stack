# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Wrapper for user-visible error exceptions to raise in the CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import exceptions as api_lib_exceptions
from googlecloudsdk.core import exceptions as core_exceptions


class Error(core_exceptions.Error):
  """Exceptions for Services errors."""


class EnableServicePermissionDeniedException(Error):
  """Permission denied exception for enable service command."""
  pass


class ListServicesPermissionDeniedException(Error):
  """Permission denied exception for list services command."""
  pass


class GetServicePermissionDeniedException(Error):
  """Permission denied exception for get service command."""
  pass


class CreateQuotaOverridePermissionDeniedException(Error):
  """Permission denied exception for create quota override command."""
  pass


class UpdateQuotaOverridePermissionDeniedException(Error):
  """Permission denied exception for update quota override command."""
  pass


class DeleteQuotaOverridePermissionDeniedException(Error):
  """Permission denied exception for delete quota override command."""
  pass


class CreateConnectionsPermissionDeniedException(Error):
  """Permission denied exception for create connection command."""
  pass


class ListConnectionsPermissionDeniedException(Error):
  """Permission denied exception for list connections command."""
  pass


class EnableVpcServiceControlsPermissionDeniedException(Error):
  """Permission denied exception for enable vpc service controls command."""
  pass


class DisableVpcServiceControlsPermissionDeniedException(Error):
  """Permission denied exception for disable vpc service controls command."""
  pass


class GenerateServiceIdentityPermissionDeniedException(Error):
  """Permission denied exception for generate service identitiy command."""
  pass


class OperationErrorException(Error):
  """Exception for operation error."""
  pass


class TimeoutError(Error):
  """Exception for timeout error."""
  pass


def ReraiseError(err, klass):
  """Transform and re-raise error helper."""
  core_exceptions.reraise(klass(api_lib_exceptions.HttpException(err)))
