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
"""Command for creating instances."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import base_classes_resource_registry as resource_registry
from googlecloudsdk.api_lib.compute import csek_utils
from googlecloudsdk.api_lib.compute import image_utils
from googlecloudsdk.api_lib.compute import instance_utils
from googlecloudsdk.api_lib.compute import metadata_utils
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.instances import flags as instances_flags
from googlecloudsdk.command_lib.compute.resource_policies import flags as maintenance_flags
from googlecloudsdk.command_lib.compute.resource_policies import util as maintenance_util
from googlecloudsdk.command_lib.compute.sole_tenancy import flags as sole_tenancy_flags
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
import six
from six.moves import zip

DETAILED_HELP = {
    'DESCRIPTION':
        """
        *{command}* facilitates the creation of Google Compute Engine
        virtual machines.

        When an instance is in RUNNING state and the system begins to boot,
        the instance creation is considered finished, and the command returns
        with a list of new virtual machines.  Note that you usually cannot log
        into a new instance until it finishes booting. Check the progress of an
        instance using `gcloud compute instances get-serial-port-output`.

        For more examples, refer to the *EXAMPLES* section below.
        """,
    'EXAMPLES':
        """
        To create an instance with the latest 'Red Hat Enterprise Linux 8' image
        available, run:

          $ {command} example-instance --image-family=rhel-8 --image-project=rhel-cloud --zone=us-central1-a

        To create instances called 'example-instance-1', 'example-instance-2',
        and 'example-instance-3' in the 'us-central1-a' zone, run:

          $ {command} example-instance-1 example-instance-2 example-instance-3 --zone=us-central1-a
        """,
}


def _CommonArgs(parser,
                enable_regional=False,
                enable_kms=False,
                deprecate_maintenance_policy=False,
                enable_resource_policy=False,
                supports_min_node_cpu=False,
                supports_location_hint=False,
                supports_erase_vss=False,
                snapshot_csek=False,
                image_csek=False):
  """Register parser args common to all tracks."""
  metadata_utils.AddMetadataArgs(parser)
  instances_flags.AddDiskArgs(parser, enable_regional, enable_kms=enable_kms)
  instances_flags.AddCreateDiskArgs(
      parser,
      enable_kms=enable_kms,
      enable_snapshots=True,
      resource_policy=enable_resource_policy,
      source_snapshot_csek=snapshot_csek,
      image_csek=image_csek)
  instances_flags.AddCanIpForwardArgs(parser)
  instances_flags.AddAddressArgs(parser, instances=True)
  instances_flags.AddAcceleratorArgs(parser)
  instances_flags.AddMachineTypeArgs(parser)
  instances_flags.AddMaintenancePolicyArgs(
      parser, deprecate=deprecate_maintenance_policy)
  instances_flags.AddNoRestartOnFailureArgs(parser)
  instances_flags.AddPreemptibleVmArgs(parser)
  instances_flags.AddServiceAccountAndScopeArgs(
      parser,
      False,
      extra_scopes_help='However, if neither `--scopes` nor `--no-scopes` are '
      'specified and the project has no default service '
      'account, then the instance will be created with no '
      'scopes. Note that the level of access that a service '
      'account has is determined by a combination of access '
      'scopes and IAM roles so you must configure both '
      'access scopes and IAM roles for the service account '
      'to work properly.')
  instances_flags.AddTagsArgs(parser)
  instances_flags.AddCustomMachineTypeArgs(parser)
  instances_flags.AddNetworkArgs(parser)
  instances_flags.AddPrivateNetworkIpArgs(parser)
  instances_flags.AddHostnameArg(parser)
  instances_flags.AddImageArgs(parser, enable_snapshots=True)
  instances_flags.AddDeletionProtectionFlag(parser)
  instances_flags.AddPublicPtrArgs(parser, instance=True)
  instances_flags.AddNetworkTierArgs(parser, instance=True)
  instances_flags.AddShieldedInstanceConfigArgs(parser)
  instances_flags.AddDisplayDeviceArg(parser)

  instances_flags.AddReservationAffinityGroup(
      parser,
      group_text='Specifies the reservation for the instance.',
      affinity_text='The type of reservation for the instance.')

  maintenance_flags.AddResourcePoliciesArgs(parser, 'added to', 'instance')

  sole_tenancy_flags.AddNodeAffinityFlagToParser(parser)

  if supports_min_node_cpu:
    instances_flags.AddMinNodeCpuArg(parser)

  if supports_location_hint:
    instances_flags.AddLocationHintArg(parser)

  if supports_erase_vss:
    flags.AddEraseVssSignature(parser, 'source snapshots or source machine'
                               ' image')

  labels_util.AddCreateLabelsFlags(parser)

  parser.add_argument(
      '--description', help='Specifies a textual description of the instances.')

  instances_flags.INSTANCES_ARG_FOR_CREATE.AddArgument(
      parser, operation_type='create')

  csek_utils.AddCsekKeyArgs(parser)

  base.ASYNC_FLAG.AddToParser(parser)
  parser.display_info.AddFormat(
      resource_registry.RESOURCE_REGISTRY['compute.instances'].list_format)
  parser.display_info.AddCacheUpdater(completers.InstancesCompleter)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create Google Compute Engine virtual machine instances."""

  _support_kms = True
  _support_nvdimm = False
  _support_public_dns = False
  _support_disk_resource_policy = False
  _support_erase_vss = False
  _support_machine_image_key = False
  _support_min_node_cpu = False
  _support_location_hint = False
  _support_source_snapshot_csek = False
  _support_image_csek = False
  _support_confidential_compute = False
  _support_post_key_revocation_action_type = False

  @classmethod
  def Args(cls, parser):
    _CommonArgs(parser, enable_kms=cls._support_kms)
    cls.SOURCE_INSTANCE_TEMPLATE = (
        instances_flags.MakeSourceInstanceTemplateArg())
    cls.SOURCE_INSTANCE_TEMPLATE.AddArgument(parser)
    instances_flags.AddLocalSsdArgs(parser)
    instances_flags.AddMinCpuPlatformArgs(parser, base.ReleaseTrack.GA)

  def Collection(self):
    return 'compute.instances'

  def GetSourceInstanceTemplate(self, args, resources):
    """Get sourceInstanceTemplate value as required by API."""
    if not args.IsSpecified('source_instance_template'):
      return None
    ref = self.SOURCE_INSTANCE_TEMPLATE.ResolveAsResource(args, resources)
    return ref.SelfLink()

  def GetSourceMachineImage(self, args, resources):
    """Get sourceMachineImage value as required by API."""
    return None

  def _BuildShieldedInstanceConfigMessage(self, messages, args):
    if (args.IsSpecified('shielded_vm_secure_boot') or
        args.IsSpecified('shielded_vm_vtpm') or
        args.IsSpecified('shielded_vm_integrity_monitoring')):
      return instance_utils.CreateShieldedInstanceConfigMessage(
          messages, args.shielded_vm_secure_boot, args.shielded_vm_vtpm,
          args.shielded_vm_integrity_monitoring)
    else:
      return None

  def _BuildConfidentialInstanceConfigMessage(self, messages, args):
    if args.IsSpecified('confidential_compute'):
      return instance_utils.CreateConfidentialInstanceMessage(
          messages, args.confidential_compute)
    else:
      return None

  def _GetNetworkInterfaces(self, args, client, holder, project, zone,
                            skip_defaults):
    return instance_utils.GetNetworkInterfaces(args, client, holder, project,
                                               zone, skip_defaults)

  def _GetDiskMessages(self, args, skip_defaults, instance_refs, compute_client,
                       resource_parser, create_boot_disk, boot_disk_size_gb,
                       image_uri, csek_keys):
    flags_to_check = [
        'disk',
        'local_ssd',
        'boot_disk_type',
        'boot_disk_device_name',
        'boot_disk_auto_delete',
        'require_csek_key_create',
    ]
    if self._support_kms:
      flags_to_check.extend([
          'create_disk',
          'boot_disk_kms_key',
          'boot_disk_kms_project',
          'boot_disk_kms_location',
          'boot_disk_kms_keyring',
      ])
    if self._support_nvdimm:
      flags_to_check.extend(['local_nvdimm'])

    if (skip_defaults and
        not instance_utils.IsAnySpecified(args, *flags_to_check)):
      return [[] for _ in instance_refs]

    # A list of lists where the element at index i contains a list of
    # disk messages that should be set for the instance at index i.
    disks_messages = []

    # A mapping of zone to boot disk references for all existing boot
    # disks that are being attached.
    # TODO(b/36050875): Simplify since resources.Resource is now hashable.
    for instance_ref in instance_refs:
      disks_messages.append(
          self._CreateDiskMessage(args, skip_defaults, instance_ref.Name(),
                                  instance_ref.project, instance_ref.zone,
                                  compute_client, resource_parser,
                                  create_boot_disk, boot_disk_size_gb,
                                  image_uri, csek_keys))
    return disks_messages

  def _CreateDiskMessage(self, args, skip_defaults, instance_name, project,
                         zone, compute_client, resource_parser,
                         create_boot_disk, boot_disk_size_gb, image_uri,
                         csek_keys):
    persistent_disks = (
        instance_utils.CreatePersistentAttachedDiskMessages(
            resource_parser, compute_client, csek_keys, args.disk or [],
            project, zone))
    persistent_create_disks = (
        instance_utils.CreatePersistentCreateDiskMessages(
            compute_client,
            resource_parser,
            csek_keys,
            getattr(args, 'create_disk', []),
            project,
            zone,
            enable_kms=self._support_kms,
            enable_snapshots=True,
            resource_policy=self._support_disk_resource_policy,
            enable_source_snapshot_csek=self._support_source_snapshot_csek,
            enable_image_csek=self._support_image_csek))
    local_nvdimms = []
    if self._support_nvdimm:
      local_nvdimms = instance_utils.CreateLocalNvdimmMessages(
          args, resource_parser, compute_client.messages, zone, project)
    local_ssds = instance_utils.CreateLocalSsdMessages(args, resource_parser,
                                                       compute_client.messages,
                                                       zone, project)

    if create_boot_disk:
      boot_snapshot_uri = instance_utils.ResolveSnapshotURI(
          user_project=project,
          snapshot=args.source_snapshot,
          resource_parser=resource_parser)

      boot_disk = instance_utils.CreateDefaultBootAttachedDiskMessage(
          compute_client,
          resource_parser,
          disk_type=args.boot_disk_type,
          disk_device_name=args.boot_disk_device_name,
          disk_auto_delete=args.boot_disk_auto_delete,
          disk_size_gb=boot_disk_size_gb,
          require_csek_key_create=(args.require_csek_key_create
                                   if csek_keys else None),
          image_uri=image_uri,
          instance_name=instance_name,
          project=project,
          zone=zone,
          csek_keys=csek_keys,
          kms_args=args,
          snapshot_uri=boot_snapshot_uri,
          enable_kms=self._support_kms)
      persistent_disks = [boot_disk] + persistent_disks
    return persistent_disks + persistent_create_disks + local_nvdimms + local_ssds

  def _GetProjectToServiceAccountMap(self, args, instance_refs, client,
                                     skip_defaults):
    project_to_sa = {}
    for instance_ref in instance_refs:
      if instance_ref.project not in project_to_sa:
        project_to_sa[instance_ref.project] = self._GetProjectServiceAccount(
            args, instance_ref.Name(), instance_ref.project, client,
            skip_defaults)
    return project_to_sa

  def _GetProjectServiceAccount(
      self,
      args,
      instance_name,
      project,
      client,
      skip_defaults,
  ):
    scopes = None
    if not args.no_scopes and not args.scopes:
      # User didn't provide any input on scopes. If project has no default
      # service account then we want to create a VM with no scopes
      request = (client.apitools_client.projects, 'Get',
                 client.messages.ComputeProjectsGetRequest(project=project))
      errors = []
      result = client.MakeRequests([request], errors)
      if not errors:
        if not result[0].defaultServiceAccount:
          scopes = []
          log.status.Print(
              'There is no default service account for project {}. '
              'Instance {} will not have scopes.'.format(
                  project, instance_name))
    if scopes is None:
      scopes = [] if args.no_scopes else args.scopes

    if args.no_service_account:
      service_account = None
    else:
      service_account = args.service_account
    if (skip_defaults and not args.IsSpecified('scopes') and
        not args.IsSpecified('no_scopes') and
        not args.IsSpecified('service_account') and
        not args.IsSpecified('no_service_account')):
      service_accounts = []
    else:
      service_accounts = instance_utils.CreateServiceAccountMessages(
          messages=client.messages,
          scopes=scopes,
          service_account=service_account)
    return service_accounts

  def _GetImageUri(self, args, client, create_boot_disk, project,
                   resource_parser):
    if create_boot_disk:
      image_expander = image_utils.ImageExpander(client, resource_parser)
      image_uri, _ = image_expander.ExpandImageFlag(
          user_project=project,
          image=args.image,
          image_family=args.image_family,
          image_project=args.image_project,
          return_image_resource=False)
      return image_uri

  def _GetNetworkInterfacesWithValidation(self, args, resource_parser,
                                          compute_client, holder, project, zone,
                                          skip_defaults):
    if args.network_interface:
      return instance_utils.CreateNetworkInterfaceMessages(
          resources=resource_parser,
          compute_client=compute_client,
          network_interface_arg=args.network_interface,
          project=project,
          zone=zone)
    else:
      instances_flags.ValidatePublicPtrFlags(args)
      if self._support_public_dns:
        instances_flags.ValidatePublicDnsFlags(args)

      return self._GetNetworkInterfaces(args, compute_client, holder, project,
                                        zone, skip_defaults)

  def _CreateRequests(self, args, instance_refs, project, zone, compute_client,
                      resource_parser, holder):
    # gcloud creates default values for some fields in Instance resource
    # when no value was specified on command line.
    # When --source-instance-template was specified, defaults are taken from
    # Instance Template and gcloud flags are used to override them - by default
    # fields should not be initialized.
    source_instance_template = self.GetSourceInstanceTemplate(
        args, resource_parser)
    skip_defaults = source_instance_template is not None

    source_machine_image = self.GetSourceMachineImage(args, resource_parser)
    skip_defaults = skip_defaults or source_machine_image is not None

    scheduling = instance_utils.GetScheduling(
        args,
        compute_client,
        skip_defaults,
        support_node_affinity=True,
        support_min_node_cpu=self._support_min_node_cpu,
        support_location_hint=self._support_location_hint)
    tags = instance_utils.GetTags(args, compute_client)
    labels = instance_utils.GetLabels(args, compute_client)
    metadata = instance_utils.GetMetadata(args, compute_client, skip_defaults)
    boot_disk_size_gb = instance_utils.GetBootDiskSizeGb(args)

    network_interfaces = self._GetNetworkInterfacesWithValidation(
        args, resource_parser, compute_client, holder, project, zone,
        skip_defaults)

    machine_type_uris = instance_utils.GetMachineTypeUris(
        args, compute_client, holder, instance_refs, skip_defaults)

    create_boot_disk = not instance_utils.UseExistingBootDisk(args.disk or [])
    image_uri = self._GetImageUri(args, compute_client, create_boot_disk,
                                  project, resource_parser)

    shielded_instance_config = self._BuildShieldedInstanceConfigMessage(
        messages=compute_client.messages, args=args)

    if self._support_confidential_compute:
      confidential_instance_config = (
          self._BuildConfidentialInstanceConfigMessage(
              messages=compute_client.messages, args=args))
    # TODO(b/80138906): Release track should not be used like this.
    # These feature are only exposed in alpha/beta
    allow_rsa_encrypted = False
    if self.ReleaseTrack() in [base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA]:
      allow_rsa_encrypted = True

    csek_keys = csek_utils.CsekKeyStore.FromArgs(args, allow_rsa_encrypted)
    disks_messages = self._GetDiskMessages(args, skip_defaults, instance_refs,
                                           compute_client, resource_parser,
                                           create_boot_disk, boot_disk_size_gb,
                                           image_uri, csek_keys)

    project_to_sa = self._GetProjectToServiceAccountMap(args, instance_refs,
                                                        compute_client,
                                                        skip_defaults)

    requests = []
    for instance_ref, machine_type_uri, disks in zip(instance_refs,
                                                     machine_type_uris,
                                                     disks_messages):

      can_ip_forward = instance_utils.GetCanIpForward(args, skip_defaults)
      guest_accelerators = instance_utils.GetAccelerators(
          args, compute_client, resource_parser, instance_ref.project,
          instance_ref.zone)

      instance = compute_client.messages.Instance(
          canIpForward=can_ip_forward,
          deletionProtection=args.deletion_protection,
          description=args.description,
          disks=disks,
          guestAccelerators=guest_accelerators,
          hostname=args.hostname,
          labels=labels,
          machineType=machine_type_uri,
          metadata=metadata,
          minCpuPlatform=args.min_cpu_platform,
          name=instance_ref.Name(),
          networkInterfaces=network_interfaces,
          serviceAccounts=project_to_sa[instance_ref.project],
          scheduling=scheduling,
          tags=tags)

      resource_policies = getattr(args, 'resource_policies', None)
      if resource_policies:
        parsed_resource_policies = []
        for policy in resource_policies:
          resource_policy_ref = maintenance_util.ParseResourcePolicyWithZone(
              resource_parser,
              policy,
              project=instance_ref.project,
              zone=instance_ref.zone)
          parsed_resource_policies.append(resource_policy_ref.SelfLink())
        instance.resourcePolicies = parsed_resource_policies

      if shielded_instance_config:
        instance.shieldedInstanceConfig = shielded_instance_config

      if self._support_confidential_compute and confidential_instance_config:
        instance.confidentialInstanceConfig = confidential_instance_config

      if self._support_erase_vss and \
        args.IsSpecified('erase_windows_vss_signature'):
        instance.eraseWindowsVssSignature = args.erase_windows_vss_signature

      if self._support_post_key_revocation_action_type and args.IsSpecified(
          'post_key_revocation_action_type'):
        instance.postKeyRevocationActionType = arg_utils.ChoiceToEnum(
            args.post_key_revocation_action_type, compute_client.messages
            .Instance.PostKeyRevocationActionTypeValueValuesEnum)

      request = compute_client.messages.ComputeInstancesInsertRequest(
          instance=instance,
          project=instance_ref.project,
          zone=instance_ref.zone)

      if source_instance_template:
        request.sourceInstanceTemplate = source_instance_template

      if source_machine_image:
        request.instance.sourceMachineImage = source_machine_image
        if args.IsSpecified('source_machine_image_csek_key_file'):
          key = instance_utils.GetSourceMachineImageKey(
              args, self.SOURCE_MACHINE_IMAGE, compute_client, holder)
          request.instance.sourceMachineImageEncryptionKey = key

      if self._support_machine_image_key and \
          args.IsSpecified('source_machine_image_csek_key_file'):
        if not args.IsSpecified('source_machine_image'):
          raise exceptions.RequiredArgumentException(
              '`--source-machine-image`',
              '`--source-machine-image-csek-key-file` requires '
              '`--source-machine-image` to be specified`')

      if args.IsSpecified('enable_display_device'):
        request.instance.displayDevice = compute_client.messages.DisplayDevice(
            enableDisplay=args.enable_display_device)

      request.instance.reservationAffinity = instance_utils.GetReservationAffinity(
          args, compute_client)

      requests.append(
          (compute_client.apitools_client.instances, 'Insert', request))
    return requests

  def Run(self, args):
    instances_flags.ValidateDiskFlags(
        args,
        enable_kms=self._support_kms,
        enable_snapshots=True,
        enable_source_snapshot_csek=self._support_source_snapshot_csek,
        enable_image_csek=self._support_image_csek)
    instances_flags.ValidateImageFlags(args)
    instances_flags.ValidateLocalSsdFlags(args)
    instances_flags.ValidateNicFlags(args)
    instances_flags.ValidateServiceAccountAndScopeArgs(args)
    instances_flags.ValidateAcceleratorArgs(args)
    instances_flags.ValidateNetworkTierArgs(args)
    instances_flags.ValidateReservationAffinityGroup(args)

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    compute_client = holder.client
    resource_parser = holder.resources

    instance_refs = instance_utils.GetInstanceRefs(args, compute_client, holder)

    requests = self._CreateRequests(args, instance_refs,
                                    instance_refs[0].project,
                                    instance_refs[0].zone, compute_client,
                                    resource_parser, holder)
    if not args.async_:
      # TODO(b/63664449): Replace this with poller + progress tracker.
      try:
        # Using legacy MakeRequests (which also does polling) here until
        # replaced by api_lib.utils.waiter.
        return compute_client.MakeRequests(requests)
      except exceptions.ToolException as e:
        invalid_machine_type_message_regex = (
            r'Invalid value for field \'resource.machineType\': .+. '
            r'Machine type with name \'.+\' does not exist in zone \'.+\'\.')
        if re.search(invalid_machine_type_message_regex, six.text_type(e)):
          raise exceptions.ToolException(
              six.text_type(e) +
              '\nUse `gcloud compute machine-types list --zones` to see the '
              'available machine  types.')
        raise

    errors_to_collect = []
    responses = compute_client.BatchRequests(requests, errors_to_collect)
    for r in responses:
      err = getattr(r, 'error', None)
      if err:
        errors_to_collect.append(poller.OperationErrors(err.errors))
    if errors_to_collect:
      raise core_exceptions.MultiError(errors_to_collect)

    operation_refs = [holder.resources.Parse(r.selfLink) for r in responses]

    log.status.Print('NOTE: The users will be charged for public IPs when VMs '
                     'are created.')

    for instance_ref, operation_ref in zip(instance_refs, operation_refs):
      log.status.Print('Instance creation in progress for [{}]: {}'.format(
          instance_ref.instance, operation_ref.SelfLink()))
    log.status.Print('Use [gcloud compute operations describe URI] command '
                     'to check the status of the operation(s).')
    if not args.IsSpecified('format'):
      # For async output we need a separate format. Since we already printed in
      # the status messages information about operations there is nothing else
      # needs to be printed.
      args.format = 'disable'
    return responses


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create Google Compute Engine virtual machine instances."""

  _support_kms = True
  _support_nvdimm = False
  _support_public_dns = False
  _support_disk_resource_policy = True
  _support_erase_vss = True
  _support_machine_image_key = True
  _support_min_node_cpu = True
  _support_location_hint = False
  _support_source_snapshot_csek = False
  _support_image_csek = False
  _support_confidential_compute = False
  _support_post_key_revocation_action_type = False

  def _GetNetworkInterfaces(self, args, client, holder, project, zone,
                            skip_defaults):
    return instance_utils.GetNetworkInterfaces(args, client, holder,
                                               project, zone, skip_defaults)

  def GetSourceMachineImage(self, args, resources):
    """Retrieves the specified source machine image's selflink.

    Args:
      args: The arguments passed into the gcloud command calling this function.
      resources: Resource parser used to retrieve the specified resource
        reference.

    Returns:
      A string containing the specified source machine image's selflink.
    """
    if not args.IsSpecified('source_machine_image'):
      return None
    ref = self.SOURCE_MACHINE_IMAGE.ResolveAsResource(args, resources)
    return ref.SelfLink()

  @classmethod
  def Args(cls, parser):
    _CommonArgs(
        parser,
        enable_regional=True,
        enable_kms=True,
        enable_resource_policy=cls._support_disk_resource_policy,
        supports_erase_vss=cls._support_erase_vss,
        supports_min_node_cpu=cls._support_min_node_cpu)
    cls.SOURCE_INSTANCE_TEMPLATE = (
        instances_flags.MakeSourceInstanceTemplateArg())
    cls.SOURCE_INSTANCE_TEMPLATE.AddArgument(parser)
    cls.SOURCE_MACHINE_IMAGE = (instances_flags.AddMachineImageArg())
    cls.SOURCE_MACHINE_IMAGE.AddArgument(parser)
    instances_flags.AddSourceMachineImageEncryptionKey(parser)
    instances_flags.AddLocalSsdArgs(parser)
    instances_flags.AddMinCpuPlatformArgs(parser, base.ReleaseTrack.BETA)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(CreateBeta):
  """Create Google Compute Engine virtual machine instances."""

  _support_kms = True
  _support_nvdimm = True
  _support_public_dns = True
  _support_disk_resource_policy = True
  _support_erase_vss = True
  _support_machine_image_key = True
  _support_min_node_cpu = True
  _support_location_hint = True
  _support_source_snapshot_csek = True
  _support_image_csek = True
  _support_confidential_compute = True
  _support_post_key_revocation_action_type = True

  def _GetNetworkInterfaces(self, args, client, holder, project, zone,
                            skip_defaults):
    return instance_utils.GetNetworkInterfacesAlpha(args, client, holder,
                                                    project, zone,
                                                    skip_defaults)

  @classmethod
  def Args(cls, parser):
    _CommonArgs(
        parser,
        enable_regional=True,
        enable_kms=True,
        deprecate_maintenance_policy=True,
        enable_resource_policy=cls._support_disk_resource_policy,
        supports_min_node_cpu=cls._support_min_node_cpu,
        supports_location_hint=cls._support_location_hint,
        supports_erase_vss=cls._support_erase_vss,
        snapshot_csek=True,
        image_csek=True)
    CreateAlpha.SOURCE_INSTANCE_TEMPLATE = (
        instances_flags.MakeSourceInstanceTemplateArg())
    CreateAlpha.SOURCE_INSTANCE_TEMPLATE.AddArgument(parser)
    CreateAlpha.SOURCE_MACHINE_IMAGE = (instances_flags.AddMachineImageArg())
    CreateAlpha.SOURCE_MACHINE_IMAGE.AddArgument(parser)
    instances_flags.AddSourceMachineImageEncryptionKey(parser)
    instances_flags.AddMinCpuPlatformArgs(parser, base.ReleaseTrack.ALPHA)
    instances_flags.AddPublicDnsArgs(parser, instance=True)
    instances_flags.AddLocalSsdArgsWithSize(parser)
    instances_flags.AddLocalNvdimmArgs(parser)
    instances_flags.AddConfidentialComputeArgs(parser)
    instances_flags.AddPostKeyRevocationActionTypeArgs(parser)

Create.detailed_help = DETAILED_HELP
