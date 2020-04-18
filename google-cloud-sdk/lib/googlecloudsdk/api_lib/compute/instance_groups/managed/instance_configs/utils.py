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
"""Utils for per-instance config APIs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


def MakePerInstanceConfig(messages, name, preserved_state_disks,
                          preserved_state_metadata):
  """Make a per-instance config message from preserved state.

  Args:
    messages: Compute API messages
    name: Name of the instance
    preserved_state_disks: List of preserved state disk map entries
    preserved_state_metadata: List of preserved state metadata map entries

  Returns:
    Per-instance config message
  """
  return messages.PerInstanceConfig(
      name=name,
      preservedState=MakePreservedState(messages, preserved_state_disks,
                                        preserved_state_metadata),
  )


def MakePerInstanceConfigFromDiskAndMetadataDicts(messages,
                                                  name,
                                                  disks=None,
                                                  metadata=None):
  """Create a per-instance config message from disks and metadata attributes.

  Args:
    messages: Messages module
    name: Name of the instance
    disks: list of disk dictionaries, eg. [{
          'device_name': 'foo',
          'source': '../projects/project-foo/.../disks/disk-a',
          'auto_delete': 'on-permanent-instance-deletion' }]
    metadata: list of metadata dictionaries, eg. [{
          'key': 'my-key',
          'value': 'my-value', }]

  Returns:
    per-instance config message
  """
  preserved_state_disks = []
  for disk_dict in disks or []:
    preserved_state_disks.append(
        MakePreservedStateDiskMapEntry(messages, *disk_dict))
  preserved_state_metadata = []
  for metadata_dict in metadata or []:
    preserved_state_metadata.append(
        MakePreservedStateMetadataMapEntry(messages, *metadata_dict))
  return MakePerInstanceConfig(messages, name, preserved_state_disks,
                               preserved_state_metadata)


def MakePreservedState(messages,
                       preserved_state_disks=None,
                       preserved_state_metadata=None):
  """Make preservedState message."""
  preserved_state = messages.PreservedState()
  if preserved_state_disks is not None:
    preserved_state.disks = messages.PreservedState.DisksValue(
        additionalProperties=preserved_state_disks)
  if preserved_state_metadata is not None:
    preserved_state.metadata = messages.PreservedState.MetadataValue(
        additionalProperties=preserved_state_metadata)
  return preserved_state


def MakePreservedStateDiskMapEntry(messages,
                                   device_name,
                                   source,
                                   mode,
                                   auto_delete='never'):
  """Make a map entry for disks field in preservedState message."""
  mode_map = {
      'READ_ONLY':
          messages.PreservedStatePreservedDisk.ModeValueValuesEnum.READ_ONLY,
      'READ_WRITE':
          messages.PreservedStatePreservedDisk.ModeValueValuesEnum.READ_WRITE
  }
  mode_map['ro'] = mode_map['READ_ONLY']
  mode_map['rw'] = mode_map['READ_WRITE']
  auto_delete_map = {
      'never':
          messages.PreservedStatePreservedDisk.AutoDeleteValueValuesEnum.NEVER,
      'on-permanent-instance-deletion':
          messages.PreservedStatePreservedDisk.AutoDeleteValueValuesEnum
          .ON_PERMANENT_INSTANCE_DELETION,
  }
  preserved_disk = messages.PreservedStatePreservedDisk(
      autoDelete=auto_delete_map[auto_delete], source=source)
  if mode:
    preserved_disk.mode = mode_map[mode]
  return messages.PreservedState.DisksValue.AdditionalProperty(
      key=device_name, value=preserved_disk)


def MakePreservedStateMetadataMapEntry(messages, key, value):
  """Make a map entry for metadata field in preservedState message."""
  return messages.PreservedState.MetadataValue.AdditionalProperty(
      key=key, value=value)
