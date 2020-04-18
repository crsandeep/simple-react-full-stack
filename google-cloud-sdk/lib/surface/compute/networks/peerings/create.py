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
"""Command for creating network peerings."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import batch_helper
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.networks.peerings import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


def _MakeRequests(client, requests, is_async):
  """Helper for making asynchronous or synchronous peering creation requests."""
  if is_async:
    responses, errors = batch_helper.MakeRequests(
        requests=requests,
        http=client.apitools_client.http,
        batch_url=client.batch_url)
    if not errors:
      for operation in responses:
        log.status.write('Creating network peering for [{0}]\n'.format(
            operation.targetLink))
        log.status.write('Monitor its progress at [{0}]\n'.format(
            operation.selfLink))
    else:
      utils.RaiseToolException(errors)
  else:
    # We want to run through the generator that MakeRequests returns in order
    # to actually make the requests.
    responses = client.MakeRequests(requests)

  return responses


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.Command):
  r"""Create a Google Compute Engine network peering.

  *{command}* is used to create peerings between virtual networks. Each side of
  a peering association is set up independently. Peering will be active only
  when the configuration from both sides matches.

  ## EXAMPLES

  To create a network peering with the name 'peering-name' between the network
  'local-network' and the network 'peer-network', run:

    $ {command} peering-name \
      --network=local-network \
      --peer-network=peer-network

  """

  enable_custom_route = False
  enable_subnet_routes_with_public_ip = False
  enable_nested_network_peering = False

  @classmethod
  def ArgsCommon(cls, parser):

    parser.add_argument('name', help='The name of the peering.')

    parser.add_argument(
        '--network',
        required=True,
        help='The name of the network in the current project to be peered '
        'with the peer network.')

    parser.add_argument(
        '--peer-network',
        required=True,
        help='The name of the network to be peered with the current network.')

    parser.add_argument(
        '--peer-project',
        required=False,
        help='The name of the project for the peer network.  If not specified, '
        'defaults to current project.')

    base.ASYNC_FLAG.AddToParser(parser)

    if cls.enable_custom_route:
      flags.AddImportCustomRoutesFlag(parser)
      flags.AddExportCustomRoutesFlag(parser)

    if cls.enable_subnet_routes_with_public_ip:
      flags.AddImportSubnetRoutesWithPublicIpFlag(parser)
      flags.AddExportSubnetRoutesWithPublicIpFlag(parser)

  @classmethod
  def Args(cls, parser):
    cls.ArgsCommon(parser)
    parser.add_argument(
        '--auto-create-routes',
        action='store_true',
        default=False,
        required=False,
        help='If set, will automatically create routes for the network '
        'peering.  Note that a backend error will be returned if this is '
        'not set.')

  def Run(self, args):
    """Issues the request necessary for adding the peering."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    peer_network_ref = resources.REGISTRY.Parse(
        args.peer_network,
        params={
            'project':
                args.peer_project or properties.VALUES.core.project.GetOrFail
        },
        collection='compute.networks')

    if self.enable_nested_network_peering:
      network_peering = client.messages.NetworkPeering(
          name=args.name,
          network=peer_network_ref.RelativeName(),
          exchangeSubnetRoutes=True)

      if self.enable_custom_route:
        network_peering.exportCustomRoutes = args.export_custom_routes
        network_peering.importCustomRoutes = args.import_custom_routes

      if self.enable_subnet_routes_with_public_ip:
        network_peering.exportSubnetRoutesWithPublicIp = \
          args.export_subnet_routes_with_public_ip
        network_peering.importSubnetRoutesWithPublicIp = \
          args.import_subnet_routes_with_public_ip

      request = client.messages.ComputeNetworksAddPeeringRequest(
          network=args.network,
          networksAddPeeringRequest=client.messages.NetworksAddPeeringRequest(
              networkPeering=network_peering),
          project=properties.VALUES.core.project.GetOrFail())
    else:
      request = client.messages.ComputeNetworksAddPeeringRequest(
          network=args.network,
          networksAddPeeringRequest=client.messages.NetworksAddPeeringRequest(
              autoCreateRoutes=args.auto_create_routes,
              name=args.name,
              peerNetwork=peer_network_ref.RelativeName()),
          project=properties.VALUES.core.project.GetOrFail())

    requests = [(client.apitools_client.networks, 'AddPeering', request)]
    return _MakeRequests(client, requests, args.async_)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  r"""Create a Google Compute Engine network peering.

  *{command}* is used to create peerings between virtual networks. Each side of
  a peering association is set up independently. Peering will be active only
  when the configuration from both sides matches.

  ## EXAMPLES

  To create a network peering with the name 'peering-name' between the network
  'local-network' and the network 'peer-network' which exports and imports
  custom routes, run:

    $ {command} peering-name \
      --network=local-network \
      --peer-network=peer-network \
      --export-custom-routes \
      --import-custom-routes

  """

  enable_custom_route = True
  enable_nested_network_peering = True

  @classmethod
  def Args(cls, parser):
    cls.ArgsCommon(parser)

    action = actions.DeprecationAction(
        'auto-create-routes',
        warn='Flag --auto-create-routes is deprecated and will '
        'be removed in a future release.',
        action='store_true')
    parser.add_argument(
        '--auto-create-routes',
        action=action,
        default=False,
        required=False,
        help='If set, will automatically create routes for the '
        'network peering. Flag auto-create-routes is deprecated. Peer network '
        'subnet routes are always created in a network when peered.')


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(CreateBeta):
  r"""Create a Google Compute Engine network peering.

  *{command}* is used to create peerings between virtual networks. Each side of
  a peering association is set up independently. Peering will be active only
  when the configuration from both sides matches.

  ## EXAMPLES

  To create a network peering with the name 'peering-name' between the network
  'local-network' and the network 'peer-network' which exports and imports
  custom routes and subnet routes with public IPs, run:

    $ {command} peering-name \
      --network=local-network \
      --peer-network=peer-network \
      --export-custom-routes \
      --import-custom-routes \
      --export-subnet-routes-with-public-ip \
      --import-subnet-routes-with-public-ip

  """

  enable_subnet_routes_with_public_ip = True
