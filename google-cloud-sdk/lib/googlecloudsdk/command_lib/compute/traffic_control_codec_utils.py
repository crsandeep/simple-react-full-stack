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
"""Common codecs needed for export sub-commands used for L7 traffic control."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.util import apis


def RegisterL7TrafficControlCodecs(api_version):
  """Registers custom field codec for L7 traffic control int64 proto fields."""
  msgs = apis.GetMessagesModule('compute', api_version)

  def _EncodeInt64Field(unused_field, value):
    int_value = encoding.CodecResult(value=value, complete=True)
    return int_value

  def _DecodeInt64Field(unused_field, value):
    # Don't need to do anything special, they're decoded just fine
    return encoding.CodecResult(value=value, complete=True)

  # Registers custom Int64 codecs for compute.Duration
  duration_proto = msgs.Duration
  encoding.RegisterCustomFieldCodec(_EncodeInt64Field, _DecodeInt64Field)(
      duration_proto.seconds)

  # Registers custom Int64 codecs for compute.Int64RangeMatch
  int64_range_match_proto = msgs.Int64RangeMatch
  encoding.RegisterCustomFieldCodec(_EncodeInt64Field, _DecodeInt64Field)(
      int64_range_match_proto.rangeStart)
  encoding.RegisterCustomFieldCodec(_EncodeInt64Field, _DecodeInt64Field)(
      int64_range_match_proto.rangeEnd)
