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
"""Declarative Request Hooks for Cloud SCC's Findings."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime
import re

from googlecloudsdk.api_lib.scc import securitycenter_client as sc_client
from googlecloudsdk.command_lib.scc.hooks import CleanUpUserInput
from googlecloudsdk.command_lib.scc.hooks import GetOrganization
from googlecloudsdk.command_lib.scc.hooks import GetSourceFromResourceName
from googlecloudsdk.core import properties


def CreateFindingsReqHook(ref, args, req):
  """Generate a finding's name and parent using org, source and finding."""
  del ref
  _ValidateMutexOnFindingAndSourceAndOrganization(args)
  finding_name = _GetFindingName(args)
  req.parent = GetSourceFromResourceName(finding_name)
  req.findingId = _GetFindingIdFromName(finding_name)
  messages = sc_client.GetMessages()
  if not req.finding:
    req.finding = messages.Finding()
  req.finding.name = finding_name
  return req


def ListFindingsReqHook(ref, args, req):
  """Generates a finding's parent using org and source and hook up filter."""
  del ref
  _ValidateMutexOnSourceAndOrganization(args)
  req.parent = _GetSourceName(args)
  req.filter = args.filter
  if req.fieldMask is not None:
    req.fieldMask = CleanUpUserInput(req.fieldMask)
  args.filter = ""
  resource_pattern = re.compile("organizations/[0-9]+/sources/[0-9-]+")
  if not args.organization:
    organization = properties.VALUES.scc.organization.Get()
  else:
    organization = args.organization
  if resource_pattern.match(organization):
    args.source = organization
  return req


def ListFindingsSecurityMarksReqHook(ref, args, req):
  """Generates a finding's parent and adds filter based on finding name."""
  del ref
  _ValidateMutexOnFindingAndSourceAndOrganization(args)
  finding_name = _GetFindingName(args)
  req.parent = GetSourceFromResourceName(finding_name)
  req.filter = "name=\"" + finding_name + "\""
  return req


def GroupFindingsReqHook(ref, args, req):
  """Generate a finding's name and parent using org, source and finding id."""
  del ref
  _ValidateMutexOnSourceAndOrganization(args)
  if not req.groupFindingsRequest:
    messages = sc_client.GetMessages()
    req.groupFindingsRequest = messages.GroupFindingsRequest()
  req.groupFindingsRequest.filter = args.filter
  args.filter = ""
  resource_pattern = re.compile("organizations/[0-9]+/sources/[0-9-]+")
  if not args.organization:
    organization = properties.VALUES.scc.organization.Get()
  else:
    organization = args.organization
  if resource_pattern.match(organization):
    args.source = organization
  req.parent = _GetSourceName(args)
  return req


def UpdateFindingsReqHook(ref, args, req):
  """Generate a finding's name using org, source and finding id."""
  del ref
  _ValidateMutexOnFindingAndSourceAndOrganization(args)
  req.name = _GetFindingName(args)
  req.updateMask = CleanUpUserInput(req.updateMask)
  # All requests require an event time
  if args.event_time is None:
    # Formatting: 2019-03-22 21:24:36.208463 -> 2019-03-22T21:33:15.830Z"
    event_time = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    if req.finding is None:
      req.finding = sc_client.GetMessages().Finding()
    req.finding.eventTime = event_time
    req.updateMask = req.updateMask + ",event_time"
  return req


def UpdateFindingSecurityMarksReqHook(ref, args, req):
  """Generate a security mark's name using org, source and finding id."""
  del ref
  _ValidateMutexOnFindingAndSourceAndOrganization(args)
  req.name = _GetFindingName(args) + "/securityMarks"
  if req.updateMask is not None:
    req.updateMask = CleanUpUserInput(req.updateMask)
  return req


def _GetFindingName(args):
  """Returns relative resource name for a finding name."""
  resource_pattern = re.compile(
      "organizations/[0-9]+/sources/[0-9-]+/findings/[a-zA-Z0-9]+")
  id_pattern = re.compile("[a-zA-Z0-9]+")
  assert resource_pattern.match(args.finding) or id_pattern.match(
      args.finding), (
          "Finding must match either organizations/"
          "[0-9]+/sources/[0-9-]+/findings/[a-zA-Z0-9]+ or [0-9]+.")
  if resource_pattern.match(args.finding):
    # Handle finding id as full resource name
    return args.finding
  return _GetSourceName(args) + "/findings/" + args.finding


def _GetSourceName(args):
  """Returns relative resource name for a source."""
  resource_pattern = re.compile("organizations/[0-9]+/sources/[0-9-]+")
  id_pattern = re.compile("[0-9-]+")
  assert resource_pattern.match(args.source) or id_pattern.match(args.source), (
      "Source must match either organizations/[0-9]+/sources/[0-9-]+ "
      "or [0-9-]+.")
  if resource_pattern.match(args.source):
    # Handle full resource name
    return args.source
  return GetOrganization(args) + "/sources/" + args.source


def _GetFindingIdFromName(finding_name):
  """Gets a finding id from the full resource name."""
  resource_pattern = re.compile(
      "organizations/[0-9]+/sources/[0-9-]+/findings/[a-zA-Z0-9]+")
  assert resource_pattern.match(finding_name), (
      "When providing a full resource path, it must include the pattern "
      "organizations/[0-9]+/sources/[0-9-]+/findings/[a-zA-Z0-9]+.")
  list_finding_components = finding_name.split("/")
  return list_finding_components[len(list_finding_components) - 1]


def _ValidateMutexOnSourceAndOrganization(args):
  """Validates that only a full resource name or split arguments are provided."""
  if "/" in args.source:
    assert args.organization is None, (
        "Only provide a full resouce name "
        "(organizations/123/sources/456) or an --organization flag, not both.")


def _ValidateMutexOnFindingAndSourceAndOrganization(args):
  """Validates that only a full resource name or split arguments are provided."""
  if "/" in args.finding:
    assert args.organization is None, (
        "Only provide a full resouce name "
        "(organizations/123/sources/456/findings/789) or an --organization "
        "flag and --sources flag, not both.")
    assert args.source is None, (
        "Only provide a full resouce name "
        "(organizations/123/sources/456/findings/789) or an --organization flag"
        " and --sources flag, not both.")
