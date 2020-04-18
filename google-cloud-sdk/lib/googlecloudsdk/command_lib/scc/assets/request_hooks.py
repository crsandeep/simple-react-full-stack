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
"""Declarative Request Hooks for Cloud SCC's Asset responses."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re

from googlecloudsdk.command_lib.scc.hooks import CleanUpUserInput
from googlecloudsdk.command_lib.scc.hooks import GetOrganization
from googlecloudsdk.command_lib.scc.hooks import GetOrganizationFromResourceName


def ListAssetsReqHook(ref, args, req):
  """Hook up filter such that the CSCC filter is used rather than gcloud."""
  del ref
  req.parent = GetOrganization(args)
  if req.fieldMask is not None:
    req.fieldMask = CleanUpUserInput(req.fieldMask)
  req.filter = args.filter
  args.filter = ""
  return req


def DescribeAssetReqHook(ref, args, req):
  """Generate organization name from organization id."""
  del ref
  req.parent = GetOrganization(args)
  req.filter = _GetNameOrResourceFilter(args)
  return req


def GetParentAssetReqHook(ref, args, req):
  """Generate organization name from organization id."""
  del ref
  req.parent = GetOrganization(args)
  req.filter = _GetNameOrResourceFilter(args)
  return req


def GetProjectAssetReqHook(ref, args, req):
  """Generate organization name from organization id."""
  del ref
  req.parent = GetOrganization(args)
  req.filter = _GetNameOrResourceFilter(args)
  return req


def GroupAssetsReqHook(ref, args, req):
  """Hook up filter such that the CSCC filter is used rather than gcloud."""
  del ref
  req.groupAssetsRequest.filter = args.filter
  args.filter = ""
  return req


def ListAssetSecurityMarksReqHook(ref, args, req):
  """Retrieves records for a specific asset."""
  del ref
  _ValidateMutexOnAssetAndOrganization(args)
  asset_name = _GetAssetName(args)
  req.parent = GetOrganizationFromResourceName(asset_name)
  req.filter = "name=\"" + asset_name + "\""
  return req


def UpdateAssetSecurityMarksReqHook(ref, args, req):
  """Generate a security mark's name using org, source and finding."""
  del ref
  _ValidateMutexOnAssetAndOrganization(args)
  req.name = _GetAssetName(args) + "/securityMarks"
  if req.updateMask is not None:
    req.updateMask = CleanUpUserInput(req.updateMask)
  return req


def _GetAssetName(args):
  """Prepares asset relative path using organization and asset."""
  resource_pattern = re.compile("organizations/[0-9]+/assets/[0-9]+")
  id_pattern = re.compile("[0-9]+")
  assert resource_pattern.match(args.asset) or id_pattern.match(args.asset), (
      "Asset must match either organizations/[0-9]+/assets/[0-9]+ or [0-9]+.")
  if resource_pattern.match(args.asset):
    # Handle asset id as full resource name
    return args.asset
  return GetOrganization(args) + "/assets/" + args.asset


def _GetNameOrResourceFilter(args):
  """Returns a filter with either name or resourceName as filter."""
  request_filter = ""
  if args.asset is not None:
    request_filter = "name=\"" + _GetAssetName(args) + "\""
  else:
    request_filter = "securityCenterProperties.resourceName=\"" + args.resource_name + "\""
  return request_filter


def _ValidateMutexOnAssetAndOrganization(args):
  """Validates that only a full resource name or split arguments are provided."""
  if "/" in args.asset:
    assert args.organization is None, (
        "Only provide a full resouce name "
        "(organizations/123/assets/456) or an --organization flag, not both.")
