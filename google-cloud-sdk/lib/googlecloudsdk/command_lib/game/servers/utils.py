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
"""Utility functions for Cloud Game Servers update commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
from apitools.base.protorpclite import messages as _messages
from apitools.base.py import encoding
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import resources
from googlecloudsdk.core import yaml
import six

GAME_SERVICES_API = 'gameservices'
OPERATIONS_COLLECTION = 'gameservices.projects.locations.operations'


def AddFieldToUpdateMask(field, patch_request):
  update_mask = patch_request.updateMask
  if update_mask:
    if update_mask.count(field) == 0:
      patch_request.updateMask = update_mask + ',' + field
  else:
    patch_request.updateMask = field
  return patch_request


def GetApiMessage(api_version):
  return apis.GetMessagesModule(GAME_SERVICES_API, api_version)


def GetClient(api_version):
  return apis.GetClientInstance(GAME_SERVICES_API, api_version)


def GetApiVersionFromArgs(args):
  """Return API version based on args.

  Update this whenever there is a new version.

  Args:
    args: The argparse namespace.

  Returns:
    API version (e.g. v1alpha or v1beta).

  Raises:
    UnsupportedReleaseTrackError: If invalid release track from args.
  """

  release_track = args.calliope_command.ReleaseTrack()
  if release_track == base.ReleaseTrack.ALPHA:
    return 'v1alpha'
  if release_track == base.ReleaseTrack.BETA:
    return 'v1beta'
  raise UnsupportedReleaseTrackError(release_track)


class UnsupportedReleaseTrackError(Exception):
  """Raised when requesting an api for an unsupported release track."""


def ParseClusters(api_version, key, val, messages=None):
  messages = messages or GetApiMessage(api_version)

  return messages.LabelSelector.LabelsValue.AdditionalProperty(
      key=key, value=val)


def ParseLabels(api_version, cluster_labels, messages=None):
  messages = messages or GetApiMessage(api_version)

  selectors = messages.LabelSelector.LabelsValue()
  selectors.additionalProperties = cluster_labels

  label_selector = messages.LabelSelector()
  label_selector.labels = selectors

  return label_selector


def GetMessages(api_version):
  return apis.GetMessagesModule(GAME_SERVICES_API, api_version)


def WaitForOperation(response, api_version):
  operation_ref = resources.REGISTRY.ParseRelativeName(
      response.name, collection=OPERATIONS_COLLECTION)
  return waiter.WaitFor(
      waiter.CloudOperationPollerNoResources(
          GetClient(api_version).projects_locations_operations), operation_ref,
      'Waiting for [{0}] to finish'.format(operation_ref.Name()))


class InvalidSpecFileError(exceptions.Error):
  """Error if a spec file is not valid JSON or YAML."""


class InvalidSchemaError(exceptions.Error):
  """Error if a schema is improperly specified."""


def ProcessConfigOverrideFile(config_override_file, api_version):
  """Reads a JSON/YAML config_override_file and returns collection of config override object."""

  try:
    overrides = json.loads(config_override_file)
  except ValueError as e:
    try:
      overrides = yaml.load(config_override_file)
    except yaml.YAMLParseError as e:
      raise InvalidSpecFileError(
          'Error parsing config_override file: [{}]'.format(e))

  messages = GetMessages(api_version)
  message_class = messages.GameServerConfigOverride
  try:
    overrides_message = [
        encoding.DictToMessage(o, message_class) for o in overrides
    ]
  except AttributeError:
    raise InvalidSchemaError(
        'Invalid schema: unexpected game server config override(s) format.')
  except _messages.ValidationError as e:
    # Unfortunately apitools doesn't provide a way to get the path to the
    # invalid field here.
    raise InvalidSchemaError('Invalid schema: [{}]'.format(e))
  unrecognized_field_paths = _GetUnrecognizedFieldPaths(overrides_message)
  if unrecognized_field_paths:
    error_msg_lines = ['Invalid schema, the following fields are unrecognized:']
    error_msg_lines += unrecognized_field_paths
    raise InvalidSchemaError('\n'.join(error_msg_lines))

  return overrides_message


def ProcessFleetConfigsFile(fleet_configs_file, api_version):
  """Reads a JSON/YAML fleet_configs_file and returns collectiong of fleet configs object."""
  try:
    fleet_configs = json.loads(fleet_configs_file)
  except ValueError as e:
    try:
      fleet_configs = yaml.load(fleet_configs_file)
    except yaml.YAMLParseError as e:
      raise InvalidSpecFileError(
          'Error parsing fleet_configs file: [{}]'.format(e))

  messages = GetMessages(api_version)
  message_class = messages.FleetConfig
  fleet_configs_message = []
  try:
    for fc in fleet_configs:
      f = encoding.DictToMessage(fc, message_class)
      spec = yaml.load(f.fleetSpec)
      spec_as_json_str = json.dumps(spec)
      f.fleetSpec = spec_as_json_str
      fleet_configs_message.append(f)
  except AttributeError:
    raise InvalidSchemaError('Invalid schema: expected proper fleet configs')
  except _messages.ValidationError as e:
    # The most likely reason this is reaised is the file that is submitted is
    # following new format (json/yaml without string blob) and we will parse
    # with the new format
    for fc in fleet_configs:
      f = messages.FleetConfig()
      if 'name' in fc:
        f.name = fc['name']
      if 'fleetSpec' not in fc:
        raise InvalidSchemaError(
            'Invalid schema: expected proper fleet configs')
      spec_as_json_str = json.dumps(fc['fleetSpec'])
      f.fleetSpec = spec_as_json_str
      fleet_configs_message.append(f)
  unrecognized_field_paths = _GetUnrecognizedFieldPaths(fleet_configs_message)
  if unrecognized_field_paths:
    error_msg_lines = ['Invalid schema, the following fields are unrecognized:']
    error_msg_lines += unrecognized_field_paths
    raise InvalidSchemaError('\n'.join(error_msg_lines))

  return fleet_configs_message


def ProcessScalingConfigsFile(scaling_configs_file, api_version):
  """Reads a JSON/YAML scaling_configs_file and returns collectiong of scaling configs object."""

  try:
    scaling_configs = json.loads(scaling_configs_file)
  except ValueError as e:
    try:
      scaling_configs = yaml.load(scaling_configs_file)
    except yaml.YAMLParseError as e:
      raise InvalidSpecFileError(
          'Error parsing scaling_configs file: [{}]'.format(e))

  messages = GetMessages(api_version)
  message_class = messages.ScalingConfig
  selector = messages.LabelSelector()
  scaling_configs_message = []
  try:
    for sc in scaling_configs:
      esc = encoding.DictToMessage(sc, message_class)
      if not esc.selectors:
        # Add default selector if not set
        esc.selectors = [selector]
      # Convert yaml to json
      spec = yaml.load(esc.fleetAutoscalerSpec)
      spec_as_json_str = json.dumps(spec)
      esc.fleetAutoscalerSpec = spec_as_json_str
      scaling_configs_message.append(esc)
  except AttributeError:
    raise InvalidSchemaError('Invalid schema: expected proper scaling configs')
  except _messages.ValidationError as e:
    # The most likely reason this is reaised is the file that is submitted is
    # following new format (json/yaml without string blob) and we will parse
    # with the new format
    for sc in scaling_configs:
      s = messages.ScalingConfig()
      if 'selectors' in sc:
        if not isinstance(sc['selectors'], list):
          raise InvalidSchemaError('Invalid schema: selectors must be a list')
        s.selectors = []
        for lab in sc['selectors']:
          labels = []
          for (key, val) in lab['labels'].items():
            labels.append(ParseClusters(None, key, val, messages))
          s.selectors.append(ParseLabels(None, labels, messages))
      else:
        # Add default selector if not set
        s.selectors = [selector]
      if 'name' in sc:
        s.name = sc['name']
      if 'schedules' in sc:
        s.schedules = []
        if not isinstance(sc['schedules'], list):
          raise InvalidSchemaError('Invalid schema: schedules must be a list')
        for sh in sc['schedules']:
          schedule = messages.Schedule()
          if 'cronJobDuration' in sh:
            schedule.cronJobDuration = sh['cronJobDuration']
          if 'cronSpec' in sh:
            schedule.cronSpec = sh['cronSpec']
          if 'startTime' in sh:
            schedule.startTime = sh['startTime']
          if 'endTime' in sh:
            schedule.endTime = sh['endTime']
          s.schedules.append(schedule)
      if 'fleetAutoscalerSpec' not in sc:
        raise InvalidSchemaError(
            'Invalid schema: expected proper scaling configs')
      spec_as_json_str = json.dumps(sc['fleetAutoscalerSpec'])
      s.fleetAutoscalerSpec = spec_as_json_str
      scaling_configs_message.append(s)
  return scaling_configs_message


def _GetUnrecognizedFieldPaths(message):
  """Returns the field paths for unrecognized fields in the message."""
  errors = encoding.UnrecognizedFieldIter(message)
  unrecognized_field_paths = []
  for edges_to_message, field_names in errors:
    message_field_path = '.'.join(six.text_type(e) for e in edges_to_message)
    # Don't print the top level columns field since the user didn't specify it
    message_field_path = message_field_path.replace('columns', '', 1)
    for field_name in field_names:
      unrecognized_field_paths.append('{}.{}'.format(message_field_path,
                                                     field_name))
  return sorted(unrecognized_field_paths)
