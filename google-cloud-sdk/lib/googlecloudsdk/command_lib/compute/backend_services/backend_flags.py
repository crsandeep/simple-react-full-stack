# pylint: disable=E1305
# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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

"""Flags and helpers for the compute backend-services backend commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.core import log


def AddDescription(parser):
  parser.add_argument(
      '--description',
      help='An optional, textual description for the backend.')


def AddInstanceGroup(parser, operation_type, with_deprecated_zone=False):
  """Adds arguments to define instance group."""
  parser.add_argument(
      '--instance-group',
      required=True,
      help='The name or URI of a Google Cloud Instance Group.')

  scope_parser = parser.add_mutually_exclusive_group()
  flags.AddRegionFlag(
      scope_parser,
      resource_type='instance group',
      operation_type='{0} the backend service'.format(operation_type),
      flag_prefix='instance-group',
      explanation=flags.REGION_PROPERTY_EXPLANATION_NO_DEFAULT)
  if with_deprecated_zone:
    flags.AddZoneFlag(
        scope_parser,
        resource_type='instance group',
        operation_type='{0} the backend service'.format(operation_type),
        explanation='DEPRECATED, use --instance-group-zone flag instead.')
  flags.AddZoneFlag(
      scope_parser,
      resource_type='instance group',
      operation_type='{0} the backend service'.format(operation_type),
      flag_prefix='instance-group',
      explanation=flags.ZONE_PROPERTY_EXPLANATION_NO_DEFAULT)


def WarnOnDeprecatedFlags(args):
  if getattr(args, 'zone', None):  # TODO(b/28518663).
    log.warning(
        'The --zone flag is deprecated, please use --instance-group-zone'
        ' instead. It will be removed in a future release.')


def _GetBalancingModes():
  """Returns the --balancing-modes flag value choices name:description dict."""
  per_rate_flags = '*--max-rate-per-instance*'
  per_connection_flags = '*--max-connections-per-instance*'
  per_rate_flags += '/*--max-rate-per-endpoint*'
  per_connection_flags += '*--max-max-per-endpoint*'
  utilization_extra_help = (
      'This is incompatible with --network-endpoint-group.')
  balancing_modes = {
      'CONNECTION': """\
          Available if the backend service's load balancing scheme is either
          `INTERNAL` or `EXTERNAL`.
          Available if the backend service's protocol is one of `SSL`, `TCP`,
          or `UDP`.

          Spreads load based on how many concurrent connections the backend
          can handle.

          For backend services with --load-balancing-scheme `EXTERNAL`, you
          must specify exactly one of these additional parameters:
          `--max-connections`, `--max-connections-per-instance`, or
          `--max-connections-per-endpoint`.

          For backend services where `--load-balancing-scheme` is `INTERNAL`,
          you must omit all of these parameters.
          """.format(per_rate_flags),
      'RATE': """\
          Available if the backend service's load balancing scheme is
          `INTERNAL_MANAGED`, `INTERNAL_SELF_MANAGED`, or `EXTERNAL`. Available
          if the backend service's protocol is one of HTTP, HTTPS, or HTTP/2.

          Spreads load based on how many HTTP requests per second (RPS) the
          backend can handle.

          You must specify exactly one of these additional parameters:
          `--max-rate`, `--max-rate-per-instance`, or `--max-rate-per-endpoint`.
          """.format(utilization_extra_help),
      'UTILIZATION': """\
          Available if the backend service's load balancing scheme is
          `INTERNAL_MANAGED`, `INTERNAL_SELF_MANAGED`, or `EXTERNAL`. Available only
          for managed or unmanaged instance group backends.

          Spreads load based on the CPU utilization of instances in a backend
          instance group.

          The following additional parameters may be specified:
          `--max-utilization`, `--max-rate`, `--max-rate-per-instance`,
          `--max-connections`, `--max-connections-per-instance`.
          For valid combinations, see `--max-utilization`.
          """.format(per_connection_flags),
  }
  return balancing_modes


def AddBalancingMode(parser,
                     support_global_neg=False,
                     support_region_neg=False):
  """Adds balancing mode argument to the argparse."""
  help_text = """\
  Defines the strategy for balancing load.
  """
  incompatible_types = []
  if support_global_neg:
    incompatible_types.extend(['INTERNET_IP_PORT', 'INTERNET_FQDN_PORT'])
  if support_region_neg:
    incompatible_types.append('SERVERLESS')
  if incompatible_types:
    help_text += """\

  This cannot be used when the endpoint type of an attached network endpoint
  group is {0}.
    """.format(' or '.join(incompatible_types))
  parser.add_argument(
      '--balancing-mode',
      choices=_GetBalancingModes(),
      type=lambda x: x.upper(),
      help=help_text)


def AddCapacityLimits(parser,
                      support_global_neg=False,
                      support_region_neg=False):
  """Adds capacity thresholds arguments to the argparse."""
  AddMaxUtilization(parser)
  capacity_group = parser.add_group(mutex=True)
  capacity_incompatible_types = []
  if support_global_neg:
    capacity_incompatible_types.extend(
        ['INTERNET_IP_PORT', 'INTERNET_FQDN_PORT'])
  if support_region_neg:
    capacity_incompatible_types.append('SERVERLESS')
  append_help_text = """\

  This cannot be used when the endpoint type of an attached network endpoint
  group is {0}.
  """.format(' or '.join(
      capacity_incompatible_types)) if capacity_incompatible_types else ''
  capacity_group.add_argument(
      '--max-rate-per-endpoint',
      type=float,
      help="""\
      Only valid for network endpoint group backends. Defines a maximum
      number of HTTP requests per second (RPS) per endpoint if all endpoints
      are healthy. When one or more endpoints are unhealthy, an effective
      maximum rate per healthy endpoint is calculated by multiplying
      `MAX_RATE_PER_ENDPOINT` by the number of endpoints in the network
      endpoint group, then dividing by the number of healthy endpoints.
      """ + append_help_text)
  capacity_group.add_argument(
      '--max-connections-per-endpoint',
      type=int,
      help="""\
      Only valid for network endpoint group backends. Defines a maximum
      number of connections per endpoint if all endpoints are healthy. When
      one or more endpoints are unhealthy, an effective maximum number of
      connections per healthy endpoint is calculated by multiplying
      `MAX_CONNECTIONS_PER_ENDPOINT` by the number of endpoints in the network
      endpoint group, then dividing by the number of healthy endpoints.
      """ + append_help_text)

  capacity_group.add_argument(
      '--max-rate',
      type=int,
      help="""\
      Maximum number of HTTP requests per second (RPS) that the backend can
      handle. Valid for network endpoint group and instance group backends
      (except for regional managed instance groups). Must not be defined if the
      backend is a managed instance group using load balancing-based autoscaling.
      """ + append_help_text)
  capacity_group.add_argument(
      '--max-rate-per-instance',
      type=float,
      help="""\
      Only valid for instance group backends. Defines a maximum number of
      HTTP requests per second (RPS) per instance if all instances in the
      instance group are healthy. When one or more instances are unhealthy,
      an effective maximum RPS per healthy instance is calculated by
      multiplying `MAX_RATE_PER_INSTANCE` by the number of instances in the
      instance group, then dividing by the number of healthy instances. This
      parameter is compatible with managed instance group backends that use
      autoscaling based on load balancing.
      """)
  capacity_group.add_argument(
      '--max-connections',
      type=int,
      help="""\
      Maximum concurrent connections that the backend can handle. Valid for
      network endpoint group and instance group backends (except for regional
      managed instance groups).
      """ + append_help_text)
  capacity_group.add_argument(
      '--max-connections-per-instance',
      type=int,
      help="""\
      Only valid for instance group backends. Defines a maximum number
      of concurrent connections per instance if all instances in the
      instance group are healthy. When one or more instances are
      unhealthy, an effective maximum number of connections per healthy
      instance is calculated by multiplying `MAX_CONNECTIONS_PER_INSTANCE`
      by the number of instances in the instance group, then dividing by
      the number of healthy instances.
      """)


def AddMaxUtilization(parser):
  """Adds max utilization argument to the argparse."""
  parser.add_argument(
      '--max-utilization',
      type=arg_parsers.BoundedFloat(lower_bound=0.0, upper_bound=1.0),
      help="""\
      Defines the maximum target for average utilization of the backend instance
      in the backend instance group. Acceptable values are `0.0` (0%) through
      `1.0`(100%). Available for all backend service protocols, with
      `--balancing-mode=UTILIZATION`.

      For backend services that use SSL, TCP, or UDP protocols, the following
      configuration options are supported:

      * no additional parameter
      * only `--max-utilization`
      * only `--max-connections` (except for regional managed instance groups)
      * only `--max-connections-per-instance`
      * both `--max-utilization` and `--max-connections` (except for regional
        managed instance groups)
      * both `--max-utilization` and `--max-connections-per-instance`

      The meanings for `-max-connections` and `--max-connections-per-instance`
      are the same as for --balancing-mode=CONNECTION. If one is used  with
      `--max-utilization`, instances are considered at capacity
      when either maximum utilization or maximum connections is reached.

      For backend services that use HTTP, HTTPS, or HTTP/2 protocols, the
      following configuration options are supported:

      * no additional parameter
      * only `--max-utilization`
      * only `--max-rate` (except for regional managed instance groups)
      * only `--max-rate-per-instance`
      * both `--max-utilization` and `--max-rate` (except for regional managed
        instance groups)
      * both `--max-utilization` and `--max-rate-per-instance`

      The meanings for `--max-rate` and `--max-rate-per-instance` are the same
      as for --balancing-mode=RATE. If one is used in conjunction with
      `--max-utilization`, instances are considered at capacity when *either*
      maximum utilization or the maximum rate is reached.""")


def AddCapacityScalar(parser,
                      support_global_neg=False,
                      support_region_neg=False):
  """Adds capacity thresholds argument to the argparse."""
  help_text = """\
      A setting that applies to all balancing modes. This value is multiplied
      by the balancing mode value to set the current max usage of the instance
      group. Acceptable values are `0.0` (0%) through `1.0` (100%). Setting this
      value to `0.0` (0%) drains the backend service. Note that draining a
      backend service only prevents new connections to instances in the group.
      All existing connections are allowed to continue until they close by
      normal means. This cannot be used for internal load balancing.
      """
  incompatible_types = []
  if support_global_neg:
    incompatible_types.extend(['INTERNET_IP_PORT', 'INTERNET_FQDN_PORT'])
  if support_region_neg:
    incompatible_types.append('SERVERLESS')
  if incompatible_types:
    help_text += """\

    This cannot be used when the endpoint type of an attached network endpoint
    group is {0}.
    """.format(' or '.join(incompatible_types))
  parser.add_argument(
      '--capacity-scaler',
      type=arg_parsers.BoundedFloat(lower_bound=0.0, upper_bound=1.0),
      help=help_text)


def AddFailover(parser, default):
  """Adds the failover argument to the argparse."""
  parser.add_argument(
      '--failover',
      action='store_true',
      default=default,
      help="""\
      Designates whether this is a failover backend. More than one
      failover backend can be configured for a given BackendService.
      Not compatible with the --global flag""")
