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
"""Utilities for the Label Manager server."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis

LABEL_MANAGER_API_NAME = 'labelmanager'
LABEL_MANAGER_API_VERSION = 'v1alpha1'


def LabelManagerClient():
  """Returns a client instance of the Label Manager service."""
  return apis.GetClientInstance(LABEL_MANAGER_API_NAME,
                                LABEL_MANAGER_API_VERSION)


def LabelManagerMessages():
  """Returns the messages module for the Label Manager service."""
  return apis.GetMessagesModule(LABEL_MANAGER_API_NAME,
                                LABEL_MANAGER_API_VERSION)


def LabelKeysService():
  """Returns the label keys service class."""
  client = LabelManagerClient()
  return client.labelKeys


def LabelValuesService():
  """Returns the label values service class."""
  client = LabelManagerClient()
  return client.labelValues


def LabelBindingsService():
  """Returns the label bindings service class."""
  client = LabelManagerClient()
  return client.labelBindings


def OperationsService():
  """Returns the operations service class."""
  client = LabelManagerClient()
  return client.operations
