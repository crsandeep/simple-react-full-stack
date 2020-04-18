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
"""Utility functions for gcloud spanner emulator."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.command_lib.emulators import util
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core.util import platforms
import ipaddress
import six

SPANNER_EMULATOR_PROPERTY_PREFIX = 'spanner'
SPANNER_EMULATOR_COMPONENT_ID = 'cloud-spanner-emulator'
SPANNER_EMULATOR_TITLE = 'Google Cloud Spanner Emulator'
SPANNER_EMULATOR_EXECUTABLE_DIR = 'cloud_spanner_emulator'
SPANNER_EMULATOR_EXECUTABLE_FILE = 'gateway_main'
SPANNER_EMULATOR_DOCKER_IMAGE = 'gcr.io/cloud-spanner-emulator/emulator:0.7.3'
SPANNER_EMULATOR_DEFAULT_GRPC_PORT = 9010
SPANNER_EMULATOR_DEFAULT_REST_PORT = 9020


def GetDataDir():
  return util.GetDataDir(SPANNER_EMULATOR_PROPERTY_PREFIX)


def _BuildStartArgsForDocker(args):
  """Builds arguments for starting the spanner emulator under docker."""

  # We use -p on Docker to enforce the specified hostname, but -p requires
  # ip addresses. We handle the localhost case specifically as it is the
  # common case.
  host_ip = args.host_port.host
  if host_ip == 'localhost':
    host_ip = '127.0.0.1'
  try:
    ipaddress.ip_address(host_ip)
  except ValueError:
    raise ValueError('When using docker, hostname specified via --host-port '
                     'must be an IPV4 or IPV6 address, found ' + host_ip)

  return execution_utils.ArgsForExecutableTool(
      'docker', 'run', '-p',
      '{}:{}:{}'.format(host_ip, args.host_port.port,
                        SPANNER_EMULATOR_DEFAULT_GRPC_PORT), '-p',
      '{}:{}:{}'.format(host_ip, args.rest_port,
                        SPANNER_EMULATOR_DEFAULT_REST_PORT),
      SPANNER_EMULATOR_DOCKER_IMAGE)


def _BuildStartArgsForNativeExecutable(args):
  spanner_executable = os.path.join(util.GetCloudSDKRoot(), 'bin',
                                    SPANNER_EMULATOR_EXECUTABLE_DIR,
                                    SPANNER_EMULATOR_EXECUTABLE_FILE)
  return execution_utils.ArgsForExecutableTool(spanner_executable, '--hostname',
                                               args.host_port.host,
                                               '--grpc_port',
                                               args.host_port.port,
                                               '--http_port',
                                               six.text_type(args.rest_port))


def _BuildStartArgs(args):
  if (platforms.OperatingSystem.Current() is not platforms.OperatingSystem.LINUX
      or args.use_docker):
    return _BuildStartArgsForDocker(args)
  else:
    return _BuildStartArgsForNativeExecutable(args)


def GetEnv(args):
  """Returns an environment variable mapping from an argparse.Namespace."""
  return {
      'SPANNER_EMULATOR_HOST':
          '{}:{}'.format(args.host_port.host, args.host_port.port)
  }


def Start(args):
  spanner_args = _BuildStartArgs(args)
  log.status.Print('Executing: {0}'.format(' '.join(spanner_args)))
  with util.Exec(spanner_args) as spanner_process:
    util.WriteEnvYaml(GetEnv(args), GetDataDir())
    util.PrefixOutput(spanner_process, SPANNER_EMULATOR_COMPONENT_ID)
