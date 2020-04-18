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
"""Command for creating instance with per instance config."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import managed_instance_groups_utils
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags
from googlecloudsdk.command_lib.compute.instance_groups.managed.instance_configs import instance_configs_messages


@base.ReleaseTracks(base.ReleaseTrack.GA)
class CreateInstanceGA(base.CreateCommand):
  """Create a new virtual machine instance in a managed instance group."""

  @staticmethod
  def Args(parser):
    instance_groups_flags.GetInstanceGroupManagerArg(
        region_flag=True).AddArgument(
            parser, operation_type='create instance in')
    instance_groups_flags.AddCreateInstancesFlags(
        parser, add_stateful_args=False)

  @classmethod
  def ShouldSetStatefulConfig(cls):
    return False

  @staticmethod
  def _CreateNewInstanceReference(holder, igm_ref, instance_name):
    """Creates reference to instance in instance group (zonal or regional)."""
    if igm_ref.Collection() == 'compute.instanceGroupManagers':
      instance_ref = holder.resources.Parse(
          instance_name,
          params={
              'project': igm_ref.project,
              'zone': igm_ref.zone,
          },
          collection='compute.instances')
    elif igm_ref.Collection() == 'compute.regionInstanceGroupManagers':
      instance_ref = holder.resources.Parse(
          instance_name,
          params={
              'project': igm_ref.project,
              'zone': igm_ref.region + '-a',
          },
          collection='compute.instances')
    else:
      raise ValueError('Unknown reference type {0}'.format(
          igm_ref.Collection()))
    if not instance_ref:
      raise managed_instance_groups_utils.ResourceCannotBeResolvedException(
          'Instance name {0} cannot be resolved.'.format(instance_name))
    return instance_ref

  def Run(self, args):
    if self.ShouldSetStatefulConfig():
      instance_groups_flags.ValidateMigStatefulFlagsForInstanceConfigs(
          args, need_disk_source=True)

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    resources = holder.resources

    igm_ref = (instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG
               .ResolveAsResource)(
                   args,
                   resources,
                   scope_lister=compute_flags.GetDefaultScopeLister(client))

    instance_ref = self._CreateNewInstanceReference(
        holder=holder, igm_ref=igm_ref, instance_name=args.instance)

    stateful_disks = (
        args.stateful_disk if self.ShouldSetStatefulConfig() else [])
    stateful_metadata = (
        args.stateful_metadata if self.ShouldSetStatefulConfig() else {})
    per_instance_config_message = (
        instance_configs_messages.CreatePerInstanceConfigMessage)(
            holder,
            instance_ref,
            stateful_disks,
            stateful_metadata,
            disk_getter=NonExistentDiskGetter(),
            set_preserved_state=self.ShouldSetStatefulConfig())

    operation_ref, service = instance_configs_messages.CallCreateInstances(
        holder=holder,
        igm_ref=igm_ref,
        per_instance_config_message=per_instance_config_message)

    operation_poller = poller.Poller(service)
    create_result = waiter.WaitFor(operation_poller, operation_ref,
                                   'Creating instance.')
    return create_result


CreateInstanceGA.detailed_help = {
    'brief':
        ('Create a new virtual machine instance in a managed instance group '
         'with a defined name.'),
    'DESCRIPTION':
        '*{command}* creates a  virtual machine instance with a defined name.',
    'EXAMPLES':
        """\
        To create an instance `instance-1` in `my-group`
        (in region europe-west4), run:

            $ {command} \\
                  my-group --region=europe-west4 --instance=instance-1
        """
}


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class CreateInstanceBeta(CreateInstanceGA):
  """Create a new virtual machine instance in a managed instance group."""

  @staticmethod
  def Args(parser):
    instance_groups_flags.GetInstanceGroupManagerArg(
        region_flag=True).AddArgument(
            parser, operation_type='create instance in')
    instance_groups_flags.AddCreateInstancesFlags(
        parser, add_stateful_args=True)

  @classmethod
  def ShouldSetStatefulConfig(cls):
    return True


CreateInstanceBeta.detailed_help = {
    'brief':
        ('Create a new virtual machine instance in a managed instance group '
         'with a defined name and optionally its stateful configuration.'),
    'DESCRIPTION':
        """\
        *{command}* creates a  virtual machine instance with a defined name and
        optionally its stateful configuration: stateful disk and stateful
        metadata key-values. Stateful configuration is stored in the
        corresponding newly created per-instance config. An instance with a
        per-instance config will preserve its given name, specified disks, and
        specified metadata key-values during instance recreation, auto-healing,
        and updates and any other lifecycle transitions of the instance.
        """,
    'EXAMPLES':
        """\
        To create an instance `instance-1` in `my-group`
        (in region europe-west4) with metadata `my-key: my-value` and a disk
        disk-1 attached to it as the device `device-1`, run:

            $ {command} \\
                  my-group --region=europe-west4 \\
                  --instance=instance-1 \\
                  --stateful-disk='device-name=foo,source=https://compute.googleapis.com/compute/alpha/projects/my-project/zones/europe-west4/disks/disk-1,mode=rw,auto-delete=on-permanent-instance-deletion' \\
                  --stateful-metadata='my-key=my-value'
        """
}


class NonExistentDiskGetter(object):
  """Dummy class returning None."""

  def __init__(self):
    self.instance_exists = False

  def get_disk(self, device_name):  # pylint: disable=unused-argument,g-bad-name
    return
