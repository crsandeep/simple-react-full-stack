# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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
"""Common utility functions for the dns tool."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources


def AppendTrailingDot(name):
  return name if not name or name.endswith('.') else name + '.'


def GetRegistry(version):
  registry = resources.REGISTRY.Clone()
  registry.RegisterApiByName('dns', version)
  return registry


def GetApiFromTrack(track):
  if track == base.ReleaseTrack.BETA:
    return 'v1beta2'
  if track == base.ReleaseTrack.ALPHA:
    return 'v1alpha2'
  if track == base.ReleaseTrack.GA:
    return 'v1'


def GetApiClient(version):
  return apis.GetClientInstance('dns', version, use_google_auth=True)
