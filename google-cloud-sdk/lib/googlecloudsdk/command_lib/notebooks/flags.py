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
"""Utilities for flags for `gcloud tasks` commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.compute.networks import flags as compute_network_flags
from googlecloudsdk.command_lib.compute.networks.subnets import flags as compute_subnet_flags
from googlecloudsdk.command_lib.kms import resource_args as kms_resource_args
from googlecloudsdk.command_lib.notebooks import completers
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import properties


def GetEnvironmentResourceArg(help_text, positional=True, required=True):
  """Constructs and returns the Environment Resource Argument."""

  def GetEnvironmentResourceSpec():
    """Constructs and returns the Resource specification for Environment."""

    def EnvironmentAttributeConfig():
      return concepts.ResourceParameterAttributeConfig(
          name='environment', help_text=help_text)

    def LocationAttributeConfig():
      return concepts.ResourceParameterAttributeConfig(
          name='{}location'.format('' if positional else 'environment-'),
          help_text=(
              'Google Cloud location of this environment '
              'https://cloud.google.com/compute/docs/regions-zones/#locations.'
          ),
          completer=completers.LocationCompleter,
          fallthroughs=[
              deps.ArgFallthrough('--location'),
              deps.PropertyFallthrough(properties.VALUES.notebooks.location)
          ],
      )

    return concepts.ResourceSpec(
        'notebooks.projects.locations.environments',
        resource_name='environment',
        environmentsId=EnvironmentAttributeConfig(),
        locationsId=LocationAttributeConfig(),
        projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
        disable_auto_completers=False)

  return concept_parsers.ConceptParser.ForResource(
      '{}environment'.format('' if positional else '--'),
      GetEnvironmentResourceSpec(),
      help_text,
      required=required)


def AddListEnvironmentFlags(parser):
  parser.add_argument(
      '--location',
      completer=completers.LocationCompleter,
      help=('Google Cloud location of this environment: '
            'https://cloud.google.com/compute/docs/regions-zones/#locations.'))


def AddCreateEnvironmentFlags(parser):
  """Construct groups and arguments specific to the environment create."""
  source_group = parser.add_group(mutex=True, required=True)
  vm_source_group = source_group.add_group()
  vm_mutex_group = vm_source_group.add_group(mutex=True, required=True)
  container_group = source_group.add_group()
  GetEnvironmentResourceArg(
      ('User-defined unique name of this environment. The environment name '
       'must be 1 to 63 characters long and contain only lowercase letters, '
       'numeric characters, and dashes. The first character must be a lowercase'
       'letter and the last character cannot be a dash.')).AddToParser(parser)
  parser.add_argument(
      '--description', help='A brief description of this environment.')
  parser.add_argument('--display-name', help='Name to display on the UI.')
  parser.add_argument(
      '--post-startup-script',
      help=(
          'Path to a Bash script that automatically runs after a notebook '
          'instance fully boots up. The path must be a URL or Cloud Storage path'
          '(gs://`path-to-file/`file-name`).'))
  base.ASYNC_FLAG.AddToParser(parser)
  vm_source_group.add_argument(
      '--vm-image-project',
      help=('The ID of the Google Cloud project that this VM image belongs to.'
            'Format: projects/`{project_id}`.'),
      required=True)
  vm_mutex_group.add_argument(
      '--vm-image-name', help='Use this VM image name to find the image.')
  vm_mutex_group.add_argument(
      '--vm-image-family',
      help=('Use this VM image family to find the image; the newest image in '
            'this family will be used.'))
  container_group.add_argument(
      '--container-repository',
      help=('The path to the container image repository. For example: '
            'gcr.io/`{project_id}`/`{image_name}`.'),
      required=True)
  container_group.add_argument(
      '--container-tag',
      help='The tag of the container image. If not specified, this defaults to the latest tag.'
  )


def AddDeleteEnvironmentFlags(parser):

  GetEnvironmentResourceArg(
      ('User-defined unique name of this environment. The environment name '
       'must be 1 to 63 characters long and contain only lowercase letters, '
       'numeric characters, and dashes. The first character must be a lowercase'
       'letter and the last character cannot be a dash.')).AddToParser(parser)
  base.ASYNC_FLAG.AddToParser(parser)


def AddDescribeEnvironmentFlags(parser):
  GetEnvironmentResourceArg(
      ('User-defined unique name of this environment. The environment name '
       'must be 1 to 63 characters long and contain only lowercase letters, '
       'numeric characters, and dashes. The first character must be a lowercase'
       'letter and the last character cannot be a dash.')).AddToParser(parser)


def GetInstanceResourceArg(help_text):
  """Constructs and returns the Instance Resource Argument."""

  def GetInstanceResourceSpec():
    """Constructs and returns the Resource specification for Instance."""

    def InstanceAttributeConfig():
      return concepts.ResourceParameterAttributeConfig(
          name='instance', help_text=help_text)

    def LocationAttributeConfig():
      return concepts.ResourceParameterAttributeConfig(
          name='location',
          help_text=(
              'Google Cloud location of this environment '
              'https://cloud.google.com/compute/docs/regions-zones/#locations.'
          ),
          fallthroughs=[
              deps.PropertyFallthrough(properties.VALUES.notebooks.location),
          ],
      )

    return concepts.ResourceSpec(
        'notebooks.projects.locations.instances',
        resource_name='instance',
        instancesId=InstanceAttributeConfig(),
        locationsId=LocationAttributeConfig(),
        projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
        disable_auto_completers=False)

  return concept_parsers.ConceptParser.ForResource(
      'instance', GetInstanceResourceSpec(), help_text, required=True)


def AddNetworkArgument(help_text, parser):
  """Adds Resource arg for network to the parser."""

  def GetNetworkResourceSpec():
    """Constructs and returns the Resource specification for Subnet."""

    def NetworkAttributeConfig():
      return concepts.ResourceParameterAttributeConfig(
          name='network',
          help_text=help_text,
          completer=compute_network_flags.NetworksCompleter)

    return concepts.ResourceSpec(
        'compute.networks',
        resource_name='network',
        network=NetworkAttributeConfig(),
        project=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
        disable_auto_completers=False)

  concept_parsers.ConceptParser.ForResource('--network',
                                            GetNetworkResourceSpec(),
                                            help_text).AddToParser(parser)


def AddSubnetArgument(help_text, parser):
  """Adds Resource arg for subnetwork to the parser."""

  def GetSubnetResourceSpec():
    """Constructs and returns the Resource specification for Subnet."""

    def SubnetAttributeConfig():
      return concepts.ResourceParameterAttributeConfig(
          name='subnet',
          help_text=help_text,
          completer=compute_subnet_flags.SubnetworksCompleter)

    def RegionAttributeConfig():
      return concepts.ResourceParameterAttributeConfig(
          name='subnet-region',
          help_text=(
              'Google Cloud region of this subnetwork '
              'https://cloud.google.com/compute/docs/regions-zones/#locations.'
          ),
          completer=completers.RegionCompleter)

    return concepts.ResourceSpec(
        'compute.subnetworks',
        resource_name='subnetwork',
        subnetwork=SubnetAttributeConfig(),
        region=RegionAttributeConfig(),
        project=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
        disable_auto_completers=False)

  concept_parsers.ConceptParser.ForResource('--subnet', GetSubnetResourceSpec(),
                                            help_text).AddToParser(parser)


def AddInstanceResource(parser, add_async_flag=True):
  GetInstanceResourceArg(
      ('User-defined unique name of this instance. The instance name must be '
       '1 to 63 characters long and contain only lowercase letters, numeric '
       'characters, and dashes. The first character must be a lowercase letter '
       'and the last character cannot be a dash.')).AddToParser(parser)
  if add_async_flag:
    base.ASYNC_FLAG.AddToParser(parser)


def AddCreateInstanceFlags(parser):
  """Construct groups and arguments specific to the instance creation."""
  accelerator_choices = [
      'NVIDIA_TESLA_K80', 'NVIDIA_TESLA_P100', 'NVIDIA_TESLA_V100',
      'NVIDIA_TESLA_P4', 'NVIDIA_TESLA_T4', 'NVIDIA_TESLA_T4_VWS',
      'NVIDIA_TESLA_P100_VWS', 'NVIDIA_TESLA_P4_VWS', 'TPU_V2', 'TPU_V3'
  ]
  boot_disk_choices = ['PD_STANDARD', 'PD_SSD']
  encryption_choices = ['GMEK', 'CMEK']
  AddInstanceResource(parser)
  environment_group = parser.add_group(mutex=True, required=True)
  GetEnvironmentResourceArg((
      'User-defined unique name of this environment. The environment name '
      'must be 1 to 63 characters long and contain only lowercase letters, '
      'numeric characters, and dashes. The first character must be a lowercase '
      'letter and the last character cannot be a dash.'),
                            positional=False,
                            required=False).AddToParser(environment_group)
  vm_source_group = environment_group.add_group()
  vm_mutex_group = vm_source_group.add_group(mutex=True, required=True)
  container_group = environment_group.add_group()
  vm_source_group.add_argument(
      '--vm-image-project',
      help=('The ID of the Google Cloud project that this VM image belongs to. '
            'Format: projects/`{project_id}`.'),
      required=True)
  vm_mutex_group.add_argument(
      '--vm-image-name', help='Use this VM image name to find the image.')
  vm_mutex_group.add_argument(
      '--vm-image-family',
      help=('Use this VM image family to find the image; the newest image '
            'in this family will be used.'))
  container_group.add_argument(
      '--container-repository',
      help=('The path to the container image repository. '
            'For example: gcr.io/`{project_id}`/`{image_name}`.'),
      required=True)
  container_group.add_argument(
      '--container-tag',
      help=('The tag of the container image. If not specified, '
            'this defaults to the latest tag.'))
  parser.add_argument(
      '--post-startup-script',
      help=(
          'Path to a Bash script that automatically runs after a notebook '
          'instance fully boots up. The path must be a URL or Cloud Storage path '
          '(gs://`path-to-file`/`file-name`).'))
  parser.add_argument(
      '--service-account',
      help=(
          'The service account on this instance, giving access to other '
          'Google Cloud services. You can use any service account within the '
          'same project, but you must have the service account user permission '
          'to use the instance. If not specified, the [Compute Engine default '
          'service account](/compute/docs/access/service-accounts#default_'
          'service_account) is used.'))
  parser.add_argument(
      '--machine-type',
      help='The [Compute Engine machine type](/compute/docs/machine-types) of this instance.',
      required=True)
  parser.add_argument(
      '--instance-owners',
      help=(
          'The owners of this instance after creation. Format: '
          '`alias@example.com`. Currently supports one owner only. If not specified'
          ", all of the service account users of the VM instance\'s service "
          'account can use the instance.'))
  accelerator_group = parser.add_group(
      help=(
          'The hardware accelerator used on this instance. If you use '
          'accelerators, make sure that your configuration has [enough vCPUs and '
          'memory to support the `machine_type` you have selected](/compute/'
          'docs/gpus/#gpus-list).'))
  accelerator_group.add_argument(
      '--accelerator-type',
      help='Type of this accelerator.',
      choices=accelerator_choices,
      default=None)
  accelerator_group.add_argument(
      '--accelerator-core-count',
      help='Count of cores of this accelerator.',
      type=int)
  gpu_group = parser.add_group(help='GPU driver configurations.')
  gpu_group.add_argument(
      '--install-gpu-driver',
      action='store_true',
      dest='install_gpu_driver',
      help=(
          'Whether the end user authorizes Google Cloud to install a GPU '
          'driver on this instance. If this field is empty or set to false, the '
          'GPU driver won\'t be installed. Only applicable to instances with GPUs.'
      ))
  gpu_group.add_argument(
      '--custom-gpu-driver-path',
      help=(
          'Specify a custom Cloud Storage path where the GPU driver is '
          'stored. If not specified, we\'ll automatically choose from official '
          'GPU drivers.'))
  boot_group = parser.add_group(help='Boot disk configurations.')
  boot_group.add_argument(
      '--boot-disk-type',
      choices=boot_disk_choices,
      default=None,
      help=('The type of disk attached to this instance, defaults to standard '
            'persistent disk (`PD_STANDARD`).'))
  boot_group.add_argument(
      '--boot-disk-size',
      type=int,
      help=('The size of the disk in GB attached to this instance, up to a '
            'maximum of 64000 GB (64 TB). The minimum recommended value '
            'is 100 GB. If not specified, this defaults to 100.'))
  encryption_group = parser.add_group(help='Disk encryption configurations.')
  encryption_group.add_argument(
      '--disk-encryption',
      choices=encryption_choices,
      default=None,
      help='Disk encryption method used on the boot disk, defaults to GMEK.')
  kms_resource_args.AddKmsKeyResourceArg(encryption_group, 'instance')
  network_group = parser.add_group(help='Network configs.')
  network_group.add_argument(
      '--no-public-ip',
      action='store_true',
      dest='no_public_ip',
      help="""\
  If specified, no public IP will be assigned to this instance.""")
  network_group.add_argument(
      '--no-proxy-access',
      action='store_true',
      dest='no_proxy_access',
      help="""\
  If true, the notebook instance will not register with the proxy.""")

  AddNetworkArgument(
      ('The name of the VPC that this instance is in. Format: '
       'projects/`{project_id}`/global/networks/`{network_id}`.'),
      network_group)
  AddSubnetArgument(
      ('The name of the subnet that this instance is in. Format: projects/'
       '`{project_id}`/regions/`{region}`/subnetworks/`{subnetwork_id}`.'),
      network_group)
  parser.add_argument(
      '--labels',
      help=('Labels to apply to this instance. These can be later modified '
            'by the setLabels method.'),
      type=arg_parsers.ArgDict(),
      metavar='KEY=VALUE')
  parser.add_argument(
      '--metadata',
      help='Custom metadata to apply to this instance.',
      type=arg_parsers.ArgDict(),
      metavar='KEY=VALUE')


def AddDescribeInstanceFlags(parser):
  AddInstanceResource(parser, add_async_flag=False)


def AddDeleteInstanceFlags(parser):
  AddInstanceResource(parser)


def AddListInstanceFlags(parser):
  parser.add_argument(
      '--location',
      completer=completers.LocationCompleter,
      help=('Google Cloud location of this environment '
            'https://cloud.google.com/compute/docs/regions-zones/#locations.'))


def AddRegisterInstanceFlags(parser):
  AddInstanceResource(parser)


def AddResetInstanceFlags(parser):
  AddInstanceResource(parser)


def AddStartInstanceFlags(parser):
  AddInstanceResource(parser)


def AddStopInstanceFlags(parser):
  AddInstanceResource(parser)


def AddUpdateInstanceFlags(parser):
  """Adds accelerator, labels and machine type flags to the parser for update."""
  accelerator_choices = [
      'NVIDIA_TESLA_K80', 'NVIDIA_TESLA_P100', 'NVIDIA_TESLA_V100',
      'NVIDIA_TESLA_P4', 'NVIDIA_TESLA_T4', 'NVIDIA_TESLA_T4_VWS',
      'NVIDIA_TESLA_P100_VWS', 'NVIDIA_TESLA_P4_VWS', 'TPU_V2', 'TPU_V3'
  ]
  AddInstanceResource(parser)
  update_group = parser.add_group(required=True)
  update_group.add_argument(
      '--accelerator-type',
      help='Type of this accelerator.',
      choices=accelerator_choices,
      default=None)
  update_group.add_argument(
      '--accelerator-core-count',
      help='Count of cores of this accelerator.',
      type=int)
  update_group.add_argument(
      '--labels',
      help=('Labels to apply to this instance. '
            'These can be later modified by the setLabels method.'),
      type=arg_parsers.ArgDict(),
      metavar='KEY=VALUE')
  update_group.add_argument(
      '--machine-type',
      help='The [Compute Engine machine type](/compute/docs/machine-types).')
