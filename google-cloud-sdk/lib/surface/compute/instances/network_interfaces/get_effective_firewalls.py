# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Command for getting the effective firewalls applied on instance network interfaces."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import firewalls_utils
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.instances import flags as instances_flags


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class GetEffectiveFirewalls(base.DescribeCommand, base.ListCommand):
  r"""Get the effective firewalls on a Google Compute Engine virtual machine network interface.

  *{command}* Get the effective firewalls applied on the network interfaces of
  a Google Compute Engine virtual machine. For example:

    $ {command} example-instance --zone us-central1-a

  gets the effective firewalls applied on the default network interface of a
  Google Compute Engine virtual machine "example-instance" in zone
  us-central1-a
  """

  @staticmethod
  def Args(parser):
    instances_flags.INSTANCE_ARG.AddArgument(parser)
    parser.add_argument(
        '--network-interface',
        default='nic0',
        help='The name of the network interface to get the effective firewalls.'
    )
    parser.display_info.AddFormat(
        firewalls_utils.EFFECTIVE_FIREWALL_LIST_FORMAT)
    lister.AddBaseListerArgs(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = holder.client.messages

    instance_ref = instances_flags.INSTANCE_ARG.ResolveAsResource(
        args, holder.resources,
        scope_lister=flags.GetDefaultScopeLister(holder.client))

    instance = client.apitools_client.instances.Get(
        messages.ComputeInstancesGetRequest(**instance_ref.AsDict()))
    for i in instance.networkInterfaces:
      if i.name == args.network_interface:
        break
    else:
      raise exceptions.UnknownArgumentException(
          'network-interface',
          'Instance does not have a network interface [{}], '
          'present interfaces are [{}].'.format(
              args.network_interface, ', '.join(
                  [i.name for i in instance.networkInterfaces])))

    request = messages.ComputeInstancesGetEffectiveFirewallsRequest(
        project=instance_ref.project,
        instance=instance_ref.instance,
        zone=instance_ref.zone,
        networkInterface=args.network_interface)
    res = client.apitools_client.instances.GetEffectiveFirewalls(request)
    org_firewall = []
    network_firewall = []
    if hasattr(res, 'firewalls'):
      network_firewall = firewalls_utils.SortNetworkFirewallRules(
          client, res.firewalls)

    if hasattr(res, 'organizationFirewalls'):
      for sp in res.organizationFirewalls:
        org_firewall_rule = firewalls_utils.SortOrgFirewallRules(
            client, sp.rules)
        org_firewall.append(
            client.messages
            .InstancesGetEffectiveFirewallsResponseOrganizationFirewallPolicy(
                id=sp.id, rules=org_firewall_rule))
    if args.IsSpecified('format') and args.format == 'json':
      return client.messages.InstancesGetEffectiveFirewallsResponseOrganizationFirewallPolicy(
          organizationFirewalls=org_firewall, firewalls=network_firewall)

    result = []
    for sp in org_firewall:
      result.extend(
          firewalls_utils.ConvertOrgSecurityPolicyRulesToEffectiveFwRules(sp))
    result.extend(
        firewalls_utils.ConvertNetworkFirewallRulesToEffectiveFwRules(
            network_firewall))
    return result


GetEffectiveFirewalls.detailed_help = {
    'EXAMPLES':
        """\
    To get the effective firewalls of instance with name example-instance, run:

      $ {command} example-instance,
    To show all fields of the firewall rules, please show in JSON format with
    option --format=json
    """,
}
