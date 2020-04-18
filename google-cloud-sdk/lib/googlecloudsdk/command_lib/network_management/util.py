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
"""Utilities for `gcloud network-management`."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.core import exceptions


class NetworkManagementError(exceptions.Error):
  """Top-level exception for all Network Management errors."""


class InvalidInputError(NetworkManagementError):
  """Exception for invalid input."""


def AppendLocationsGlobalToParent(unused_ref, unused_args, request):
  """Add locations/global to parent path, since it isn't automatically populated by apitools."""
  request.parent += "/locations/global"
  return request


def UpdateOperationRequestNameVariable(unused_ref, unused_args, request):
  request.name += "/locations/global"
  return request


def AddFieldToUpdateMask(field, patch_request):
  """Adds name of field to update mask."""
  update_mask = patch_request.updateMask
  if not update_mask:
    patch_request.updateMask = field
  elif field not in update_mask:
    patch_request.updateMask = update_mask + "," + field
  return patch_request


def ClearSingleEndpointAttr(patch_request, endpoint_type, endpoint_name):
  """Checks if given endpoint can be removed from Connectivity Test and removes it."""
  alt_endpoint_name = "instance" if endpoint_name == "ipAddress" else "ipAddress"
  test = patch_request.connectivityTest
  endpoints = getattr(test, endpoint_type)

  if getattr(endpoints, alt_endpoint_name, None):
    setattr(endpoints, endpoint_name, "")
    setattr(test, endpoint_type, endpoints)
    patch_request.connectivityTest = test
    return AddFieldToUpdateMask(endpoint_type + "." + endpoint_name,
                                patch_request)
  else:
    raise InvalidInputError(
        "Invalid Connectivity Test. At least one of --{}-instance or --{}-ip-address must be specified."
        .format(endpoint_type, endpoint_type))


def ClearEndpointAttrs(unused_ref, args, patch_request):
  """Handles clear_source_* and clear_destination_* flags."""
  flags_and_endpoints = [
      ("clear_source_instance", "source", "instance"),
      ("clear_source_ip_address", "source", "ipAddress"),
      ("clear_destination_instance", "destination", "instance"),
      ("clear_destination_ip_address", "destination", "ipAddress")
  ]

  for flag, endpoint_type, endpoint_name in flags_and_endpoints:
    if args.IsSpecified(flag):
      patch_request = ClearSingleEndpointAttr(
          patch_request,
          endpoint_type,
          endpoint_name,
      )

  return patch_request


def ValidateInstanceNames(unused_ref, args, request):
  """Checks if all provided instances are in valid format."""
  flags = [
      "source_instance",
      "destination_instance",
  ]
  instance_pattern = re.compile(
      r"projects/(?:[a-z][a-z0-9-]*[a-z0-9]|[a-z])/zones/[-\w]+/instances/[-\w]+"
  )
  for flag in flags:
    if args.IsSpecified(flag):
      instance = getattr(args, flag)
      if not instance_pattern.match(instance):
        raise InvalidInputError(
            "Invalid value for flag {}: {}\n"
            "Expected instance in the following format:\n"
            "  projects/my-project/zones/zone/instances/my-instance".format(
                flag, instance))

  return request


def ValidateNetworkURIs(unused_ref, args, request):
  """Checks if all provided networks are in valid format."""
  flags = [
      "source_network",
      "destination_network",
  ]
  network_pattern = re.compile(
      r"projects/(?:[a-z][a-z0-9-]*[a-z0-9]|[a-z])/global/networks/[-\w]+")
  for flag in flags:
    if args.IsSpecified(flag):
      network = getattr(args, flag)
      if not network_pattern.match(network):
        raise InvalidInputError(
            "Invalid value for flag {}: {}\n"
            "Expected network in the following format:\n"
            "  projects/my-project/global/networks/my-network".format(
                flag, network))

  return request
