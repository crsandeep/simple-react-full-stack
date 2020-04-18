# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""gcloud dns managed-zone update command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dns import managed_zones
from googlecloudsdk.api_lib.dns import util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dns import flags
from googlecloudsdk.command_lib.dns import util as command_util
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import properties


def _CommonArgs(parser, messages):
  flags.GetZoneResourceArg(
      'The name of the managed-zone to be updated.').AddToParser(parser)
  flags.AddCommonManagedZonesDnssecArgs(parser, messages)
  flags.GetManagedZonesDescriptionArg().AddToParser(parser)
  labels_util.AddUpdateLabelsFlags(parser)
  flags.GetManagedZoneNetworksArg().AddToParser(parser)
  base.ASYNC_FLAG.AddToParser(parser)
  flags.GetForwardingTargetsArg().AddToParser(parser)
  flags.GetDnsPeeringArgs().AddToParser(parser)


def _Update(zones_client,
            args,
            private_visibility_config=None,
            forwarding_config=None,
            peering_config=None,
            reverse_lookup_config=None):
  """Helper function to perform the update."""
  zone_ref = args.CONCEPTS.zone.Parse()

  dnssec_config = command_util.ParseDnssecConfigArgs(args,
                                                     zones_client.messages)
  labels_update = labels_util.ProcessUpdateArgsLazy(
      args, zones_client.messages.ManagedZone.LabelsValue,
      lambda: zones_client.Get(zone_ref).labels)

  kwargs = {}
  if private_visibility_config:
    kwargs['private_visibility_config'] = private_visibility_config
  if forwarding_config:
    kwargs['forwarding_config'] = forwarding_config
  if peering_config:
    kwargs['peering_config'] = peering_config
  if reverse_lookup_config:
    kwargs['reverse_lookup_config'] = reverse_lookup_config
  return zones_client.Patch(
      zone_ref,
      args.async_,
      dnssec_config=dnssec_config,
      description=args.description,
      labels=labels_update.GetOrNone(),
      **kwargs)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class UpdateGA(base.UpdateCommand):
  """Update an existing Cloud DNS managed-zone.

  Update an existing Cloud DNS managed-zone.

  ## EXAMPLES

  To change the description of a managed-zone, run:

    $ {command} my_zone --description="Hello, world!"

  """

  @staticmethod
  def Args(parser):
    messages = apis.GetMessagesModule('dns', 'v1')
    _CommonArgs(parser, messages)

  def Run(self, args):
    zones_client = managed_zones.Client.FromApiVersion('v1')
    messages = apis.GetMessagesModule('dns', 'v1')

    forwarding_config = None
    if args.forwarding_targets:
      forwarding_config = command_util.ParseManagedZoneForwardingConfig(
          args.forwarding_targets, messages)

    peering_config = None
    if args.target_project and args.target_network:
      peering_network = 'https://www.googleapis.com/compute/v1/projects/{}/global/networks/{}'.format(
          args.target_project, args.target_network)
      peering_config = messages.ManagedZonePeeringConfig()
      peering_config.targetNetwork = messages.ManagedZonePeeringConfigTargetNetwork(
          networkUrl=peering_network)

    visibility_config = None
    if args.networks:
      networks = args.networks if args.networks != [''] else []

      def GetNetworkSelfLink(network):
        return util.GetRegistry('v1').Parse(
            network,
            collection='compute.networks',
            params={
                'project': properties.VALUES.core.project.GetOrFail
            }).SelfLink()

      network_urls = [GetNetworkSelfLink(n) for n in networks]
      network_configs = [
          messages.ManagedZonePrivateVisibilityConfigNetwork(networkUrl=nurl)
          for nurl in network_urls
      ]
      visibility_config = messages.ManagedZonePrivateVisibilityConfig(
          networks=network_configs)

    return _Update(zones_client, args,
                   private_visibility_config=visibility_config,
                   forwarding_config=forwarding_config,
                   peering_config=peering_config)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBeta(base.UpdateCommand):
  """Update an existing Cloud DNS managed-zone.

  Update an existing Cloud DNS managed-zone.

  ## EXAMPLES

  To change the description of a managed-zone, run:

    $ {command} my_zone --description="Hello, world!"

  """

  @staticmethod
  def Args(parser):
    messages = apis.GetMessagesModule('dns', 'v1beta2')
    _CommonArgs(parser, messages)
    flags.GetPrivateForwardingTargetsArg().AddToParser(parser)
    flags.GetReverseLookupArg().AddToParser(parser)

  def Run(self, args):
    api_version = util.GetApiFromTrack(self.ReleaseTrack())
    zones_client = managed_zones.Client.FromApiVersion(api_version)
    messages = zones_client.messages

    forwarding_config = None
    if args.forwarding_targets or args.private_forwarding_targets:
      forwarding_config = command_util.ParseManagedZoneForwardingConfigWithForwardingPath(
          messages=messages,
          server_list=args.forwarding_targets,
          private_server_list=args.private_forwarding_targets)
    else:
      forwarding_config = None

    peering_config = None
    if args.target_project and args.target_network:
      peering_network = 'https://www.googleapis.com/compute/v1/projects/{}/global/networks/{}'.format(
          args.target_project, args.target_network)
      peering_config = messages.ManagedZonePeeringConfig()
      peering_config.targetNetwork = messages.ManagedZonePeeringConfigTargetNetwork(
          networkUrl=peering_network)

    visibility_config = None
    if args.networks:
      networks = args.networks if args.networks != [''] else []

      def GetNetworkSelfLink(network):
        return util.GetRegistry(api_version).Parse(
            network,
            collection='compute.networks',
            params={
                'project': properties.VALUES.core.project.GetOrFail
            }).SelfLink()

      network_urls = [GetNetworkSelfLink(n) for n in networks]
      network_configs = [
          messages.ManagedZonePrivateVisibilityConfigNetwork(networkUrl=nurl)
          for nurl in network_urls
      ]
      visibility_config = messages.ManagedZonePrivateVisibilityConfig(
          networks=network_configs)

    reverse_lookup_config = None
    if args.IsSpecified(
        'managed_reverse_lookup') and args.managed_reverse_lookup:
      reverse_lookup_config = messages.ManagedZoneReverseLookupConfig()

    return _Update(
        zones_client,
        args,
        private_visibility_config=visibility_config,
        forwarding_config=forwarding_config,
        peering_config=peering_config,
        reverse_lookup_config=reverse_lookup_config)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(UpdateBeta):
  """Update an existing Cloud DNS managed-zone.

  Update an existing Cloud DNS managed-zone.

  ## EXAMPLES

  To change the description of a managed-zone, run:

    $ {command} my_zone --description="Hello, world!"

  """

  @staticmethod
  def Args(parser):
    messages = apis.GetMessagesModule('dns', 'v1alpha2')
    _CommonArgs(parser, messages)
    flags.GetPrivateForwardingTargetsArg().AddToParser(parser)
    flags.GetReverseLookupArg().AddToParser(parser)
