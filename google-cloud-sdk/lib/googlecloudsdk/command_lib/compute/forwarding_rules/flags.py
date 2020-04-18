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

"""Flags and helpers for the compute forwarding-rules commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.addresses import flags as addresses_flags
from googlecloudsdk.command_lib.util import completers


FORWARDING_RULES_OVERVIEW = """\
        A forwarding rule directs traffic that matches a destination IP address
        (and possibly a TCP or UDP port) to a forwarding target (load balancer,
        VPN gateway or VM instance).

        Forwarding rules can be either global or regional, specified with the
        ``--global'' or ``--region=REGION'' flags. For more information about
        the scope of a forwarding rule, refer to
        https://cloud.google.com/load-balancing/docs/forwarding-rule-concepts.

        Forwarding rules can be external, internal, internal managed, or
        internal self-managed, specified with the
        ``--load-balancing-scheme=[EXTERNAL|INTERNAL|INTERNAL_MANAGED|INTERNAL_SELF_MANAGED]''
        flag. External forwarding rules are accessible from the internet, while
        internal forwarding rules are only accessible from within their VPC
        networks. You can specify a reserved static external or internal IP
        address with the ``--address=ADDRESS'' flag for the forwarding rule.
        Otherwise, if the flag is unspecified, an ephemeral IP address is
        automatically assigned (global IP addresses for global forwarding rules
        and regional IP addresses for regional forwarding rules); an internal
        forwarding rule is automatically assigned an ephemeral internal IP
        address from the subnet specified with the ``--subnet'' flag. You must
        provide an IP address for an internal self-managed forwarding rule.

        Different types of load balancers work at different layers of the OSI
        networking model (http://en.wikipedia.org/wiki/Network_layer). Layer 3/4
        targets include target pools, target SSL proxies, target TCP proxies,
        and backend services. Layer 7 targets include target HTTP proxies and
        target HTTPS proxies. For more information, refer to
        https://cloud.google.com/load-balancing/docs/forwarding-rule-concepts.
        """


FORWARDING_RULES_OVERVIEW_ALPHA = """\
        A forwarding rule directs traffic that matches a destination IP address
        (and possibly a TCP or UDP port) to a forwarding target (load balancer,
        VPN gateway or VM instance).

        Forwarding rules can be either global or regional, specified with the
        ``--global'' or ``--region=REGION'' flag. For more information about
        the scope of a forwarding rule, refer to
        https://cloud.google.com/load-balancing/docs/forwarding-rule-concepts.

        Forwarding rules can be external, internal, internal managed, or
        internal self-managed, specified with the
        ``--load-balancing-scheme=[EXTERNAL|INTERNAL|INTERNAL_MANAGED|INTERNAL_SELF_MANAGED]''
        flag. External forwarding rules are accessible from the internet, while
        internal forwarding rules are only accessible from within their VPC
        networks. You can specify a reserved static external or internal IP
        address with the ``--address=ADDRESS'' flag for the forwarding rule.
        Otherwise, if the flag is unspecified, an ephemeral IP address is
        automatically assigned (global IP addresses for global forwarding rules
        and regional IP addresses for regional forwarding rules); an internal
        forwarding rule is automatically assigned an ephemeral internal IP
        address from the subnet specified with the ``--subnet'' flag. You must
        provide an IP address for an internal self-managed forwarding rule.

        Different types of load balancers work at different layers of the OSI
        networking model (http://en.wikipedia.org/wiki/Network_layer). Layer 3
        targets include target pools, target SSL proxies, target TCP proxies,
        and backend services. Layer 7 targets include target HTTP proxies,
        target HTTPS and target gRPC proxies. For more information, refer to
        https://cloud.google.com/load-balancing/docs/forwarding-rule-concepts.
        """


class ForwardingRulesZonalCompleter(compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(ForwardingRulesZonalCompleter, self).__init__(
        collection='compute.forwardingRules',
        list_command=('compute forwarding-rules list --filter=region:* --uri'),
        **kwargs)


class ForwardingRulesGlobalCompleter(
    compute_completers.GlobalListCommandCompleter):

  def __init__(self, **kwargs):
    super(ForwardingRulesGlobalCompleter, self).__init__(
        collection='compute.globalForwardingRules',
        list_command='compute forwarding-rules list --global --uri',
        **kwargs)


class ForwardingRulesCompleter(completers.MultiResourceCompleter):

  def __init__(self, **kwargs):
    super(ForwardingRulesCompleter, self).__init__(
        completers=[ForwardingRulesGlobalCompleter,
                    ForwardingRulesZonalCompleter],
        **kwargs)


def ForwardingRuleArgument(required=True):
  return compute_flags.ResourceArgument(
      resource_name='forwarding rule',
      completer=ForwardingRulesCompleter,
      required=required,
      regional_collection='compute.forwardingRules',
      global_collection='compute.globalForwardingRules',
      region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION)


def ForwardingRuleArgumentPlural(required=True):
  return compute_flags.ResourceArgument(
      resource_name='forwarding rule',
      completer=ForwardingRulesCompleter,
      plural=True,
      required=required,
      regional_collection='compute.forwardingRules',
      global_collection='compute.globalForwardingRules',
      region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION)


def ForwardingRuleArgumentForRoute(required=True):
  return compute_flags.ResourceArgument(
      resource_name='forwarding rule',
      name='--next-hop-ilb',
      completer=ForwardingRulesCompleter,
      plural=False,
      required=required,
      regional_collection='compute.forwardingRules',
      short_help=
      'Target forwarding rule that receives forwarded traffic.',
      region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION)


BACKEND_SERVICE_ARG = compute_flags.ResourceArgument(
    name='--backend-service',
    required=False,
    resource_name='backend service',
    regional_collection='compute.regionBackendServices',
    global_collection='compute.targetBackendServices',
    short_help='Target backend service that receives the traffic.',
    region_explanation=('If not specified, the region is set to the'
                        ' region of the forwarding rule.'))


def NetworkArg(include_l7_internal_load_balancing):
  """Returns the network parameter."""

  load_balancing_scheme = ('--load-balancing-scheme=INTERNAL or ' +
                           '--load-balancing-scheme=INTERNAL_SELF_MANAGED')

  if include_l7_internal_load_balancing:
    load_balancing_scheme += ' or --load-balancing-scheme=INTERNAL_MANAGED'

  return compute_flags.ResourceArgument(
      name='--network',
      required=False,
      resource_name='network',
      global_collection='compute.networks',
      short_help='Network that this forwarding rule applies to.',
      detailed_help="""
          (Only for %s) Network that this
          forwarding rule applies to. If this field is not specified, the default
          network is used. In the absence of the default network, this field
          must be specified.
          """ % load_balancing_scheme)


SUBNET_ARG = compute_flags.ResourceArgument(
    name='--subnet',
    required=False,
    resource_name='subnetwork',
    regional_collection='compute.subnetworks',
    short_help='Subnet that this forwarding rule applies to.',
    detailed_help="""\
        (Only for --load-balancing-scheme=INTERNAL) Subnetwork that this
        forwarding rule applies to. If the network configured for this
        forwarding rule is in auto subnet mode, this flag is optional and the
        subnet in the same region of the forwarding rule is used. However,
        if the network is in custom subnet mode, a subnetwork must be specified.
        """,
    region_explanation=('If not specified, the region is set to the'
                        ' region of the forwarding rule.'))


def TargetGrpcProxyArg():
  """Return a resource argument for parsing a target gRPC proxy."""

  target_grpc_proxy_arg = compute_flags.ResourceArgument(
      name='--target-grpc-proxy',
      required=False,
      resource_name='target gRPC proxy',
      global_collection='compute.targetGrpcProxies',
      short_help='Target gRPC proxy that receives the traffic.',
      detailed_help=('Target gRPC proxy that receives the traffic.'),
      region_explanation=None)
  return target_grpc_proxy_arg


def TargetHttpProxyArg(include_l7_internal_load_balancing=False):
  """Return a resource argument for parsing a target http proxy."""

  target_http_proxy_arg = compute_flags.ResourceArgument(
      name='--target-http-proxy',
      required=False,
      resource_name='http proxy',
      global_collection='compute.targetHttpProxies',
      regional_collection='compute.regionTargetHttpProxies'
      if include_l7_internal_load_balancing else None,
      short_help='Target HTTP proxy that receives the traffic.',
      detailed_help=('Target HTTP proxy that receives the traffic. '
                     'Acceptable values for --ports flag are: 80, 8080.'),
      region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION
      if include_l7_internal_load_balancing else None)
  return target_http_proxy_arg


def TargetHttpsProxyArg(include_l7_internal_load_balancing=False):
  """Return a resource argument for parsing a target https proxy."""

  target_https_proxy_arg = compute_flags.ResourceArgument(
      name='--target-https-proxy',
      required=False,
      resource_name='https proxy',
      global_collection='compute.targetHttpsProxies',
      regional_collection='compute.regionTargetHttpsProxies'
      if include_l7_internal_load_balancing else None,
      short_help='Target HTTPS proxy that receives the traffic.',
      detailed_help=('Target HTTPS proxy that receives the traffic. '
                     'Acceptable values for --ports flag are: 443.'),
      region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION
      if include_l7_internal_load_balancing else None)
  return target_https_proxy_arg

TARGET_INSTANCE_ARG = compute_flags.ResourceArgument(
    name='--target-instance',
    required=False,
    resource_name='target instance',
    zonal_collection='compute.targetInstances',
    short_help='Name of the target instance that receives the traffic.',
    detailed_help=textwrap.dedent("""\
      Name of the target instance that receives the traffic. The
      target instance must be in a zone in the forwarding rule's
      region. Global forwarding rules cannot direct traffic to target
      instances.
      """) + compute_flags.ZONE_PROPERTY_EXPLANATION)

TARGET_POOL_ARG = compute_flags.ResourceArgument(
    name='--target-pool',
    required=False,
    resource_name='target pool',
    regional_collection='compute.targetPools',
    short_help='Target pool that receives the traffic.',
    detailed_help="""\
      Target pool that receives the traffic. The target pool
      must be in the same region as the forwarding rule. Global
      forwarding rules cannot direct traffic to target pools.
      """,
    region_explanation=('If not specified, the region is set to the'
                        ' region of the forwarding rule.'))

TARGET_SSL_PROXY_ARG = compute_flags.ResourceArgument(
    name='--target-ssl-proxy',
    required=False,
    resource_name='ssl proxy',
    global_collection='compute.targetSslProxies',
    short_help='Target SSL proxy that receives the traffic.',
    detailed_help=('Target SSL proxy that receives the traffic. '
                   'Acceptable values for --ports flag are: '
                   '25, 43, 110, 143, 195, 443, 465, 587, '
                   '700, 993, 995, 1883, 5222.'))

TARGET_TCP_PROXY_ARG = compute_flags.ResourceArgument(
    name='--target-tcp-proxy',
    required=False,
    resource_name='tcp proxy',
    global_collection='compute.targetTcpProxies',
    short_help='Target TCP proxy that receives the traffic.',
    detailed_help=('Target TCP proxy that receives the traffic. '
                   'Acceptable values for --ports flag are: '
                   '25, 43, 110, 143, 195, 443, 465, 587, '
                   '700, 993, 995, 1883, 5222.'))

TARGET_VPN_GATEWAY_ARG = compute_flags.ResourceArgument(
    name='--target-vpn-gateway',
    required=False,
    resource_name='VPN gateway',
    regional_collection='compute.targetVpnGateways',
    short_help='Target VPN gateway that receives forwarded traffic.',
    detailed_help=(
        'Target VPN gateway (Cloud VPN Classic gateway) that receives forwarded'
        'traffic. '
        'Acceptable values for --ports flag are: 500, 4500.'),
    region_explanation=('If not specified, the region is set to the'
                        ' region of the forwarding rule.'))


def AddressArgHelp(include_l7_internal_load_balancing):
  """Build the help text for the address argument."""

  lb_schemes = '(EXTERNAL, INTERNAL, INTERNAL_MANAGED'
  if include_l7_internal_load_balancing:
    lb_schemes += ', INTERNAL_MANAGED'
  lb_schemes += ')'

  detailed_help = """\
    IP address that the forwarding rule serves. When a client sends traffic
    to this IP address, the forwarding rule directs the traffic to the target
    that you specify in the forwarding rule.

    If you don't specify a reserved IP address, an ephemeral IP address is
    assigned. You can specify the IP address as a literal IP address or a
    reference to an existing Address resource. The following examples are all
    valid:
    - 100.1.2.3
    - https://compute.googleapis.com/compute/v1/projects/project-1/regions/us-central1/addresses/address-1
    - projects/project-1/regions/us-central1/addresses/address-1
    - regions/us-central1/addresses/address-1
    - global/addresses/address-1
    - address-1

    The load-balancing-scheme (%s) and the forwarding rule's target determine
    the type of IP address that you can use. The address type must be external
    for load-balancing-scheme EXTERNAL, and for the other load-balancing-schemes
    the address must be internal. For detailed information, refer to
    https://cloud.google.com/load-balancing/docs/forwarding-rule-concepts#ip_address_specifications.
  """ % (
      lb_schemes)

  return textwrap.dedent(detailed_help)


def AddressArg(include_l7_internal_load_balancing):
  return compute_flags.ResourceArgument(
      name='--address',
      required=False,
      resource_name='address',
      completer=addresses_flags.AddressesCompleter,
      regional_collection='compute.addresses',
      global_collection='compute.globalAddresses',
      region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION,
      short_help='IP address that the forwarding rule will serve.',
      detailed_help=AddressArgHelp(
          include_l7_internal_load_balancing=include_l7_internal_load_balancing)
  )


def AddUpdateArgs(parser,
                  include_l7_internal_load_balancing=False,
                  include_target_grpc_proxy=False):
  """Adds common flags for mutating forwarding rule targets."""
  target = parser.add_mutually_exclusive_group(required=True)

  if include_target_grpc_proxy:
    TargetGrpcProxyArg().AddArgument(parser, mutex_group=target)

  TargetHttpProxyArg(
      include_l7_internal_load_balancing=include_l7_internal_load_balancing
  ).AddArgument(
      parser, mutex_group=target)
  TargetHttpsProxyArg(
      include_l7_internal_load_balancing=include_l7_internal_load_balancing
  ).AddArgument(
      parser, mutex_group=target)
  TARGET_INSTANCE_ARG.AddArgument(parser, mutex_group=target)
  TARGET_POOL_ARG.AddArgument(parser, mutex_group=target)
  TARGET_SSL_PROXY_ARG.AddArgument(parser, mutex_group=target)
  TARGET_TCP_PROXY_ARG.AddArgument(parser, mutex_group=target)
  TARGET_VPN_GATEWAY_ARG.AddArgument(parser, mutex_group=target)

  BACKEND_SERVICE_ARG.AddArgument(parser, mutex_group=target)
  NetworkArg(
      include_l7_internal_load_balancing=include_l7_internal_load_balancing
  ).AddArgument(parser)
  SUBNET_ARG.AddArgument(parser)

  AddLoadBalancingScheme(
      parser,
      include_l7_ilb=include_l7_internal_load_balancing,
      include_target_grpc_proxy=include_target_grpc_proxy)


def AddLoadBalancingScheme(parser,
                           include_l7_ilb=False,
                           include_target_grpc_proxy=False):
  """Adds the load-balancing-scheme flag."""
  td_proxies = ('--target-http-proxy, --target-https-proxy, --target-grpc-proxy'
                if include_target_grpc_proxy else
                '--target-http-proxy, --target-https-proxy')
  load_balancing_choices = {
      'EXTERNAL':
          'External load balancing or forwarding, used with one of '
          '--target-http-proxy, --target-https-proxy, --target-tcp-proxy, '
          '--target-ssl-proxy, --target-pool, --target-vpn-gateway, '
          '--target-instance.',
      'INTERNAL':
          'Internal load balancing or forwarding, used with --backend-service.',
      'INTERNAL_SELF_MANAGED':
          """Traffic director load balancing or forwarding, used with
          {0}.""".format(td_proxies)
  }

  if include_l7_ilb:
    load_balancing_choices.update({
        'INTERNAL_MANAGED': 'Internal HTTP(S) Load Balancing, used with '
                            '--target-http-proxy, --target-https-proxy.'
    })

  parser.add_argument(
      '--load-balancing-scheme',
      choices=load_balancing_choices,
      type=lambda x: x.replace('-', '_').upper(),
      default='EXTERNAL',
      help='This defines the forwarding rule\'s load balancing scheme.')


def AddAllowGlobalAccess(parser):
  """Adds allow global access flag to the argparse."""
  parser.add_argument(
      '--allow-global-access',
      action='store_true',
      default=None,
      help="""\
      If True, then clients from all regions can access this internal
      forwarding rule. This can only be specified for forwarding rules with
      the LOAD_BALANCING_SCHEME set to INTERNAL and the target must be either
      a backend service or a target instance.
      """)


def AddIPProtocols(parser):
  """Adds IP protocols flag, with values available in the given version."""

  protocols = ['AH', 'ESP', 'ICMP', 'SCTP', 'TCP', 'UDP']

  parser.add_argument(
      '--ip-protocol',
      choices=protocols,
      type=lambda x: x.upper(),
      help="""\
      IP protocol that the rule will serve. The default is `TCP`.

      Note that if the load-balancing scheme is `INTERNAL`, the protocol must
      be one of: `TCP`, `UDP`.

      For a load-balancing scheme that is `EXTERNAL`, all IP_PROTOCOL
      options are valid.
      """)


def AddIpVersionGroup(parser):
  """Adds IP versions flag in a mutually exclusive group."""
  parser.add_argument(
      '--ip-version',
      choices=['IPV4', 'IPV6'],
      type=lambda x: x.upper(),
      help="""\
      Version of the IP address to be allocated if no --address is given.
      The default is IPv4.
      """)


def AddAddressesAndIPVersions(parser, required,
                              include_l7_internal_load_balancing):
  """Adds Addresses and IP versions flag."""

  address_arg = AddressArg(
      include_l7_internal_load_balancing=include_l7_internal_load_balancing)
  group = parser.add_mutually_exclusive_group(required=required)
  AddIpVersionGroup(group)
  address_arg.AddArgument(parser, mutex_group=group)


def AddDescription(parser):
  """Adds description flag."""

  parser.add_argument(
      '--description',
      help='Optional textual description for the forwarding rule.')


def AddPortsAndPortRange(parser):
  """Adds ports and port range flags."""

  ports_scope = parser.add_mutually_exclusive_group()
  ports_metavar = 'ALL | [PORT | START_PORT-END_PORT],[...]'
  ports_help = """\
  List of comma-separated ports. The forwarding rule forwards packets with
  matching destination ports. Port specification requirements vary
  depending on the load-balancing scheme and target.
  For more information, refer to https://cloud.google.com/load-balancing/docs/forwarding-rule-concepts#port_specifications.
  """

  ports_scope.add_argument(
      '--ports',
      metavar=ports_metavar,
      type=PortRangesWithAll.CreateParser(),
      default=None,
      help=ports_help)

  ports_scope.add_argument(
      '--port-range',
      type=arg_parsers.Range.Parse,
      metavar='[PORT | START_PORT-END_PORT]',
      help="""\
      DEPRECATED, use --ports. If specified, only packets addressed to ports in
      the specified range are forwarded. For more information, refer to
      https://cloud.google.com/load-balancing/docs/forwarding-rule-concepts#port_specifications.
      """)


def AddNetworkTier(parser, supports_network_tier_flag, for_update):
  """Adds network tier flag."""

  # This arg is a string simulating enum NetworkTier because one of the
  # option SELECT is hidden since it's not advertised to all customers.
  if supports_network_tier_flag:
    if for_update:
      parser.add_argument(
          '--network-tier',
          type=lambda x: x.upper(),
          help="""\
          Update the network tier of a forwarding rule. It does not allow to
          change from `PREMIUM` to `STANDARD` and visa versa.
          """)
    else:
      parser.add_argument(
          '--network-tier',
          type=lambda x: x.upper(),
          help="""\
          Network tier to assign to the forwarding rules. ``NETWORK_TIER''
          must be one of: `PREMIUM`, `STANDARD`. The default value is `PREMIUM`.
          """)


def AddIsMirroringCollector(parser):
  parser.add_argument(
      '--is-mirroring-collector',
      action='store_true',
      default=None,
      help="""\
      If set, this forwarding rule can be used as a collector for packet
      mirroring. This can only be specified for forwarding rules with the
      LOAD_BALANCING_SCHEME set to INTERNAL.
      """)


class PortRangesWithAll(object):
  """Particular keyword 'all' or a range of integer values."""

  def __init__(self, all_specified, ranges):
    self.all_specified = all_specified
    self.ranges = ranges

  @staticmethod
  def CreateParser():
    """Creates parser to parse keyword 'all' first before parse range."""

    def _Parse(string_value):
      if string_value.lower() == 'all':
        return PortRangesWithAll(True, [])
      else:
        type_parse = arg_parsers.ArgList(
            min_length=1, element_type=arg_parsers.Range.Parse)
        return PortRangesWithAll(False, type_parse(string_value))

    return _Parse
