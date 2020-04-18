# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Command for creating instance templates."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import json
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import constants
from googlecloudsdk.api_lib.compute import image_utils
from googlecloudsdk.api_lib.compute import instance_template_utils
from googlecloudsdk.api_lib.compute import instance_utils
from googlecloudsdk.api_lib.compute import metadata_utils
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.instance_templates import flags as instance_templates_flags
from googlecloudsdk.command_lib.compute.instance_templates import mesh_mode_aux_data
from googlecloudsdk.command_lib.compute.instances import flags as instances_flags
from googlecloudsdk.command_lib.compute.sole_tenancy import flags as sole_tenancy_flags
from googlecloudsdk.command_lib.compute.sole_tenancy import util as sole_tenancy_util
from googlecloudsdk.command_lib.util.args import labels_util

import six

_INSTANTIATE_FROM_VALUES = [
    'attach-read-only',
    'blank',
    'custom-image',
    'do-not-include',
    'source-image',
    'source-image-family',
]


def _CommonArgs(
    parser,
    release_track,
    support_source_instance,
    support_local_ssd_size=False,
    support_kms=False,
    support_resource_policy=False,
    support_min_node_cpu=False,
    support_location_hint=False
):
  """Adding arguments applicable for creating instance templates."""
  parser.display_info.AddFormat(instance_templates_flags.DEFAULT_LIST_FORMAT)
  metadata_utils.AddMetadataArgs(parser)
  instances_flags.AddDiskArgs(parser, enable_kms=support_kms)
  instances_flags.AddCreateDiskArgs(parser, enable_kms=support_kms,
                                    resource_policy=support_resource_policy)
  if support_local_ssd_size:
    instances_flags.AddLocalSsdArgsWithSize(parser)
  else:
    instances_flags.AddLocalSsdArgs(parser)
  instances_flags.AddCanIpForwardArgs(parser)
  instances_flags.AddAddressArgs(parser, instances=False)
  instances_flags.AddAcceleratorArgs(parser)
  instances_flags.AddMachineTypeArgs(parser)
  deprecate_maintenance_policy = release_track in [base.ReleaseTrack.ALPHA]
  instances_flags.AddMaintenancePolicyArgs(parser, deprecate_maintenance_policy)
  instances_flags.AddNoRestartOnFailureArgs(parser)
  instances_flags.AddPreemptibleVmArgs(parser)
  instances_flags.AddServiceAccountAndScopeArgs(parser, False)
  instances_flags.AddTagsArgs(parser)
  instances_flags.AddCustomMachineTypeArgs(parser)
  instances_flags.AddImageArgs(parser)
  instances_flags.AddNetworkArgs(parser)
  instances_flags.AddShieldedInstanceConfigArgs(parser)
  labels_util.AddCreateLabelsFlags(parser)
  instances_flags.AddNetworkTierArgs(parser, instance=True)
  instances_flags.AddPrivateNetworkIpArgs(parser)

  sole_tenancy_flags.AddNodeAffinityFlagToParser(parser)

  if support_min_node_cpu:
    instances_flags.AddMinNodeCpuArg(parser)

  if support_location_hint:
    instances_flags.AddLocationHintArg(parser)

  flags.AddRegionFlag(
      parser,
      resource_type='subnetwork',
      operation_type='attach')

  parser.add_argument(
      '--description',
      help='Specifies a textual description for the instance template.')

  Create.InstanceTemplateArg = (
      instance_templates_flags.MakeInstanceTemplateArg())
  Create.InstanceTemplateArg.AddArgument(parser, operation_type='create')
  if support_source_instance:
    instance_templates_flags.MakeSourceInstanceArg().AddArgument(parser)
    parser.add_argument(
        '--configure-disk',
        type=arg_parsers.ArgDict(
            spec={
                'auto-delete': arg_parsers.ArgBoolean(),
                'device-name': str,
                'instantiate-from': str,
                'custom-image': str,
            },
        ),
        metavar='PROPERTY=VALUE',
        action='append',
        help="""\
        This option has effect only when used with `--source-instance`. It
        allows you to override how the source-instance's disks are defined in
        the template.

        *auto-delete*::: If `true`, this persistent disk will be automatically
        deleted when the instance is deleted. However, if the disk is later
        detached from the instance, this option won't apply. If not provided,
        the setting is copied from the source instance. Allowed values of the
        flag are: `false`, `no`, `true`, and `yes`.

        *device-name*::: Name of the device.

        *instantiate-from*::: Specifies whether to include the disk and which
        image to use. Valid values are: {}

        *custom-image*::: The custom image to use if custom-image is specified
        for instantiate-from.
        """.format(', '.join(_INSTANTIATE_FROM_VALUES)),
    )

  instances_flags.AddReservationAffinityGroup(
      parser,
      group_text="""\
Specifies the reservation for instances created from this template.
""",
      affinity_text="""\
The type of reservation for instances created from this template.
""")

  parser.display_info.AddCacheUpdater(completers.InstanceTemplatesCompleter)


def _ValidateInstancesFlags(args, support_kms=False,):
  """Validate flags for instance template that affects instance creation.

  Args:
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the .Args() method.
      support_kms: If KMS is supported.
  """
  instances_flags.ValidateDiskCommonFlags(args)
  instances_flags.ValidateDiskBootFlags(args, enable_kms=support_kms)
  instances_flags.ValidateCreateDiskFlags(args)
  instances_flags.ValidateLocalSsdFlags(args)
  instances_flags.ValidateNicFlags(args)
  instances_flags.ValidateServiceAccountAndScopeArgs(args)
  instances_flags.ValidateAcceleratorArgs(args)
  instances_flags.ValidateReservationAffinityGroup(args)


def _AddSourceInstanceToTemplate(
    compute_api, args, instance_template, support_source_instance):
  """Set the source instance for the template."""

  if not support_source_instance or not args.source_instance:
    return
  source_instance_arg = instance_templates_flags.MakeSourceInstanceArg()
  source_instance_ref = source_instance_arg.ResolveAsResource(
      args, compute_api.resources)
  instance_template.sourceInstance = source_instance_ref.SelfLink()
  if args.configure_disk:
    messages = compute_api.client.messages
    instance_template.sourceInstanceParams = messages.SourceInstanceParams()
    for disk in args.configure_disk:
      instantiate_from = disk.get('instantiate-from')
      custom_image = disk.get('custom-image')
      if custom_image and instantiate_from != 'custom-image':
        raise exceptions.InvalidArgumentException(
            '--configure-disk',
            'Value for `instaniate-from` must be \'custom-image\' if the key '
            '`custom-image` is specified.')
      disk_config = messages.DiskInstantiationConfig()
      disk_config.autoDelete = disk.get('auto-delete')
      disk_config.deviceName = disk.get('device-name')
      disk_config.instantiateFrom = (
          messages.DiskInstantiationConfig.InstantiateFromValueValuesEnum(
              instantiate_from.upper().replace('-', '_')))
      disk_config.customImage = custom_image
      instance_template.sourceInstanceParams.diskConfigs.append(disk_config)
  # `properties` and `sourceInstance` are a one of.
  instance_template.properties = None


def BuildShieldedInstanceConfigMessage(messages, args):
  """Common routine for creating instance template.

  Build a shielded VM config message.

  Args:
      messages: The client messages.
      args: the arguments passed to the test.

  Returns:
      A shielded VM config message.
  """
  # Set the default values for ShieldedInstanceConfig parameters

  shielded_instance_config_message = None
  enable_secure_boot = None
  enable_vtpm = None
  enable_integrity_monitoring = None
  if not (hasattr(args, 'shielded_vm_secure_boot') or
          hasattr(args, 'shielded_vm_vtpm') or
          hasattr(args, 'shielded_vm_integrity_monitoring')):
    return shielded_instance_config_message

  if (not args.IsSpecified('shielded_vm_secure_boot') and
      not args.IsSpecified('shielded_vm_vtpm') and
      not args.IsSpecified('shielded_vm_integrity_monitoring')):
    return shielded_instance_config_message

  if args.shielded_vm_secure_boot is not None:
    enable_secure_boot = args.shielded_vm_secure_boot
  if args.shielded_vm_vtpm is not None:
    enable_vtpm = args.shielded_vm_vtpm
  if args.shielded_vm_integrity_monitoring is not None:
    enable_integrity_monitoring = args.shielded_vm_integrity_monitoring
  # compute message for shielded VM configuration.
  shielded_instance_config_message = instance_utils.CreateShieldedInstanceConfigMessage(
      messages, enable_secure_boot, enable_vtpm, enable_integrity_monitoring)

  return shielded_instance_config_message


def BuildConfidentialInstanceConfigMessage(messages, args):
  """Build a Confidential Instance Config message.

  Args:
      messages: The client messages.
      args: the arguments passed to the test.

  Returns:
      A Confidential Instance Config message.
  """
  confidential_instance_config_message = None
  enable_confidential_compute = False
  if not (hasattr(args, 'confidential_compute') and
          args.IsSpecified('confidential_compute')):
    return confidential_instance_config_message

  if args.confidential_compute is not None and (isinstance(
      args.confidential_compute, bool)):
    enable_confidential_compute = args.confidential_compute
  confidential_instance_config_message = (
      instance_utils.CreateConfidentialInstanceMessage(
          messages, enable_confidential_compute))
  return confidential_instance_config_message


def PackageLabels(labels_cls, labels):
  # Sorted for test stability
  return labels_cls(additionalProperties=[
      labels_cls.AdditionalProperty(key=key, value=value)
      for key, value in sorted(six.iteritems(labels))])


# Function copied from labels_util.
# Temporary fix for adoption tracking of Managed Envoy.
# TODO(b/146051298) Remove this fix when structured metadata is available.
def ParseCreateArgsWithMeshMode(args, labels_cls, labels_dest='labels'):
  """Initializes labels based on args and the given class."""
  labels = getattr(args, labels_dest)
  if getattr(args, 'mesh',
             False) and args.mesh['mode'] == mesh_mode_aux_data.MeshModes.ON:
    if labels is None:
      labels = collections.OrderedDict()
    labels['mesh-mode'] = 'on'

  if labels is None:
    return None
  return PackageLabels(labels_cls, labels)


def AddScopesForMeshMode(args):

  if getattr(args, 'mesh', False) and args.mesh[
      'mode'] == mesh_mode_aux_data.MeshModes.ON:

    if args.scopes is None:
      args.scopes = constants.DEFAULT_SCOPES[:]

    if 'cloud-platform' not in args.scopes and 'https://www.googleapis.com/auth/cloud-platform' not in args.scopes:
      args.scopes.append('cloud-platform')


def AddMeshArgsToMetadata(args):
  """Inserts the Mesh mode arguments provided by the user to the instance metadata.

  Args:
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the .Args() method.
  """
  if getattr(args, 'mesh', False):

    mesh_mode_config = collections.OrderedDict()

    # add --mesh flag data to metadata.
    mesh_mode_config['mode'] = args.mesh['mode']
    if 'workload-ports' in args.mesh:
      # convert list of strings to list of integers.
      workload_ports = list(map(int, args.mesh['workload-ports'].split(';')))
      # find unique ports by converting list of integers to set of integers.
      unique_workload_ports = set(workload_ports)
      # convert it back to list of integers.
      # this is done to make it JSON serializable.
      workload_ports = list(unique_workload_ports)
      mesh_mode_config['service'] = {
          'workload-ports': workload_ports,
      }

    # add --mesh_labels flag to metadata as described by go/gce-envoy-gcloud
    if getattr(args, 'mesh_labels', False):
      mesh_mode_config['labels'] = args.mesh_labels

    # add --mesh-proxy-config flag to metadata
    # as described by go/gce-envoy-gcloud
    if getattr(args, 'mesh_proxy_config', False):
      mesh_mode_config['proxy-spec'] = {
          'trafficdirector-config': args.mesh_proxy_config
      }

    if args.mesh['mode'] == mesh_mode_aux_data.MeshModes.ON:
      args.metadata['enable-osconfig'] = 'true'
      gce_software_declaration = collections.OrderedDict()
      mesh_agent_recipe = collections.OrderedDict()

      mesh_agent_recipe['name'] = 'install-gce-mesh-agent'
      mesh_agent_recipe['desired_state'] = 'INSTALLED'
      mesh_agent_recipe['installSteps'] = [{
          'scriptRun': {
              'script': mesh_mode_aux_data.startup_script
          }
      }]

      gce_software_declaration['softwareRecipes'] = [mesh_agent_recipe]

      args.metadata['gce-software-declaration'] = json.dumps(
          gce_software_declaration)
      args.metadata['enable-guest-attributes'] = 'TRUE'

    args.metadata['gce-mesh'] = json.dumps(mesh_mode_config)


def _RunCreate(compute_api,
               args,
               support_source_instance,
               support_kms=False,
               support_min_node_cpu=False,
               support_confidential_compute=False,
               support_location_hint=False):
  """Common routine for creating instance template.

  This is shared between various release tracks.

  Args:
      compute_api: The compute api.
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the .Args() method.
      support_source_instance: indicates whether source instance is supported.
      support_kms: Indicate whether KMS is integrated or not.
      support_min_node_cpu: Indicate whether the --min-node-cpu flag for
        sole tenancy overcommit is supported.
      support_confidential_compute: Indicate whether confidential compute is
        supported.
      support_location_hint: Indicate whether location hint is supported

  Returns:
      A resource object dispatched by display.Displayer().
  """
  _ValidateInstancesFlags(
      args, support_kms=support_kms)
  instances_flags.ValidateNetworkTierArgs(args)

  instance_templates_flags.ValidateMeshModeFlags(args)

  client = compute_api.client

  boot_disk_size_gb = utils.BytesToGb(args.boot_disk_size)
  utils.WarnIfDiskSizeIsTooSmall(boot_disk_size_gb, args.boot_disk_type)

  instance_template_ref = (
      Create.InstanceTemplateArg.ResolveAsResource(
          args, compute_api.resources))

  AddScopesForMeshMode(args)
  AddMeshArgsToMetadata(args)

  metadata = metadata_utils.ConstructMetadataMessage(
      client.messages,
      metadata=args.metadata,
      metadata_from_file=args.metadata_from_file)

  if hasattr(args, 'network_interface') and args.network_interface:
    network_interfaces = (
        instance_template_utils.CreateNetworkInterfaceMessages)(
            resources=compute_api.resources,
            scope_lister=flags.GetDefaultScopeLister(client),
            messages=client.messages,
            network_interface_arg=args.network_interface,
            region=args.region)
  else:
    network_tier = getattr(args, 'network_tier', None)
    network_interfaces = [
        instance_template_utils.CreateNetworkInterfaceMessage(
            resources=compute_api.resources,
            scope_lister=flags.GetDefaultScopeLister(client),
            messages=client.messages,
            network=args.network,
            private_ip=args.private_network_ip,
            region=args.region,
            subnet=args.subnet,
            address=(instance_template_utils.EPHEMERAL_ADDRESS
                     if not args.no_address and not args.address
                     else args.address),
            network_tier=network_tier)
    ]

  # Compute the shieldedInstanceConfig message.
  shieldedinstance_config_message = BuildShieldedInstanceConfigMessage(
      messages=client.messages, args=args)

  if support_confidential_compute:
    confidential_instance_config_message = (
        BuildConfidentialInstanceConfigMessage(
            messages=client.messages, args=args))

  node_affinities = sole_tenancy_util.GetSchedulingNodeAffinityListFromArgs(
      args, client.messages)

  min_node_cpu = None
  if support_min_node_cpu and args.IsSpecified('min_node_cpu'):
    min_node_cpu = args.min_node_cpu

  location_hint = None
  if support_location_hint and args.IsSpecified('location_hint'):
    location_hint = args.location_hint

  scheduling = instance_utils.CreateSchedulingMessage(
      messages=client.messages,
      maintenance_policy=args.maintenance_policy,
      preemptible=args.preemptible,
      restart_on_failure=args.restart_on_failure,
      node_affinities=node_affinities,
      min_node_cpu=min_node_cpu,
      location_hint=location_hint)

  if args.no_service_account:
    service_account = None
  else:
    service_account = args.service_account
  service_accounts = instance_utils.CreateServiceAccountMessages(
      messages=client.messages,
      scopes=[] if args.no_scopes else args.scopes,
      service_account=service_account)

  create_boot_disk = not instance_utils.UseExistingBootDisk(args.disk or [])
  if create_boot_disk:
    image_expander = image_utils.ImageExpander(client, compute_api.resources)
    try:
      image_uri, _ = image_expander.ExpandImageFlag(
          user_project=instance_template_ref.project,
          image=args.image,
          image_family=args.image_family,
          image_project=args.image_project,
          return_image_resource=True)
    except utils.ImageNotFoundError as e:
      if args.IsSpecified('image_project'):
        raise e
      image_uri, _ = image_expander.ExpandImageFlag(
          user_project=instance_template_ref.project,
          image=args.image,
          image_family=args.image_family,
          image_project=args.image_project,
          return_image_resource=False)
      raise utils.ImageNotFoundError(
          'The resource [{}] was not found. Is the image located in another '
          'project? Use the --image-project flag to specify the '
          'project where the image is located.'.format(image_uri))
  else:
    image_uri = None

  if args.tags:
    tags = client.messages.Tags(items=args.tags)
  else:
    tags = None

  persistent_disks = (
      instance_template_utils.CreatePersistentAttachedDiskMessages(
          client.messages, args.disk or []))

  persistent_create_disks = (
      instance_template_utils.CreatePersistentCreateDiskMessages(
          client, compute_api.resources, instance_template_ref.project,
          getattr(args, 'create_disk', []), support_kms=support_kms))

  if create_boot_disk:
    boot_disk_list = [
        instance_template_utils.CreateDefaultBootAttachedDiskMessage(
            messages=client.messages,
            disk_type=args.boot_disk_type,
            disk_device_name=args.boot_disk_device_name,
            disk_auto_delete=args.boot_disk_auto_delete,
            disk_size_gb=boot_disk_size_gb,
            image_uri=image_uri,
            kms_args=args,
            support_kms=support_kms)]
  else:
    boot_disk_list = []

  local_nvdimms = instance_utils.CreateLocalNvdimmMessages(
      args,
      compute_api.resources,
      client.messages,
  )

  local_ssds = instance_utils.CreateLocalSsdMessages(
      args,
      compute_api.resources,
      client.messages,
  )

  disks = (
      boot_disk_list + persistent_disks + persistent_create_disks +
      local_nvdimms + local_ssds
  )

  machine_type = instance_utils.InterpretMachineType(
      machine_type=args.machine_type,
      custom_cpu=args.custom_cpu,
      custom_memory=args.custom_memory,
      ext=getattr(args, 'custom_extensions', None),
      vm_type=getattr(args, 'custom_vm_type', None))

  guest_accelerators = (
      instance_template_utils.CreateAcceleratorConfigMessages(
          client.messages, getattr(args, 'accelerator', None)))

  instance_template = client.messages.InstanceTemplate(
      properties=client.messages.InstanceProperties(
          machineType=machine_type,
          disks=disks,
          canIpForward=args.can_ip_forward,
          metadata=metadata,
          minCpuPlatform=args.min_cpu_platform,
          networkInterfaces=network_interfaces,
          serviceAccounts=service_accounts,
          scheduling=scheduling,
          tags=tags,
          guestAccelerators=guest_accelerators,
      ),
      description=args.description,
      name=instance_template_ref.Name(),
  )

  instance_template.properties.shieldedInstanceConfig = shieldedinstance_config_message

  instance_template.properties.reservationAffinity = instance_utils.GetReservationAffinity(
      args, client)

  if support_confidential_compute:
    instance_template.properties.confidentialInstanceConfig = (
        confidential_instance_config_message)

  request = client.messages.ComputeInstanceTemplatesInsertRequest(
      instanceTemplate=instance_template,
      project=instance_template_ref.project)

  request.instanceTemplate.properties.labels = ParseCreateArgsWithMeshMode(
      args, client.messages.InstanceProperties.LabelsValue)

  _AddSourceInstanceToTemplate(
      compute_api, args, instance_template, support_source_instance)

  return client.MakeRequests([(client.apitools_client.instanceTemplates,
                               'Insert', request)])


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a Compute Engine virtual machine instance template.

  *{command}* facilitates the creation of Google Compute Engine
  virtual machine instance templates. For example, running:

      $ {command} INSTANCE-TEMPLATE

  will create one instance templates called 'INSTANCE-TEMPLATE'.

  Instance templates are global resources, and can be used to create
  instances in any zone.
  """
  _support_source_instance = True
  _support_kms = True
  _support_min_node_cpu = False
  _support_location_hint = False

  @classmethod
  def Args(cls, parser):
    _CommonArgs(
        parser,
        release_track=base.ReleaseTrack.GA,
        support_source_instance=cls._support_source_instance,
        support_kms=cls._support_kms,
        support_min_node_cpu=cls._support_min_node_cpu,
        support_location_hint=cls._support_location_hint
    )
    instances_flags.AddMinCpuPlatformArgs(parser, base.ReleaseTrack.GA)

  def Run(self, args):
    """Creates and runs an InstanceTemplates.Insert request.

    Args:
      args: argparse.Namespace, An object that contains the values for the
          arguments specified in the .Args() method.

    Returns:
      A resource object dispatched by display.Displayer().
    """
    return _RunCreate(
        base_classes.ComputeApiHolder(base.ReleaseTrack.GA),
        args,
        support_source_instance=self._support_source_instance,
        support_kms=self._support_kms,
        support_min_node_cpu=self._support_min_node_cpu,
        support_location_hint=self._support_location_hint
    )


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create a Compute Engine virtual machine instance template.

  *{command}* facilitates the creation of Google Compute Engine
  virtual machine instance templates. For example, running:

      $ {command} INSTANCE-TEMPLATE

  will create one instance templates called 'INSTANCE-TEMPLATE'.

  Instance templates are global resources, and can be used to create
  instances in any zone.
  """
  _support_source_instance = True
  _support_kms = True
  _support_resource_policy = True
  _support_min_node_cpu = True
  _support_location_hint = False

  @classmethod
  def Args(cls, parser):
    _CommonArgs(
        parser,
        release_track=base.ReleaseTrack.BETA,
        support_local_ssd_size=False,
        support_source_instance=cls._support_source_instance,
        support_kms=cls._support_kms,
        support_resource_policy=cls._support_resource_policy,
        support_min_node_cpu=cls._support_min_node_cpu,
        support_location_hint=cls._support_location_hint
    )
    instances_flags.AddMinCpuPlatformArgs(parser, base.ReleaseTrack.BETA)

  def Run(self, args):
    """Creates and runs an InstanceTemplates.Insert request.

    Args:
      args: argparse.Namespace, An object that contains the values for the
          arguments specified in the .Args() method.

    Returns:
      A resource object dispatched by display.Displayer().
    """
    return _RunCreate(
        base_classes.ComputeApiHolder(base.ReleaseTrack.BETA),
        args=args,
        support_source_instance=self._support_source_instance,
        support_kms=self._support_kms,
        support_min_node_cpu=self._support_min_node_cpu,
        support_location_hint=self._support_location_hint)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(Create):
  """Create a Compute Engine virtual machine instance template.

  *{command}* facilitates the creation of Google Compute Engine
  virtual machine instance templates. For example, running:

      $ {command} INSTANCE-TEMPLATE

  will create one instance templates called 'INSTANCE-TEMPLATE'.

  Instance templates are global resources, and can be used to create
  instances in any zone.
  """
  _support_source_instance = True
  _support_kms = True
  _support_resource_policy = True
  _support_min_node_cpu = True
  _support_confidential_compute = True
  _support_location_hint = True

  @classmethod
  def Args(cls, parser):
    _CommonArgs(
        parser,
        release_track=base.ReleaseTrack.ALPHA,
        support_local_ssd_size=True,
        support_source_instance=cls._support_source_instance,
        support_kms=cls._support_kms,
        support_resource_policy=cls._support_resource_policy,
        support_min_node_cpu=cls._support_min_node_cpu,
        support_location_hint=cls._support_location_hint
    )
    instances_flags.AddLocalNvdimmArgs(parser)
    instances_flags.AddMinCpuPlatformArgs(parser, base.ReleaseTrack.ALPHA)
    instances_flags.AddConfidentialComputeArgs(parser)
    instance_templates_flags.AddMeshModeConfigArgs(parser)

  def Run(self, args):
    """Creates and runs an InstanceTemplates.Insert request.

    Args:
      args: argparse.Namespace, An object that contains the values for the
          arguments specified in the .Args() method.

    Returns:
      A resource object dispatched by display.Displayer().
    """
    return _RunCreate(
        base_classes.ComputeApiHolder(base.ReleaseTrack.ALPHA),
        args=args,
        support_source_instance=self._support_source_instance,
        support_kms=self._support_kms,
        support_min_node_cpu=self._support_min_node_cpu,
        support_confidential_compute=self._support_confidential_compute,
        support_location_hint=self._support_location_hint)


DETAILED_HELP = {
    'brief':
        'Create a Compute Engine virtual machine instance template',
    'DESCRIPTION':
        '*{command}* facilitates the creation of Google Compute '
        'Engine virtual machine instance templates. Instance '
        'templates are global resources, and can be used to create '
        'instances in any zone.',
    'EXAMPLES':
        """\
        To create an instance template named 'INSTANCE-TEMPLATE' with the 'n2'
        vm type, '9GB' memory, and 2 CPU cores, run:

          $ {command} INSTANCE-TEMPLATE --custom-vm-type=n2 --custom-cpu=2 --custom-memory=9GB
        """
}


Create.detailed_help = DETAILED_HELP
