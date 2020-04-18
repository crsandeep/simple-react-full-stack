# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Flags for workflow templates related commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import properties


def _RegionAttributeConfig():
  fallthroughs = [deps.PropertyFallthrough(properties.VALUES.dataproc.region)]
  return concepts.ResourceParameterAttributeConfig(
      name='region',
      help_text=(
          'Dataproc region for the {resource}. Each Dataproc '
          'region constitutes an independent resource namespace constrained to '
          'deploying instances into Compute Engine zones inside the '
          'region. Overrides the default `dataproc/region` property '
          'value for this command invocation.'),
      fallthroughs=fallthroughs)


def AddRegionFlag(parser):
  region_prop = properties.VALUES.dataproc.region
  parser.add_argument(
      '--region',
      help=region_prop.help_text,
      # Don't set default, because it would override users' property setting.
      action=actions.StoreProperty(region_prop))


def ClusterConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='cluster',
      help_text='The Cluster name.',
  )


def _GetClusterResourceSpec(api_version):
  return concepts.ResourceSpec(
      'dataproc.projects.regions.clusters',
      api_version=api_version,
      resource_name='cluster',
      disable_auto_completers=True,
      projectId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      region=_RegionAttributeConfig(),
      clusterName=ClusterConfig(),
  )


def AddClusterResourceArg(parser, verb, api_version):
  concept_parsers.ConceptParser.ForResource(
      'cluster',
      _GetClusterResourceSpec(api_version),
      'The name of the cluster to {}.'.format(verb),
      required=True).AddToParser(parser)


def AddZoneFlag(parser, short_flags=True):
  """Add zone flag."""
  parser.add_argument(
      '--zone',
      *(['-z'] if short_flags else []),
      help="""
            The compute zone (e.g. us-central1-a) for the cluster. If empty
            and --region is set to a value other than `global`, the server will
            pick a zone in the region.
            """,
      action=actions.StoreProperty(properties.VALUES.compute.zone))


def AddVersionFlag(parser):
  parser.add_argument(
      '--version', type=int, help='The version of the workflow template.')


def AddFileFlag(parser, input_type, action):
  # Examples: workflow template to run/export/import, cluster to create.
  parser.add_argument(
      '--file',
      help='The YAML file containing the {0} to {1}'.format(input_type, action),
      required=True)


def JobConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='job',
      help_text='The Job ID.',
  )


def _GetJobResourceSpec(api_version):
  return concepts.ResourceSpec(
      'dataproc.projects.regions.jobs',
      api_version=api_version,
      resource_name='job',
      disable_auto_completers=True,
      projectId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      region=_RegionAttributeConfig(),
      jobId=JobConfig(),
  )


def AddJobResourceArg(parser, verb, api_version):
  concept_parsers.ConceptParser.ForResource(
      'job',
      _GetJobResourceSpec(api_version),
      'The ID of the job to {0}.'.format(verb),
      required=True).AddToParser(parser)


def OperationConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='operation',
      help_text='The Operation ID.',
  )


def _GetOperationResourceSpec(api_version):
  return concepts.ResourceSpec(
      'dataproc.projects.regions.operations',
      api_version=api_version,
      resource_name='operation',
      disable_auto_completers=True,
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      regionsId=_RegionAttributeConfig(),
      operationsId=OperationConfig(),
  )


def AddOperationResourceArg(parser, verb, api_version):
  name = 'operation'
  concept_parsers.ConceptParser.ForResource(
      name,
      _GetOperationResourceSpec(api_version),
      'The ID of the operation to {0}.'.format(verb),
      required=True).AddToParser(parser)


def AddTimeoutFlag(parser, default='10m'):
  # This may be made visible or passed to the server in future.
  parser.add_argument(
      '--timeout',
      type=arg_parsers.Duration(),
      default=default,
      help=('Client side timeout on how long to wait for Dataproc operations. '
            'See $ gcloud topic datetimes for information on duration '
            'formats.'),
      hidden=True)


def AddParametersFlag(parser):
  parser.add_argument(
      '--parameters',
      metavar='PARAM=VALUE',
      type=arg_parsers.ArgDict(),
      help="""
          A map from parameter names to values that should be used for those
          parameters. A value must be provided for every configured parameter.
          Parameters can be configured when creating or updating a workflow
          template.
          """,
      dest='parameters')


def AddMinCpuPlatformArgs(parser):
  """Add mininum CPU platform flags for both master and worker instances."""
  help_text = """\
      When specified, the VM will be scheduled on host with specified CPU
      architecture or a newer one. To list available CPU platforms in given
      zone, run:

          $ gcloud compute zones describe ZONE

      CPU platform selection is available only in selected zones; zones that
      allow CPU platform selection will have an `availableCpuPlatforms` field
      that contains the list of available CPU platforms for that zone.

      You can find more information online:
      https://cloud.google.com/compute/docs/instances/specify-min-cpu-platform
      """
  parser.add_argument(
      '--master-min-cpu-platform',
      metavar='PLATFORM',
      required=False,
      help=help_text)
  parser.add_argument(
      '--worker-min-cpu-platform',
      metavar='PLATFORM',
      required=False,
      help=help_text)


def AddComponentFlag(parser):
  """Add optional components flag."""
  help_text = """\
      List of optional components to be installed on cluster machines.

      The following page documents the optional components that can be
      installed:
      https://cloud.google.com/dataproc/docs/concepts/configuring-clusters/optional-components.
      """
  parser.add_argument(
      '--optional-components',
      metavar='COMPONENT',
      type=arg_parsers.ArgList(element_type=lambda val: val.upper()),
      dest='components',
      help=help_text)


def TemplateAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='template',
      help_text='The workflow template name.',
  )


def _GetTemplateResourceSpec(api_version):
  return concepts.ResourceSpec(
      'dataproc.projects.regions.workflowTemplates',
      api_version=api_version,
      resource_name='template',
      disable_auto_completers=True,
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      regionsId=_RegionAttributeConfig(),
      workflowTemplatesId=TemplateAttributeConfig(),
  )


def AddTemplateResourceArg(parser, verb, api_version, positional=True):
  """Adds a workflow template resource argument.

  Args:
    parser: the argparse parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
    api_version: api version, for example v1 or v1beta2
    positional: bool, if True, means that the instance ID is a positional rather
      than a flag.
  """
  name = 'template' if positional else '--workflow-template'
  concept_parsers.ConceptParser.ForResource(
      name,
      _GetTemplateResourceSpec(api_version),
      'The name of the workflow template to {}.'.format(verb),
      required=True).AddToParser(parser)


def _AutoscalingPolicyResourceSpec(api_version):
  return concepts.ResourceSpec(
      'dataproc.projects.regions.autoscalingPolicies',
      api_version=api_version,
      resource_name='autoscaling policy',
      disable_auto_completers=True,
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      regionsId=_RegionAttributeConfig(),
      autoscalingPoliciesId=concepts.ResourceParameterAttributeConfig(
          name='autoscaling_policy',
          help_text='The autoscaling policy id.',
      ),
  )


def AddAutoscalingPolicyResourceArg(parser, verb, api_version):
  """Adds a workflow template resource argument.

  Args:
    parser: the argparse parser for the command.
    verb: str, the verb to apply to the resource, such as 'to update'.
    api_version: api version, for example v1 or v1beta2
  """
  concept_parsers.ConceptParser.ForResource(
      'autoscaling_policy',
      _AutoscalingPolicyResourceSpec(api_version),
      'The autoscaling policy to {}.'.format(verb),
      required=True).AddToParser(parser)


def AddAutoscalingPolicyResourceArgForCluster(parser, api_version):
  """Adds a workflow template resource argument.

  Args:
    parser: the argparse parser for the command.
    api_version: api version, for example v1 or v1beta2
  """
  concept_parsers.ConceptParser.ForResource(
      '--autoscaling-policy',
      _AutoscalingPolicyResourceSpec(api_version),
      'The autoscaling policy to use.',
      command_level_fallthroughs={
          'region': ['--region'],
      },
      flag_name_overrides={
          'region': ''
      },
      required=False).AddToParser(parser)


def AddListOperationsFormat(parser):
  parser.display_info.AddTransforms({
      'operationState': _TransformOperationState,
      'operationTimestamp': _TransformOperationTimestamp,
      'operationType': _TransformOperationType,
      'operationWarnings': _TransformOperationWarnings,
  })
  parser.display_info.AddFormat('table(name.segment():label=NAME, '
                                'metadata.operationTimestamp():label=TIMESTAMP,'
                                'metadata.operationType():label=TYPE, '
                                'metadata.operationState():label=STATE, '
                                'status.code.yesno(no=\'\'):label=ERROR, '
                                'metadata.operationWarnings():label=WARNINGS)')


def _TransformOperationType(metadata):
  """Extract operation type from metadata."""
  if 'operationType' in metadata:
    return metadata['operationType']
  elif 'graph' in metadata:
    return 'WORKFLOW'
  return ''


def _TransformOperationState(metadata):
  """Extract operation state from metadata."""
  if 'status' in metadata:
    return metadata['status']['state']
  elif 'state' in metadata:
    return metadata['state']
  return ''


def _TransformOperationTimestamp(metadata):
  """Extract operation start timestamp from metadata."""
  if 'statusHistory' in metadata:
    return metadata['statusHistory'][0]['stateStartTime']
  elif 'startTime' in metadata:
    return metadata['startTime']
  return ''


def _TransformOperationWarnings(metadata):
  """Returns a count of operations if any are present."""
  if 'warnings' in metadata:
    return len(metadata['warnings'])
  return ''
