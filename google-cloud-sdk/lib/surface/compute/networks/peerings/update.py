# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Command for updating network peerings."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute.networks.peerings import flags
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Update(base.Command):
  r"""Update a Google Compute Engine network peering.

  ## EXAMPLES

  To update the peering named peering-name to both export and import custom
  routes, run:

    $ {command} peering-name \
      --export-custom-routes \
      --import-custom-routes

  """

  enable_subnet_routes_with_public_ip = False

  @classmethod
  def Args(cls, parser):
    parser.add_argument('name', help='The name of the peering.')
    parser.add_argument(
        '--network',
        required=True,
        help='The name of the network in the current project to be peered '
        'with the peer network.')
    flags.AddImportCustomRoutesFlag(parser)
    flags.AddExportCustomRoutesFlag(parser)

    if cls.enable_subnet_routes_with_public_ip:
      flags.AddImportSubnetRoutesWithPublicIpFlag(parser)
      flags.AddExportSubnetRoutesWithPublicIpFlag(parser)

  def Run(self, args):
    """Issues the request necessary for updating the peering."""
    self.ValidateArgs(args)
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = holder.client.messages
    network_peering = messages.NetworkPeering(
        name=args.name,
        exportCustomRoutes=args.export_custom_routes,
        importCustomRoutes=args.import_custom_routes)

    if self.enable_subnet_routes_with_public_ip:
      network_peering.exportSubnetRoutesWithPublicIp = args.export_subnet_routes_with_public_ip
      network_peering.importSubnetRoutesWithPublicIp = args.import_subnet_routes_with_public_ip

    request = client.messages.ComputeNetworksUpdatePeeringRequest(
        network=args.network,
        networksUpdatePeeringRequest=client.messages
        .NetworksUpdatePeeringRequest(networkPeering=network_peering),
        project=properties.VALUES.core.project.GetOrFail())

    return client.MakeRequests([(client.apitools_client.networks,
                                 'UpdatePeering', request)])

  def ValidateArgs(self, args):
    """Validate arguments."""
    check_args = [
        args.export_custom_routes is None,
        args.import_custom_routes is None]

    if self.enable_subnet_routes_with_public_ip:
      check_args.extend([
          args.export_subnet_routes_with_public_ip is None,
          args.import_subnet_routes_with_public_ip is None])

    if all(check_args):
      raise exceptions.ToolException('At least one property must be modified.')


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(Update):
  r"""Update a Google Compute Engine network peering.

  ## EXAMPLES

  To update the peering named peering-name to both export and import custom
  routes, run:

    $ {command} peering-name \
      --export-custom-routes \
      --import-custom-routes

  To update the peering named peering-name to both export and import subnet
  routes with public ip, run:

    $ {command} peering-name \
      --export-subnet-routes-with-public-ip \
      --import-subnet-routes-with-public-ip

  """
  enable_subnet_routes_with_public_ip = True
