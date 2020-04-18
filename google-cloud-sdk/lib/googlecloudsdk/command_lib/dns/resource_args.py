# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Shared resource flags for Cloud DNS commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.util import completers
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import properties


class PolicyCompleter(completers.ListCommandCompleter):

  def __init__(self, api_version, **kwargs):
    super(PolicyCompleter, self).__init__(
        collection='dns.policies',
        api_version=api_version,
        list_command='alpha dns policies list --format=value(name)',
        parse_output=True,
        **kwargs)


def PolicyAttributeConfig(api_version):
  return concepts.ResourceParameterAttributeConfig(
      name='policy',
      completer=PolicyCompleter(api_version=api_version),
      help_text='The Cloud DNS policy name {resource}.')


def ProjectAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='project',
      help_text='The Cloud project for the {resource}.',
      fallthroughs=[deps.PropertyFallthrough(properties.VALUES.core.project)])


def GetPolicyResourceSpec(api_version):
  return concepts.ResourceSpec(
      'dns.policies',
      api_version=api_version,
      resource_name='policy',
      policy=PolicyAttributeConfig(api_version=api_version),
      project=ProjectAttributeConfig())


def AddPolicyResourceArg(parser,
                         verb,
                         api_version,
                         positional=True,
                         required=True):
  """Add a resource argument for a Cloud DNS Policy.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
    api_version: str, the version of the API to use.
    positional: bool, if True, means that the policy name is a positional rather
      than a flag.
    required: bool, if True, means that the arg will be required.
  """
  if positional:
    name = 'policy'
  else:
    name = '--policy'
  concept_parsers.ConceptParser.ForResource(
      name,
      GetPolicyResourceSpec(api_version),
      'The policy {}.'.format(verb),
      required=required).AddToParser(parser)
