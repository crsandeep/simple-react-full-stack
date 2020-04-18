# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Command for updating networks."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.networks import flags
from googlecloudsdk.command_lib.compute.networks import network_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  r"""Update a Google Compute Engine Network.

  *{command}* is used to update virtual networks. The updates that
  cabe be performed on a network are changing the BGP routing mode
  and switching from auto subnet mode to custom subnet mode. Switching
  from auto subnet mode to custom subnet mode cannot be undone.

  ## EXAMPLES

  To update regional network with the name 'network-name' to global, run:

    $ {command} network-name \
      --bgp-routing-mode=global

  To update an auto subnet mode network with the name 'network-name' to custom
  subnet mode, run:

    $ {command} network-name \
      --switch-to-custom-subnet-mode

  """

  NETWORK_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.NETWORK_ARG = flags.NetworkArgument()
    cls.NETWORK_ARG.AddArgument(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    network_utils.AddUpdateArgs(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    messages = holder.client.messages
    service = holder.client.apitools_client.networks

    network_ref = self.NETWORK_ARG.ResolveAsResource(args, holder.resources)

    if args.switch_to_custom_subnet_mode:
      prompt_msg = 'Network [{0}] will be switched to custom mode. '.format(
          network_ref.Name()) + 'This operation cannot be undone.'
      console_io.PromptContinue(
          message=prompt_msg, default=True, cancel_on_no=True)
      result = service.SwitchToCustomMode(
          messages.ComputeNetworksSwitchToCustomModeRequest(
              project=network_ref.project, network=network_ref.Name()))
      operation_ref = resources.REGISTRY.Parse(
          result.name,
          params={'project': network_ref.project},
          collection='compute.globalOperations')

      if args.async_:
        log.UpdatedResource(
            operation_ref,
            kind='network {0}'.format(network_ref.Name()),
            is_async=True,
            details='Run the [gcloud compute operations describe] command '
            'to check the status of this operation.')
        return result

      operation_poller = poller.Poller(service, network_ref)
      return waiter.WaitFor(operation_poller, operation_ref,
                            'Switching network to custom-mode')

    network_resource = messages.Network()
    should_patch = False
    if getattr(args, 'mtu', None) is not None:
      network_resource.mtu = args.mtu
      should_patch = True

    if args.bgp_routing_mode:
      should_patch = True
      network_resource.routingConfig = messages.NetworkRoutingConfig()
      network_resource.routingConfig.routingMode = (
          messages.NetworkRoutingConfig.RoutingModeValueValuesEnum(
              args.bgp_routing_mode.upper()))

    if should_patch:
      resource = service.Patch(
          messages.ComputeNetworksPatchRequest(
              project=network_ref.project,
              network=network_ref.Name(),
              networkResource=network_resource))

    return resource


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(Update):
  """Update a Google Compute Engine Network."""

  @classmethod
  def Args(cls, parser):
    cls.NETWORK_ARG = flags.NetworkArgument()
    cls.NETWORK_ARG.AddArgument(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    network_utils.AddUpdateArgsAlpha(parser)


Update.detailed_help = {
    'brief':
        'Update a Google Compute Engine network',
    'DESCRIPTION':
        """\

        *{command}* is used to update Google Compute Engine networks."""
}
