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

"""Flags and helpers for the compute backend-services commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.util import completers


DEFAULT_LIST_FORMAT = """\
    table(
      name,
      backends[].group.scoped_suffixes().list():label=BACKENDS,
      protocol
    )"""

DEFAULT_BETA_LIST_FORMAT = """\
    table(
      name,
      backends[].group.scoped_suffixes().list():label=BACKENDS,
      protocol,
      loadBalancingScheme,
      healthChecks.map().basename().list()
    )"""


class RegionalBackendServicesCompleter(compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(RegionalBackendServicesCompleter, self).__init__(
        collection='compute.regionBackendServices',
        list_command=('compute backend-services list '
                      '--filter=region:* --uri'),
        **kwargs)


class GlobalBackendServicesCompleter(compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(GlobalBackendServicesCompleter, self).__init__(
        collection='compute.backendServices',
        list_command=('compute backend-services list --global --uri'),
        **kwargs)


class BackendServicesCompleter(completers.MultiResourceCompleter):

  def __init__(self, **kwargs):
    super(BackendServicesCompleter, self).__init__(
        completers=[RegionalBackendServicesCompleter,
                    GlobalBackendServicesCompleter],
        **kwargs)


ZONAL_INSTANCE_GROUP_ARG = compute_flags.ResourceArgument(
    name='--instance-group',
    resource_name='instance group',
    completer=compute_completers.InstanceGroupsCompleter,
    zonal_collection='compute.instanceGroups',
    zone_explanation=compute_flags.ZONE_PROPERTY_EXPLANATION)


MULTISCOPE_INSTANCE_GROUP_ARG = compute_flags.ResourceArgument(
    name='--instance-group',
    resource_name='instance group',
    completer=compute_completers.InstanceGroupsCompleter,
    zonal_collection='compute.instanceGroups',
    regional_collection='compute.regionInstanceGroups',
    zone_explanation=compute_flags.ZONE_PROPERTY_EXPLANATION,
    region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION)


GLOBAL_BACKEND_SERVICE_ARG = compute_flags.ResourceArgument(
    name='backend_service_name',
    resource_name='backend service',
    completer=GlobalBackendServicesCompleter,
    global_collection='compute.backendServices')


GLOBAL_MULTI_BACKEND_SERVICE_ARG = compute_flags.ResourceArgument(
    name='backend_service_name',
    resource_name='backend service',
    completer=BackendServicesCompleter,
    plural=True,
    global_collection='compute.backendServices')


GLOBAL_REGIONAL_BACKEND_SERVICE_ARG = compute_flags.ResourceArgument(
    name='backend_service_name',
    resource_name='backend service',
    completer=BackendServicesCompleter,
    regional_collection='compute.regionBackendServices',
    global_collection='compute.backendServices')


GLOBAL_REGIONAL_MULTI_BACKEND_SERVICE_ARG = compute_flags.ResourceArgument(
    name='backend_service_name',
    resource_name='backend service',
    completer=BackendServicesCompleter,
    plural=True,
    regional_collection='compute.regionBackendServices',
    global_collection='compute.backendServices')


NETWORK_ARG = compute_flags.ResourceArgument(
    name='--network',
    required=False,
    resource_name='network',
    global_collection='compute.networks',
    short_help='Network that this backend service applies to.',
    detailed_help="""\
        Network that this backend service applies to. It can only be set if
        the load-balancing-scheme is INTERNAL.
        """)


def GetNetworkEndpointGroupArg(support_global_neg=False,
                               support_region_neg=False):
  return compute_flags.ResourceArgument(
      name='--network-endpoint-group',
      resource_name='network endpoint group',
      zonal_collection='compute.networkEndpointGroups',
      global_collection='compute.globalNetworkEndpointGroups'
      if support_global_neg else None,
      regional_collection='compute.regionNetworkEndpointGroups'
      if support_region_neg else None,
      zone_explanation=compute_flags.ZONE_PROPERTY_EXPLANATION,
      region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION
      if support_region_neg else None)


def BackendServiceArgumentForUrlMap(required=True,
                                    include_l7_internal_load_balancing=False):
  return compute_flags.ResourceArgument(
      resource_name='backend service',
      name='--default-service',
      required=required,
      completer=BackendServicesCompleter,
      global_collection='compute.backendServices',
      regional_collection='compute.regionBackendServices'
      if include_l7_internal_load_balancing else None,
      short_help=(
          'A backend service that will be used for requests for which this '
          'URL map has no mappings.'),
      region_explanation=('If not specified it will be set to the '
                          'region of the URL map.'))


def BackendServiceArgumentForUrlMapPathMatcher(required=True):
  return compute_flags.ResourceArgument(
      resource_name='backend service',
      name='--default-service',
      required=required,
      completer=BackendServicesCompleter,
      global_collection='compute.backendServices',
      short_help=(
          'A backend service that will be used for requests that the path '
          'matcher cannot match.'))


def BackendServiceArgumentForTargetSslProxy(required=True):
  return compute_flags.ResourceArgument(
      resource_name='backend service',
      name='--backend-service',
      required=required,
      completer=BackendServicesCompleter,
      global_collection='compute.backendServices',
      short_help=('.'),
      detailed_help="""\
        A backend service that will be used for connections to the target SSL
        proxy.
        """)


def BackendServiceArgumentForTargetTcpProxy(required=True):
  return compute_flags.ResourceArgument(
      resource_name='backend service',
      name='--backend-service',
      required=required,
      completer=BackendServicesCompleter,
      global_collection='compute.backendServices',
      short_help=('.'),
      detailed_help="""\
        A backend service that will be used for connections to the target TCP
        proxy.
        """)


def AddLoadBalancingScheme(parser, include_l7_ilb=False):
  parser.add_argument(
      '--load-balancing-scheme',
      choices=['INTERNAL', 'EXTERNAL', 'INTERNAL_SELF_MANAGED'] +
      (['INTERNAL_MANAGED'] if include_l7_ilb else []),
      type=lambda x: x.replace('-', '_').upper(),
      default='EXTERNAL',
      help="""\
      Specifies the load balancer type. Choose EXTERNAL for load balancers
      that receive traffic from external clients. Choose INTERNAL for
      Internal TCP/UDP Load Balancing. Choose INTERNAL_MANAGED for
      Internal HTTP(S) Load Balancing. Choose INTERNAL_SELF_MANAGED for
      Traffic Director. For more information, refer to this guide:
      https://cloud.google.com/load-balancing/docs/choosing-load-balancer
      """)


def AddConnectionDrainingTimeout(parser):
  parser.add_argument(
      '--connection-draining-timeout',
      type=arg_parsers.Duration(upper_bound='1h'),
      help="""\
      Connection draining timeout to be used during removal of VMs from
      instance groups. This guarantees that for the specified time all existing
      connections to a VM will remain untouched, but no new connections will be
      accepted. Set timeout to zero to disable connection draining. Enable
      feature by specifying a timeout of up to one hour.
      If the flag is omitted API default value (0s) will be used.
      See $ gcloud topic datetimes for information on duration formats.
      """)


def AddCustomRequestHeaders(parser, remove_all_flag=False, default=None):
  """Adds custom request header flag to the argparse."""
  group = parser.add_mutually_exclusive_group()
  group.add_argument(
      '--custom-request-header',
      action='append',
      help="""\
      Specifies a HTTP Header to be added by your load balancer.
      This flag can be repeated to specify multiple headers.
      For example:

        $ {command} NAME \
            --custom-request-header "header-name: value" \
            --custom-request-header "another-header:"
      """)
  if remove_all_flag:
    group.add_argument(
        '--no-custom-request-headers',
        action='store_true',
        default=default,
        help="""\
        Remove all custom request headers for the backend service.
        """)


def AddEnableCdn(parser):
  parser.add_argument(
      '--enable-cdn',
      action=arg_parsers.StoreTrueFalseAction,
      help="""\
      Enable or disable Cloud CDN for the backend service. Only available for
      backend services with --load-balancing-scheme=EXTERNAL that use a
      --protocol of HTTP, HTTPS, or HTTP2. Cloud CDN caches HTTP responses at
      the edge of Google's network. Cloud CDN is disabled by default.
      """)


def AddCacheKeyIncludeProtocol(parser, default):
  """Adds cache key include/exclude protocol flag to the argparse."""
  parser.add_argument(
      '--cache-key-include-protocol',
      action='store_true',
      default=default,
      help="""\
      Enable including protocol in cache key. If enabled, http and https
      requests will be cached separately. Can only be applied for global
      resources.""")


def AddCacheKeyIncludeHost(parser, default):
  """Adds cache key include/exclude host flag to the argparse."""
  parser.add_argument(
      '--cache-key-include-host',
      action='store_true',
      default=default,
      help="""\
      Enable including host in cache key. If enabled, requests to different
      hosts will be cached separately. Can only be applied for global resources.
      """)


def AddCacheKeyIncludeQueryString(parser, default):
  """Adds cache key include/exclude query string flag to the argparse."""
  update_command = default is None
  if update_command:
    update_command_help = """\
        Enable including query string in cache key. If enabled, the query string
        parameters will be included according to
        --cache-key-query-string-whitelist and
        --cache-key-query-string-blacklist. If disabled, the entire query string
        will be excluded. Use "--cache-key-query-string-blacklist=" (sets the
        blacklist to the empty list) to include the entire query string. Can
        only be applied for global resources.
        """
  else:  # create command
    update_command_help = """\
        Enable including query string in cache key. If enabled, the query string
        parameters will be included according to
        --cache-key-query-string-whitelist and
        --cache-key-query-string-blacklist. If neither is set, the entire query
        string will be included. If disabled, then the entire query string will
        be excluded. Can only be applied for global resources.
        """
  parser.add_argument(
      '--cache-key-include-query-string',
      action='store_true',
      default=default,
      help=update_command_help)


def AddCacheKeyQueryStringList(parser):
  """Adds cache key include/exclude query string flags to the argparse."""
  cache_key_query_string_list = parser.add_mutually_exclusive_group()
  cache_key_query_string_list.add_argument(
      '--cache-key-query-string-whitelist',
      type=arg_parsers.ArgList(min_length=1),
      metavar='QUERY_STRING',
      default=None,
      help="""\
      Specifies a comma separated list of query string parameters to include
      in cache keys. All other parameters will be excluded. Either specify
      --cache-key-query-string-whitelist or --cache-key-query-string-blacklist,
      not both. '&' and '=' will be percent encoded and not treated as
      delimiters. Can only be applied for global resources.
      """)
  cache_key_query_string_list.add_argument(
      '--cache-key-query-string-blacklist',
      type=arg_parsers.ArgList(),
      metavar='QUERY_STRING',
      default=None,
      help="""\
      Specifies a comma separated list of query string parameters to exclude
      in cache keys. All other parameters will be included. Either specify
      --cache-key-query-string-whitelist or --cache-key-query-string-blacklist,
      not both. '&' and '=' will be percent encoded and not treated as
      delimiters. Can only be applied for global resources.
      """)


def HealthCheckArgument(required=False, support_regional_health_check=False):
  return compute_flags.ResourceArgument(
      resource_name='health check',
      name='--health-checks',
      completer=compute_completers.HealthChecksCompleter,
      plural=True,
      required=required,
      global_collection='compute.healthChecks',
      regional_collection='compute.regionHealthChecks'
      if support_regional_health_check else None,
      short_help="""\
      Specifies a list of health check objects for checking the health of
      the backend service. Currently at most one health check can be specified.
      Health checks need not be for the same protocol as that of the backend
      service.
      """,
      region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION
      if support_regional_health_check else None)


def HttpHealthCheckArgument(required=False):
  return compute_flags.ResourceArgument(
      resource_name='http health check',
      name='--http-health-checks',
      completer=compute_completers.HttpHealthChecksCompleter,
      plural=True,
      required=required,
      global_collection='compute.httpHealthChecks',
      short_help="""\
      Specifies a list of legacy HTTP health check objects for checking the
      health of the backend service.

      Legacy health checks are not recommended for backend services. It is
      possible to use a legacy health check on a backend service for a HTTP(S)
      load balancer if that backend service uses instance groups. For more
      information, refer to this guide:
      https://cloud.google.com/load-balancing/docs/health-check-concepts#lb_guide.
      """)


def HttpsHealthCheckArgument(required=False):
  return compute_flags.ResourceArgument(
      resource_name='https health check',
      name='--https-health-checks',
      completer=compute_completers.HttpsHealthChecksCompleter,
      plural=True,
      required=required,
      global_collection='compute.httpsHealthChecks',
      short_help="""\
      Specifies a list of legacy HTTPS health check objects for checking the
      health of the backend service.

      Legacy health checks are not recommended for backend services. It is
      possible to use a legacy health check on a backend service for a HTTP(S)
      load balancer if that backend service uses instance groups. For more
      information, refer to this guide:
      https://cloud.google.com/load-balancing/docs/health-check-concepts#lb_guide.
      """)


def AddNoHealthChecks(parser, default=None):
  """Adds the no health checks argument to the argparse."""
  parser.add_argument(
      '--no-health-checks',
      action='store_true',
      default=default,
      help='Removes all health checks for the backend service.')


def GetHealthCheckUris(args, resource_resolver, resource_parser):
  """Returns health check URIs from arguments."""
  health_check_refs = []

  if args.http_health_checks:
    health_check_refs.extend(
        resource_resolver.HTTP_HEALTH_CHECK_ARG.ResolveAsResource(
            args, resource_parser))

  if getattr(args, 'https_health_checks', None):
    health_check_refs.extend(
        resource_resolver.HTTPS_HEALTH_CHECK_ARG.ResolveAsResource(
            args, resource_parser))

  if getattr(args, 'health_checks', None):
    if health_check_refs:
      raise exceptions.ToolException(
          'Mixing --health-checks with --http-health-checks or with '
          '--https-health-checks is not supported.')
    else:
      health_check_refs.extend(
          resource_resolver.HEALTH_CHECK_ARG.ResolveAsResource(
              args,
              resource_parser,
              default_scope=compute_scope.ScopeEnum.GLOBAL))

  if health_check_refs and getattr(args, 'no_health_checks', None):
    raise exceptions.ToolException(
        'Combining --health-checks, --http-health-checks, or '
        '--https-health-checks with --no-health-checks is not supported.'
    )

  return [health_check_ref.SelfLink() for health_check_ref in health_check_refs]


def AddIap(parser, help=None):  # pylint: disable=redefined-builtin
  """Add support for --iap flag."""
  # We set this to str, but it's really an ArgDict.  See
  # backend_services_utils.GetIAP for the re-parse and rationale.
  return parser.add_argument(
      '--iap',
      metavar=('disabled|enabled,['
               'oauth2-client-id=OAUTH2-CLIENT-ID,'
               'oauth2-client-secret=OAUTH2-CLIENT-SECRET]'),
      help=help or 'Specifies a list of settings for IAP service.')


def AddSessionAffinity(parser,
                       target_pools=False,
                       hidden=False,
                       support_client_only=False):
  """Adds session affinity flag to the argparse.

  Args:
    parser: An argparse.ArgumentParser instance.
    target_pools: Indicates if the backend pool is target pool.
    hidden: if hidden=True, retains help but does not display it.
    support_client_only: Indicates if CLIENT_IP_NO_DESTINATION is valid choice.
  """
  choices = {
      'CLIENT_IP': (
          "Route requests to instances based on the hash of the client's IP "
          'address.'),
      'NONE': 'Session affinity is disabled.',
      'CLIENT_IP_PROTO': (
          'Connections from the same client IP with the same IP '
          'protocol will go to the same VM in the pool while that VM remains'
          ' healthy.'),
  }

  if not target_pools:
    choices.update({
        'GENERATED_COOKIE': (
            '(Applicable if `--load-balancing-scheme` is '
            '`INTERNAL_MANAGED`, `INTERNAL_SELF_MANAGED`, or `EXTERNAL`) '
            ' If the `--load-balancing-scheme` is `EXTERNAL`, routes '
            ' requests to backend VMs or endpoints in a NEG, based on the '
            ' contents of the `GCLB` cookie set by the load balancer. Only '
            ' applicable when `--protocol` is HTTP, HTTPS, or HTTP2. If the '
            ' `--load-balancing-scheme` is `INTERNAL_MANAGED` or '
            ' `INTERNAL_SELF_MANAGED`, routes requests to backend VMs or '
            ' endpoints in a NEG, based on the contents of the `GCILB` cookie '
            ' set by the proxy. (If no cookie is present, the proxy '
            ' chooses a backend VM or endpoint and sends a `Set-Cookie` '
            ' response for future requests.) If the `--load-balancing-scheme` '
            ' is `INTERNAL_SELF_MANAGED`, routes requests to backend VMs or '
            ' endpoints in a NEG, based on the contents of a cookie set by '
            ' Traffic Director.'),
        'CLIENT_IP_PROTO': (
            '(Applicable if `--load-balancing-scheme` is `INTERNAL`) '
            'Connections from the same client IP with the same IP '
            'protocol will go to the same backend VM while that VM remains'
            ' healthy.'),
        'CLIENT_IP_PORT_PROTO': (
            '(Applicable if `--load-balancing-scheme` is `INTERNAL`) '
            'Connections from the same client IP with the same IP protocol and '
            'port will go to the same backend VM while that VM remains '
            'healthy.'),
        'HTTP_COOKIE': (
            '(Applicable if `--load-balancing-scheme` is `INTERNAL_MANAGED`'
            ' or `INTERNAL_SELF_MANAGED`) Route requests to backend VMs or '
            ' endpoints in a NEG, based on an HTTP cookie named in the '
            ' `HTTP_COOKIE` flag (with the optional `--affinity-cookie-ttl` '
            ' flag). If the client has not provided the cookie, '
            ' the proxy generates the cookie and returns it to the client in a '
            ' `Set-Cookie` header. This session affinity is only valid if the '
            ' load balancing locality policy is either `RING_HASH` or `MAGLEV` '
            ' and the backend service\'s consistent hash specifies the HTTP '
            ' cookie.'),
        'HEADER_FIELD': (
            '(Applicable if `--load-balancing-scheme` is `INTERNAL_MANAGED`'
            ' or `INTERNAL_SELF_MANAGED`) Route requests to backend VMs or '
            ' endpoints in a NEG based on the value of the HTTP header named '
            ' in the `--custom-request-header` flag. This session '
            ' affinity is only valid if the load balancing locality policy '
            ' is either RING_HASH or MAGLEV and the backend service\'s '
            ' consistent hash specifies the name of the HTTP header.'),
    })
    if support_client_only:
      choices.update({
          'CLIENT_IP_NO_DESTINATION': (
              'Directs a particular client\'s request to the same backend VM '
              'based on a hash created on the client\'s IP address only. This '
              'is used in L4 ILB as Next-Hop scenarios. It differs from the '
              'Client-IP option in that Client-IP uses a hash based on both '
              'client-IP\'s address and destination address.'
              )
      })
  help_str = 'The type of TCP session affinity to use. Not supported for UDP.'
  parser.add_argument(
      '--session-affinity',
      choices=choices,
      # Tri-valued, None => don't include property.
      default='NONE' if target_pools else None,
      type=lambda x: x.upper(),
      hidden=hidden,
      help=help_str)


def AddAffinityCookieTtl(parser, hidden=False):
  """Adds affinity cookie Ttl flag to the argparse."""
  affinity_cookie_ttl_help = """\
      If session-affinity is set to "generated_cookie", this flag sets
      the TTL, in seconds, of the resulting cookie.  A setting of 0
      indicates that the cookie should be transient.
      See $ gcloud topic datetimes for information on duration formats.
      """
  parser.add_argument(
      '--affinity-cookie-ttl',
      type=arg_parsers.Duration(),
      default=None,  # Tri-valued, None => don't include property.
      help=affinity_cookie_ttl_help,
      hidden=hidden,
  )


def AddDescription(parser):
  parser.add_argument(
      '--description',
      help='An optional, textual description for the backend service.')


def AddTimeout(parser, default='30s'):
  parser.add_argument(
      '--timeout',
      default=default,
      type=arg_parsers.Duration(),
      help="""\
      Applicable to all load balancers except internal TCP/UDP load
      balancers. For internal TCP/UDP load balancers
      (``load-balancing-scheme'' INTERNAL), ``timeout'' is ignored.

      If the ``protocol'' is HTTP, HTTPS, or HTTP2, ``timeout'' is a
      request/response timeout for HTTP(S) traffic, meaning the amount
      of time that the load balancer waits for a backend to return a
      full response to a request. If WebSockets traffic is supported, the
      ``timeout'' parameter sets the maximum amount of time that a
      WebSocket can be open (idle or not).

      For example, for HTTP, HTTPS, or HTTP2 traffic, specifying a ``timeout''
      of 10s means that backends have 10 seconds to respond to the load
      balancer's requests. The load balancer retries the HTTP GET request one
      time if the backend closes the connection or times out before sending
      response headers to the load balancer. If the backend sends response
      headers or if the request sent to the backend is not an HTTP GET request,
      the load balancer does not retry. If the backend does not reply at all,
      the load balancer returns a 502 Bad Gateway error to the client.

      If the ``protocol'' is SSL or TCP, ``timeout'' is an idle timeout.
      """)


def AddPortName(parser):
  """Add port-name flag."""
  parser.add_argument(
      '--port-name',
      help="""\
      The name of a service that has been added to an instance group
      in this backend. Instance group services map a name to a port
      number which is used by the load balancing service.
      Only one ``port-name'' may be added to a backend service, and that
      name must exist as a service on all instance groups that are a
      part of this backend service. The port number associated with the
      name may differ between instances. If you do not specify
      this flag, your instance groups must have a service named ``http''
      configured. See also
      `gcloud compute instance-groups set-named-ports --help`.
      The ``port-name'' parameter cannot be set if the
      load-balancing-scheme is INTERNAL.
      """)


def AddProtocol(parser, default='HTTP', support_grpc_protocol=False):
  """Adds --protocol flag to the argparse.

  Args:
    parser: An argparse.ArgumentParser instance.
    default: The default protocol if this flag is unspecified.
    support_grpc_protocol: Indicates if GRPC is a valid protocol.
  """
  td_protocols = ('HTTP, HTTPS, HTTP2, GRPC'
                  if support_grpc_protocol else 'HTTP, HTTPS, HTTP2')
  parser.add_argument(
      '--protocol',
      default=default,
      type=lambda x: x.upper(),
      help="""\
      Protocol for incoming requests.

      If the `load-balancing-scheme` is `INTERNAL` (internal TCP/UDP load
      balancers), the protocol must be one of: TCP, UDP.

      If the `load-balancing-scheme` is `INTERNAL_SELF_MANAGED` (Traffic
      Director), the protocol must be one of: {0}.

      If the `load-balancing-scheme` is `INTERNAL_MANAGED` (internal HTTP(S)
      load balancers), the protocol must be one of: HTTP, HTTPS, HTTP2.

      If the `load-balancing-scheme` is `EXTERNAL` (HTTP(S), SSL proxy, or TCP
      proxy load balancers), the protocol must be one of: HTTP, HTTPS, HTTP2,
      SSL, TCP.
      """.format(td_protocols))


def AddConnectionDrainOnFailover(parser, default):
  """Adds the connection drain on failover argument to the argparse."""
  parser.add_argument(
      '--connection-drain-on-failover',
      action='store_true',
      default=default,
      help="""\
      Connection drain is enabled by default and on failover or failback
      connections will be drained. If connection drain is disabled, the existing
      connection state will be cleared immediately on a best effort basis on
      failover or failback, all connections will then be served by the active
      pool of instances. Not compatible with the --global flag, load balancing
      scheme must be INTERNAL, and the protocol must be TCP.
      """)


def AddDropTrafficIfUnhealthy(parser, default):
  """Adds the drop traffic if unhealthy argument to the argparse."""
  parser.add_argument(
      '--drop-traffic-if-unhealthy',
      action='store_true',
      default=default,
      help="""\
      Enable dropping of traffic if there are no healthy VMs detected in both
      the primary and backup instance groups. Not compatible with the --global
      flag and load balancing scheme must be INTERNAL.
      """)


def AddFailoverRatio(parser):
  """Adds the failover ratio argument to the argparse."""
  parser.add_argument(
      '--failover-ratio',
      type=arg_parsers.BoundedFloat(lower_bound=0.0, upper_bound=1.0),
      help="""\
      If the ratio of the healthy VMs in the primary backend is at or below this
      number, traffic arriving at the load-balanced IP will be directed to the
      failover backend(s). Not compatible with the --global flag.
      """)


def AddEnableLogging(parser, default):
  """Adds the enable logging argument to the argparse."""
  parser.add_argument(
      '--enable-logging',
      action='store_true',
      default=default,
      help="""\
      The logging options for the load balancer traffic served by this backend
      service. If logging is enabled, logs will be exported to Stackdriver.
      Enabled by default.
      """)


def AddLoggingSampleRate(parser):
  """Adds the logging sample rate argument to the argparse."""
  parser.add_argument(
      '--logging-sample-rate',
      type=arg_parsers.BoundedFloat(lower_bound=0.0, upper_bound=1.0),
      help="""\
      This field can only be specified if logging is enabled for the backend
      service. The value of the field must be a float in the range [0, 1]. This
      configures the sampling rate of requests to the load balancer where 1.0
      means all logged requests are reported and 0.0 means no logged requests
      are reported. The default value is 1.0.
      """)


def AddInstanceGroupAndNetworkEndpointGroupArgs(parser,
                                                verb,
                                                support_global_neg=False,
                                                support_region_neg=False):
  """Adds instance group and network endpoint group args to the argparse."""
  backend_group = parser.add_group(required=True, mutex=True)
  instance_group = backend_group.add_group('Instance Group')
  neg_group = backend_group.add_group('Network Endpoint Group')
  MULTISCOPE_INSTANCE_GROUP_ARG.AddArgument(
      instance_group, operation_type='{} the backend service'.format(verb))
  neg_group_arg = GetNetworkEndpointGroupArg(
      support_global_neg=support_global_neg,
      support_region_neg=support_region_neg)
  neg_group_arg.AddArgument(
      neg_group, operation_type='{} the backend service'.format(verb))


def AddNetwork(parser):
  NETWORK_ARG.AddArgument(parser)
