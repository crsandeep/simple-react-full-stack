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
"""Shared resource flags for Events commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.run import resource_args as run_resource_args


def TriggerAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='trigger',
      help_text='Name of the trigger.')


def GetTriggerResourceSpec():
  return concepts.ResourceSpec(
      'run.namespaces.triggers',
      namespacesId=run_resource_args.NamespaceAttributeConfig(),
      triggersId=TriggerAttributeConfig(),
      resource_name='Trigger')


def GetCoreNamespaceResourceSpec():
  """Returns a resource spec for namespace core api, rather than just run.namespaces."""
  return concepts.ResourceSpec(
      'run.api.v1.namespaces',
      namespacesId=run_resource_args.NamespaceAttributeConfig(),
      resource_name='namespace',
      api_version='v1')
