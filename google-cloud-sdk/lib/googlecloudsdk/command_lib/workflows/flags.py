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
"""Shared flags for Cloud Workflows commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import exceptions
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files


def LocationAttributeConfig():
  """Builds an AttributeConfig for the location resource."""
  return concepts.ResourceParameterAttributeConfig(
      name='location',
      fallthroughs=[
          deps.PropertyFallthrough(properties.FromString('workflows/location'))
      ],
      help_text='Cloud location for the {resource}. '
      ' Alternatively, set the property [workflows/location].')


def WorkflowAttributeConfig():
  """Builds an AttributeConfig for the workflow resource."""
  return concepts.ResourceParameterAttributeConfig(
      name='workflow', help_text='Workflow for the {resource}.')


def GetWorkflowResourceSpec():
  """Builds a ResourceSpec for the workflow resource."""
  return concepts.ResourceSpec(
      'workflows.projects.locations.workflows',
      resource_name='workflow',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=LocationAttributeConfig(),
      workflowsId=WorkflowAttributeConfig())


def AddWorkflowResourceArg(parser, verb):
  """Add a resource argument for a Cloud Workflows workflow.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
  """
  concept_parsers.ConceptParser.ForResource(
      'workflow',
      GetWorkflowResourceSpec(),
      'Name of the workflow {}.'.format(verb),
      required=True).AddToParser(parser)


def AddSourceArg(parser):
  """Adds argument for specifying source for the workflow."""
  parser.add_argument(
      '--source',
      help='Location of a workflow source code to deploy. Required on first '
      'deployment. Location needs to be defined as a path to a local file '
      'with the source code.')


def AddDescriptionArg(parser):
  """Adds argument for specifying description of the workflow."""
  parser.add_argument(
      '--description', help='The description of the workflow to deploy.')


def AddServiceAccountArg(parser):
  """Adds argument for specifying service account used by the workflow."""
  parser.add_argument(
      '--service-account', help='The service account that should be used as '
      'the workflow identity. "projects/PROJECT_ID/serviceAccounts/" prefix '
      'may be skipped from the full resource name, in that case '
      '"projects/-/serviceAccounts/" is prepended to the service account ID.')


def ParseWorkflow(args):
  """Get and validate workflow from the args."""
  return args.CONCEPTS.workflow.Parse()


def SetSource(args, workflow, updated_fields):
  """Set source for the workflow based on the arguments.

  Also update updated_fields accordingly.
  Currently only local source file is supported.

  Args:
    args: args passed to the command.
    workflow: the workflow in which to set the source configuration.
    updated_fields: a list to which an appropriate source field will be added.
  """
  if args.source:
    try:
      workflow.sourceContents = files.ReadFileContents(args.source)
    except files.MissingFileError:
      raise exceptions.BadArgumentException('--source',
                                            'specified file does not exist.')
    updated_fields.append('sourceContents')


def SetDescription(args, workflow, updated_fields):
  """Set description for the workflow based on the arguments.

  Also update updated_fields accordingly.

  Args:
    args: args passed to the command.
    workflow: the workflow in which to set the description.
    updated_fields: a list to which a description field will be added if needed.
  """
  if args.description is not None:
    workflow.description = args.description
    updated_fields.append('description')


def SetServiceAccount(args, workflow, updated_fields):
  """Set service account for the workflow based on the arguments.

  Also update updated_fields accordingly.

  Args:
    args: args passed to the command.
    workflow: the workflow in which to set the service account.
    updated_fields: a list to which a service_account field will be added
    if needed.
  """
  if args.service_account is not None:
    prefix = ''
    if not args.service_account.startswith('projects/'):
      prefix = 'projects/-/serviceAccounts/'
    workflow.serviceAccount = prefix + args.service_account
    updated_fields.append('serviceAccount')


def SetLabels(labels, workflow, updated_fields):
  """Set labels for the workflow based on the arguments.

  Also update updated_fields accordingly.

  Args:
    labels: labels parsed as string to be set on the workflow, or None in case
      the field shouldn't be set.
    workflow: the workflow in which to set the labels.
    updated_fields: a list to which a labels field will be added if needed.
  """
  if labels is not None:
    workflow.labels = labels
    updated_fields.append('labels')
