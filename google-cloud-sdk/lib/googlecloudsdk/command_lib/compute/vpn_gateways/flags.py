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
"""Flags and helpers for the compute vpn-gateways commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import flags as compute_flags

# The default output format for the list sub-command.
DEFAULT_LIST_FORMAT = """\
    table(
      name,
      vpnInterfaces[0].ipAddress:label=INTERFACE0,
      vpnInterfaces[1].ipAddress:label=INTERFACE1,
      network.basename(),
      region.basename()
    )"""


class VpnGatewaysCompleter(compute_completers.ListCommandCompleter):
  """A VPN Gateway completer for a resource argument."""

  def __init__(self, **kwargs):
    super(VpnGatewaysCompleter, self).__init__(
        collection='compute.vpnGateways',
        list_command='alpha compute vpn-gateways list --uri',
        **kwargs)


def GetVpnGatewayArgument(required=True, plural=False):
  """Returns the resource argument object for the VPN Gateway flag."""
  return compute_flags.ResourceArgument(
      resource_name='VPN Gateway',
      completer=VpnGatewaysCompleter,
      plural=plural,
      custom_plural='VPN Gateways',
      required=required,
      regional_collection='compute.vpnGateways',
      region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION)


def GetVpnGatewayArgumentForOtherResource(required=False):
  """Returns the flag for specifying the VPN Gateway."""
  return compute_flags.ResourceArgument(
      name='--vpn-gateway',
      resource_name='VPN Gateway',
      completer=VpnGatewaysCompleter,
      plural=False,
      required=required,
      regional_collection='compute.vpnGateways',
      short_help=(
          'Reference to a VPN gateway, this flag is used for creating '
          'HA VPN tunnels.'
      ),
      region_explanation=('Should be the same as region, if not specified, '
                          'it will be automatically set.'),
      detailed_help="""\
        Reference to a Highly Available VPN Gateway.
        """)


def GetPeerVpnGatewayArgumentForOtherResource(required=False):
  """Returns the flag for specifying the peer VPN Gateway."""
  return compute_flags.ResourceArgument(
      name='--peer-gcp-gateway',
      resource_name='VPN Gateway',
      completer=VpnGatewaysCompleter,
      plural=False,
      required=required,
      regional_collection='compute.vpnGateways',
      short_help=(
          'Peer side Highly Available VPN Gateway representing the remote '
          'tunnel endpoint, this flag is used when creating HA VPN tunnels '
          'from Google Cloud to Google Cloud.'
          'Either --peer-external-gateway or --peer-gcp-gateway must be specified when '
          'creating VPN tunnels from High Available VPN gateway.'),
      region_explanation=('Should be the same as region, if not specified, '
                          'it will be automatically set.'),
      detailed_help="""\
        Reference to the peer side Highly Available VPN Gateway.
        """)


def GetDescriptionFlag():
  """Returns the flag for VPN Gateway description."""
  return base.Argument(
      '--description',
      help='An optional, textual description for the VPN Gateway.')
