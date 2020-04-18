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
"""Command to create a new VPN gateway."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.vpn_gateways import vpn_gateways_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.networks import flags as network_flags
from googlecloudsdk.command_lib.compute.vpn_gateways import flags

_VPN_GATEWAY_ARG = flags.GetVpnGatewayArgument()
_NETWORK_ARG = network_flags.NetworkArgumentForOtherResource("""\
  A reference to a network to which the VPN gateway is attached.
  """)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a new Google Compute Engine Highly Available VPN gateway.

  *{command}* creates a new Highly Available VPN gateway.

  Highly Available VPN Gateway provides a means to create a VPN solution with a
  higher availability SLA compared to Classic Target VPN Gateway.
  Highly Available VPN gateways are simply referred to as VPN gateways in the
  API documentation and gcloud commands.
  A VPN Gateway can reference one or more VPN tunnels that connect it to
  external VPN gateways or Cloud VPN Gateways.
  """
  detailed_help = {
      'EXAMPLES':
          """\
          To create a VPN gateway, run:

              $ {command} my-vpn-gateway --region=us-central1 --network=default
          """
  }

  @staticmethod
  def Args(parser):
    """Set up arguments for this command."""
    parser.display_info.AddFormat(flags.DEFAULT_LIST_FORMAT)
    _NETWORK_ARG.AddArgument(parser)
    _VPN_GATEWAY_ARG.AddArgument(parser, operation_type='create')
    flags.GetDescriptionFlag().AddToParser(parser)
    parser.display_info.AddCacheUpdater(flags.VpnGatewaysCompleter)

  def Run(self, args):
    """Issues the request to create a new VPN gateway."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    helper = vpn_gateways_utils.VpnGatewayHelper(holder)
    vpn_gateway_ref = _VPN_GATEWAY_ARG.ResolveAsResource(args, holder.resources)
    network_ref = _NETWORK_ARG.ResolveAsResource(args, holder.resources)

    vpn_gateway_to_insert = helper.GetVpnGatewayForInsert(
        name=vpn_gateway_ref.Name(),
        description=args.description,
        network=network_ref.SelfLink())
    operation_ref = helper.Create(vpn_gateway_ref, vpn_gateway_to_insert)
    return helper.WaitForOperation(vpn_gateway_ref, operation_ref,
                                   'Creating VPN Gateway')
