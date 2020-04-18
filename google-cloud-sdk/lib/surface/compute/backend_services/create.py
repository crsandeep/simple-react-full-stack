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
"""Command for creating backend services.

   There are separate alpha, beta, and GA command classes in this file.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import signed_url_flags
from googlecloudsdk.command_lib.compute.backend_services import backend_services_utils
from googlecloudsdk.command_lib.compute.backend_services import flags
from googlecloudsdk.core import log


# TODO(b/73642225): Determine whether 'https' should be default
def _ResolvePortName(args):
  """Determine port name if one was not specified."""
  if args.port_name:
    return args.port_name

  if args.protocol == 'HTTPS':
    return 'https'
  if args.protocol == 'HTTP2':
    return 'http2'
  if args.protocol == 'SSL':
    return 'ssl'
  if args.protocol == 'TCP':
    return 'tcp'

  return 'http'


# TODO(b/73642225): Determine whether 'HTTPS' should be default
def _ResolveProtocol(messages, args, default='HTTP'):
  valid_options = messages.BackendService.ProtocolValueValuesEnum.names()
  if args.protocol and args.protocol not in valid_options:
    raise ValueError('{} is not a supported option. See the help text of '
                     '--protocol for supported options.'.format(args.protocol))
  return messages.BackendService.ProtocolValueValuesEnum(
      args.protocol or default)


def AddIapFlag(parser):
  # TODO(b/34479878): It would be nice if the auto-generated help text were
  # a bit better so we didn't need to be quite so verbose here.
  flags.AddIap(
      parser,
      help="""\
      Configure Identity Aware Proxy (IAP) service. You can configure IAP to be
      'enabled' or 'disabled' (default). If it is enabled you can provide values
      for 'oauth2-client-id' and 'oauth2-client-secret'. For example,
      '--iap=enabled,oauth2-client-id=foo,oauth2-client-secret=bar' will
      turn IAP on, and '--iap=disabled' will turn it off. See
      https://cloud.google.com/iap/ for more information about this feature.
      """)


class CreateHelper(object):
  """Helper class to create a backend service."""

  HEALTH_CHECK_ARG = None
  HTTP_HEALTH_CHECK_ARG = None
  HTTPS_HEALTH_CHECK_ARG = None

  @classmethod
  def Args(cls, parser, support_l7_internal_load_balancer, support_failover,
           support_logging, support_multinic, support_client_only,
           support_grpc_protocol):
    """Add flags to create a backend service to the parser."""

    parser.display_info.AddFormat(flags.DEFAULT_LIST_FORMAT)
    flags.GLOBAL_REGIONAL_BACKEND_SERVICE_ARG.AddArgument(
        parser, operation_type='create')
    flags.AddDescription(parser)
    cls.HEALTH_CHECK_ARG = flags.HealthCheckArgument(
        support_regional_health_check=support_l7_internal_load_balancer)
    cls.HEALTH_CHECK_ARG.AddArgument(parser, cust_metavar='HEALTH_CHECK')
    cls.HTTP_HEALTH_CHECK_ARG = flags.HttpHealthCheckArgument()
    cls.HTTP_HEALTH_CHECK_ARG.AddArgument(
        parser, cust_metavar='HTTP_HEALTH_CHECK')
    cls.HTTPS_HEALTH_CHECK_ARG = flags.HttpsHealthCheckArgument()
    cls.HTTPS_HEALTH_CHECK_ARG.AddArgument(
        parser, cust_metavar='HTTPS_HEALTH_CHECK')
    flags.AddTimeout(parser)
    flags.AddPortName(parser)
    flags.AddProtocol(
        parser, default=None, support_grpc_protocol=support_grpc_protocol)
    flags.AddEnableCdn(parser)
    flags.AddSessionAffinity(parser, support_client_only=support_client_only)
    flags.AddAffinityCookieTtl(parser)
    flags.AddConnectionDrainingTimeout(parser)
    flags.AddLoadBalancingScheme(
        parser, include_l7_ilb=support_l7_internal_load_balancer)
    flags.AddCustomRequestHeaders(parser, remove_all_flag=False)
    flags.AddCacheKeyIncludeProtocol(parser, default=True)
    flags.AddCacheKeyIncludeHost(parser, default=True)
    flags.AddCacheKeyIncludeQueryString(parser, default=True)
    flags.AddCacheKeyQueryStringList(parser)
    AddIapFlag(parser)
    parser.display_info.AddCacheUpdater(flags.BackendServicesCompleter)
    signed_url_flags.AddSignedUrlCacheMaxAge(parser, required=False)

    if support_failover:
      flags.AddConnectionDrainOnFailover(parser, default=None)
      flags.AddDropTrafficIfUnhealthy(parser, default=None)
      flags.AddFailoverRatio(parser)

    if support_logging:
      flags.AddEnableLogging(parser, default=None)
      flags.AddLoggingSampleRate(parser)

    if support_multinic:
      flags.AddNetwork(parser)

  def __init__(self, support_l7_internal_load_balancer, support_failover,
               support_logging, support_multinic):
    self._support_l7_internal_load_balancer = support_l7_internal_load_balancer
    self._support_failover = support_failover
    self._support_logging = support_logging
    self._support_multinic = support_multinic

  def _CreateGlobalRequests(self, holder, args, backend_services_ref):
    """Returns a global backend service create request."""

    if args.load_balancing_scheme == 'INTERNAL':
      raise exceptions.ToolException(
          'Must specify --region for internal load balancer.')
    if (self._support_failover and
        (args.IsSpecified('connection_drain_on_failover') or
         args.IsSpecified('drop_traffic_if_unhealthy') or
         args.IsSpecified('failover_ratio'))):
      raise exceptions.InvalidArgumentException(
          '--global',
          'cannot specify failover policies for global backend services.')
    backend_service = self._CreateBackendService(holder, args,
                                                 backend_services_ref)

    client = holder.client
    if args.connection_draining_timeout is not None:
      backend_service.connectionDraining = (
          client.messages.ConnectionDraining(
              drainingTimeoutSec=args.connection_draining_timeout))

    if args.enable_cdn:
      backend_service.enableCDN = args.enable_cdn

    backend_services_utils.ApplyCdnPolicyArgs(
        client,
        args,
        backend_service,
        is_update=False,
        apply_signed_url_cache_max_age=True)

    if args.session_affinity is not None:
      backend_service.sessionAffinity = (
          client.messages.BackendService.SessionAffinityValueValuesEnum(
              args.session_affinity))
    if args.affinity_cookie_ttl is not None:
      backend_service.affinityCookieTtlSec = args.affinity_cookie_ttl
    if args.custom_request_header is not None:
      backend_service.customRequestHeaders = args.custom_request_header

    self._ApplyIapArgs(client.messages, args.iap, backend_service)

    if args.load_balancing_scheme != 'EXTERNAL':
      backend_service.loadBalancingScheme = (
          client.messages.BackendService.LoadBalancingSchemeValueValuesEnum(
              args.load_balancing_scheme))

    backend_services_utils.ApplyLogConfigArgs(
        client.messages,
        args,
        backend_service,
        support_logging=self._support_logging)

    request = client.messages.ComputeBackendServicesInsertRequest(
        backendService=backend_service, project=backend_services_ref.project)

    return [(client.apitools_client.backendServices, 'Insert', request)]

  def _CreateRegionalRequests(self, holder, args, backend_services_ref):
    """Returns a regional backend service create request."""

    if (not args.cache_key_include_host or
        not args.cache_key_include_protocol or
        not args.cache_key_include_query_string or
        args.cache_key_query_string_blacklist is not None or
        args.cache_key_query_string_whitelist is not None):
      raise exceptions.ToolException(
          'Custom cache key flags cannot be used for regional requests.')

    if (self._support_multinic and args.IsSpecified('network') and
        args.load_balancing_scheme != 'INTERNAL'):
      raise exceptions.InvalidArgumentException(
          '--network', 'can only specify network for INTERNAL backend service.')

    backend_service = self._CreateRegionBackendService(holder, args,
                                                       backend_services_ref)
    client = holder.client

    if args.connection_draining_timeout is not None:
      backend_service.connectionDraining = client.messages.ConnectionDraining(
          drainingTimeoutSec=args.connection_draining_timeout)
    if args.custom_request_header is not None:
      backend_service.customRequestHeaders = args.custom_request_header
    backend_services_utils.ApplyFailoverPolicyArgs(client.messages, args,
                                                   backend_service,
                                                   self._support_failover)

    if args.session_affinity is not None:
      backend_service.sessionAffinity = (
          client.messages.BackendService.SessionAffinityValueValuesEnum(
              args.session_affinity))

    if args.port_name is not None:
      backend_service.portName = args.port_name

    if self._support_multinic and args.IsSpecified('network'):
      backend_service.network = flags.NETWORK_ARG.ResolveAsResource(
          args, holder.resources).SelfLink()

    request = client.messages.ComputeRegionBackendServicesInsertRequest(
        backendService=backend_service,
        region=backend_services_ref.region,
        project=backend_services_ref.project)

    return [(client.apitools_client.regionBackendServices, 'Insert', request)]

  def _CreateBackendService(self, holder, args, backend_services_ref):
    health_checks = flags.GetHealthCheckUris(args, self, holder.resources)
    enable_cdn = True if args.enable_cdn else None

    return holder.client.messages.BackendService(
        description=args.description,
        name=backend_services_ref.Name(),
        healthChecks=health_checks,
        portName=_ResolvePortName(args),
        protocol=_ResolveProtocol(holder.client.messages, args),
        timeoutSec=args.timeout,
        enableCDN=enable_cdn)

  def _CreateRegionBackendService(self, holder, args, backend_services_ref):
    """Creates a regional backend service."""

    health_checks = flags.GetHealthCheckUris(args, self, holder.resources)
    messages = holder.client.messages

    return messages.BackendService(
        description=args.description,
        name=backend_services_ref.Name(),
        healthChecks=health_checks,
        loadBalancingScheme=(
            messages.BackendService.LoadBalancingSchemeValueValuesEnum(
                args.load_balancing_scheme)),
        protocol=_ResolveProtocol(messages, args, default='TCP'),
        timeoutSec=args.timeout)

  def _ApplyIapArgs(self, messages, iap_arg, backend_service):
    if iap_arg is not None:
      backend_service.iap = backend_services_utils.GetIAP(iap_arg, messages)
      if backend_service.iap.enabled:
        log.warning(backend_services_utils.IapBestPracticesNotice())
      if (backend_service.iap.enabled and backend_service.protocol is
          not messages.BackendService.ProtocolValueValuesEnum.HTTPS):
        log.warning(backend_services_utils.IapHttpWarning())

  def Run(self, args, holder):
    """Issues request necessary to create Backend Service."""

    client = holder.client
    ref = flags.GLOBAL_REGIONAL_BACKEND_SERVICE_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))
    if ref.Collection() == 'compute.backendServices':
      requests = self._CreateGlobalRequests(holder, args, ref)
    elif ref.Collection() == 'compute.regionBackendServices':
      requests = self._CreateRegionalRequests(holder, args, ref)

    return client.MakeRequests(requests)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class CreateGA(base.CreateCommand):
  """Create a backend service.

  *{command}* is used to create backend services. Backend
  services define groups of backends that can receive
  traffic. Each backend group has parameters that define the
  group's capacity (e.g. max CPU utilization, max queries per
  second, ...). URL maps define which requests are sent to which
  backend services.

  Backend services created through this command will start out
  without any backend groups. To add backend groups, use 'gcloud
  compute backend-services add-backend' or 'gcloud compute
  backend-services edit'.
  """

  _support_l7_internal_load_balancer = True
  _support_failover = True
  _support_logging = True
  _support_multinic = True
  _support_client_only = False
  _support_grpc_protocol = False

  @classmethod
  def Args(cls, parser):
    CreateHelper.Args(
        parser,
        support_l7_internal_load_balancer=cls
        ._support_l7_internal_load_balancer,
        support_failover=cls._support_failover,
        support_logging=cls._support_logging,
        support_multinic=cls._support_multinic,
        support_client_only=cls._support_client_only,
        support_grpc_protocol=cls._support_grpc_protocol)

  def Run(self, args):
    """Issues request necessary to create Backend Service."""

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    return CreateHelper(
        support_l7_internal_load_balancer=self
        ._support_l7_internal_load_balancer,
        support_failover=self._support_failover,
        support_logging=self._support_logging,
        support_multinic=self._support_multinic).Run(args, holder)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(CreateGA):
  """Create a backend service.

  *{command}* is used to create backend services. Backend
  services define groups of backends that can receive
  traffic. Each backend group has parameters that define the
  group's capacity (e.g. max CPU utilization, max queries per
  second, ...). URL maps define which requests are sent to which
  backend services.

  Backend services created through this command will start out
  without any backend groups. To add backend groups, use 'gcloud
  compute backend-services add-backend' or 'gcloud compute
  backend-services edit'.
  """
  _support_multinic = True
  _support_client_only = False
  _support_grpc_protocol = False


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(CreateBeta):
  """Create a backend service.

  *{command}* is used to create backend services. Backend
  services define groups of backends that can receive
  traffic. Each backend group has parameters that define the
  group's capacity (e.g. max CPU utilization, max queries per
  second, ...). URL maps define which requests are sent to which
  backend services.

  Backend services created through this command will start out
  without any backend groups. To add backend groups, use 'gcloud
  compute backend-services add-backend' or 'gcloud compute
  backend-services edit'.
  """
  _support_client_only = True
  _support_grpc_protocol = True
