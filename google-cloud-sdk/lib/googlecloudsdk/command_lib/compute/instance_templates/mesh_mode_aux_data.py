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
"""Auxiliary data for implementing Mesh mode flags Instance Templates."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import enum


class MeshModes(str, enum.Enum):
  ON = 'ON'
  OFF = 'OFF'


startup_script = """#! /bin/bash
sudo adduser --system --disabled-login envoy
sudo gsutil cp gs://gce-mesh/mesh-agent/releases/mesh-agent-0.1.tgz /home/envoy
sudo tar -xzf /home/envoy/mesh-agent-0.1.tgz -C /home/envoy
sudo /home/envoy/mesh-agent/mesh-agent-bootstrap.sh"""
