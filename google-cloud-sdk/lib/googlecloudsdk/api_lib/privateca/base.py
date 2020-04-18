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
"""Shared utilities for accessing the Private CA API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis

import six.moves.urllib.parse


def GetClientClass():
  return apis.GetClientClass('privateca', 'v1alpha1')


def GetClientInstance():
  return apis.GetClientInstance('privateca', 'v1alpha1')


def GetMessagesModule():
  return apis.GetMessagesModule('privateca', 'v1alpha1')


def GetServiceName():
  """Gets the service name based on the configured API endpoint."""
  endpoint = apis.GetEffectiveApiEndpoint('privateca', 'v1alpha1')
  return six.moves.urllib.parse.urlparse(endpoint).hostname
