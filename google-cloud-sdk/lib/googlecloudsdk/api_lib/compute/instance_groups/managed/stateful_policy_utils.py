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
"""Utils for Stateful policy API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


def MakePreservedStateDisksMapEntry(messages, stateful_disk):
  """Make a map entry for disks field in preservedState message."""
  auto_delete_map = {
      'never':
          messages.PreservedStatePreservedDisk.AutoDeleteValueValuesEnum.NEVER,
      'on-permanent-instance-deletion':
          messages.PreservedStatePreservedDisk.AutoDeleteValueValuesEnum
          .ON_PERMANENT_INSTANCE_DELETION
  }
  disk_device = messages.PreservedStatePreservedDisk()
  if 'auto_delete' in stateful_disk:
    disk_device.autoDelete = auto_delete_map[stateful_disk['auto_delete']]
  return messages.PreservedState.DisksValue.AdditionalProperty(
      key=stateful_disk['device_name'], value=disk_device)


def MakePreservedState(messages, preserved_state_disks=None):
  """Make preservedState message for preservedStateFromPolicy."""
  preserved_state = messages.PreservedState()
  if preserved_state:
    preserved_state.disks = messages.PreservedState.DisksValue(
        additionalProperties=preserved_state_disks)
  return preserved_state


def MakeStatefulPolicyPreservedStateDiskEntry(messages, stateful_disk_dict):
  """Create StatefulPolicyPreservedState from a list of device names."""
  disk_device = messages.StatefulPolicyPreservedStateDiskDevice()
  if stateful_disk_dict.get('auto-delete'):
    disk_device.autoDelete = (
        stateful_disk_dict.get('auto-delete').GetAutoDeleteEnumValue(
            messages.StatefulPolicyPreservedStateDiskDevice
            .AutoDeleteValueValuesEnum))
  # Add all disk_devices to map
  return messages.StatefulPolicyPreservedState.DisksValue.AdditionalProperty(
      key=stateful_disk_dict.get('device-name'), value=disk_device)


def MakeStatefulPolicy(messages, preserved_state_disks):
  """Make stateful policy proto from a list of preserved state disk protos."""
  if not preserved_state_disks:
    preserved_state_disks = []
  return messages.StatefulPolicy(
      preservedState=messages.StatefulPolicyPreservedState(
          disks=messages.StatefulPolicyPreservedState.DisksValue(
              additionalProperties=preserved_state_disks)))


def PatchStatefulPolicyDisk(preserved_state, patch):
  """Patch the preserved state proto."""
  if patch.value.autoDelete:
    preserved_state.value.autoDelete = patch.value.autoDelete
