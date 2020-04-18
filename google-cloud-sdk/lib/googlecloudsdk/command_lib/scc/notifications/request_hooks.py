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
"""Declarative Request Hooks for Cloud SCC's Notification Configs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.api_lib.scc import securitycenter_client as sc_client
from googlecloudsdk.command_lib.scc.hooks import GetOrganization
from googlecloudsdk.command_lib.scc.hooks import GetOrganizationFromResourceName
from googlecloudsdk.core import exceptions as core_exceptions


class InvalidNotificationConfigError(core_exceptions.Error):
  """Exception raised for errors in the input."""


def ListNotificationReqHook(ref, args, req):
  """Generate an organization id if only given numbers."""
  del ref
  req.parent = GetOrganization(args)
  return req

def DescribeNotificationReqHook(ref, args, req):
  """Generate a notification config using organization and config id."""
  del ref
  _ValidateMutexOnConfigIdAndOrganization(args)
  req.name = _GetNotificationConfigName(args)
  return req

def CreateNotificationReqHook(ref, args, req):
  """Generate a notification config using organization and config id."""
  del ref
  _ValidateMutexOnConfigIdAndOrganization(args)
  config = _GetNotificationConfigName(args)
  req.parent = GetOrganizationFromResourceName(config)
  req.configId = _GetNotificationConfigId(config)
  messages = sc_client.GetMessages("v1")
  if (args.filter is None):
    streamingConfig = messages.StreamingConfig()
    streamingConfig.filter = "";
    req.notificationConfig.streamingConfig = streamingConfig;
  return req

def DeleteNotificationReqHook(ref, args, req):
  """Generate a notification config using organization and config id."""
  del ref
  _ValidateMutexOnConfigIdAndOrganization(args)
  req.name = _GetNotificationConfigName(args)
  return req

def UpdateNotificationReqHook(ref, args, req):
  """Generate a notification config using organization and config id."""
  del ref
  _ValidateMutexOnConfigIdAndOrganization(args)
  req.name = _GetNotificationConfigName(args)
  return req

def _GetNotificationConfigName(args):
  """Returns relative resource name for a notification config."""
  resource_pattern = re.compile(
      "organizations/[0-9]+/notificationConfigs/[a-zA-Z0-9-_]{1,128}$")
  id_pattern = re.compile("[a-zA-Z0-9-_]{1,128}$")
  if not resource_pattern.match(
      args.notificationConfigId) and not id_pattern.match(
          args.notificationConfigId):
    raise InvalidNotificationConfigError(
        "NotificationConfig must match either organizations/"
        "[0-9]+/notificationConfigs/[a-zA-Z0-9-_]{1,128})$ or "
        "[a-zA-Z0-9-_]{1,128}$.")
  if resource_pattern.match(args.notificationConfigId):
    # Handle config id as full resource name
    return args.notificationConfigId
  return GetOrganization(args) + "/notificationConfigs/" + args.notificationConfigId

def _GetNotificationConfigId(resource_name):
  params_as_list = resource_name.split("/")
  return params_as_list[3]

def _ValidateMutexOnConfigIdAndOrganization(args):
  """Validates that only a full resource name or split arguments are provided."""
  if "/" in args.notificationConfigId:
    if args.organization is not None:
      raise InvalidNotificationConfigError(
          "Only provide a full resouce name "
          "(organizations/123/notificationConfigs/test-config) or an --organization "
          "flag, not both.")
  else:
    if args.organization is None:
      raise InvalidNotificationConfigError(
          "Organization must be provided if it is not included in notification id."
      )
