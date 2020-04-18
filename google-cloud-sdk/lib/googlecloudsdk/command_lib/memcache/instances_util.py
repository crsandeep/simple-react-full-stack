# -*- coding: utf-8 -*- #
# Copyright 2020 Google Inc. All Rights Reserved.
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
"""Utilities for `gcloud memcache instances` commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib import memcache
from googlecloudsdk.calliope import arg_parsers

MEMCACHE_EXTENDED_OPTIONS = ('track-sizes', 'watcher-logbuf-size',
                             'worker-logbuf-size', 'lru-crawler',
                             'idle-timeout', 'lru-maintainer', 'maxconns-fast',
                             'hash-algorithm')


def NodeMemory(value):
  """Declarative command argument type for node-memory flag."""
  size = arg_parsers.BinarySize(
      suggested_binary_size_scales=['MB', 'GB'], default_unit='MB')
  return int(size(value) / 1024 / 1024)


def Parameters(value):
  """Declarative command argument type for parameters flag."""
  return arg_parsers.ArgDict(key_type=_FormatExtendedOptions)(value)


def _FormatExtendedOptions(key):
  """Replaces dash with underscore for extended options parameters."""
  if key in MEMCACHE_EXTENDED_OPTIONS:
    return key.replace('-', '_')
  return key


def ChooseUpdateMethod(unused_ref, args):
  if args.IsSpecified('parameters'):
    return 'updateParameters'
  return 'patch'


def CreateUpdateRequest(ref, args):
  """Returns an Update or UpdateParameters request depending on the args given."""
  messages = memcache.Messages(ref.GetCollectionInfo().api_version)
  if args.IsSpecified('parameters'):
    params = encoding.DictToMessage(args.parameters,
                                    messages.MemcacheParameters.ParamsValue)
    parameters = messages.MemcacheParameters(params=params)
    param_req = messages.UpdateParametersRequest(
        updateMask='params', parameters=parameters)
    request = (
        messages.MemcacheProjectsLocationsInstancesUpdateParametersRequest(
            name=ref.RelativeName(), updateParametersRequest=param_req))
  else:
    mask = []
    instance = messages.Instance()
    if args.IsSpecified('display_name'):
      mask.append('displayName')
      instance.displayName = args.display_name
    if args.IsSpecified('node_count'):
      mask.append('nodeCount')
      instance.nodeCount = args.node_count
    if args.IsSpecified('labels'):
      mask.append('labels')
      instance.labels = messages.Instance.LabelsValue(
          additionalProperties=args.labels)
    update_mask = ','.join(mask)
    request = (
        messages.MemcacheProjectsLocationsInstancesPatchRequest(
            name=ref.RelativeName(), instance=instance, updateMask=update_mask))

  return request
