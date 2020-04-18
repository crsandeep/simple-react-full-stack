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
"""Commands for updating backend services.

   There are separate alpha, beta, and GA command classes in this file.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.backend_services import (
    client as backend_service_client)
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import signed_url_flags
from googlecloudsdk.command_lib.compute.backend_services import backend_services_utils
from googlecloudsdk.command_lib.compute.backend_services import flags
from googlecloudsdk.command_lib.compute.security_policies import (
    flags as security_policy_flags)
from googlecloudsdk.core import log
from googlecloudsdk.core import resources as resources_exceptions


def AddIapFlag(parser):
  # TODO(b/34479878): It would be nice if the auto-generated help text were
  # a bit better so we didn't need to be quite so verbose here.
  flags.AddIap(
      parser,
      help="""\
      Change the Identity Aware Proxy (IAP) service configuration for the
      backend service. You can set IAP to 'enabled' or 'disabled', or modify
      the OAuth2 client configuration (oauth2-client-id and
      oauth2-client-secret) used by IAP. If any fields are unspecified, their
      values will not be modified. For instance, if IAP is enabled,
      '--iap=disabled' will disable IAP, and a subsequent '--iap=enabled' will
      then enable it with the same OAuth2 client configuration as the first
      time it was enabled. See
      https://cloud.google.com/iap/ for more information about this feature.
      """)


class UpdateHelper(object):
  """Helper class that updates a backend service."""

  HEALTH_CHECK_ARG = None
  HTTP_HEALTH_CHECK_ARG = None
  HTTPS_HEALTH_CHECK_ARG = None
  SECURITY_POLICY_ARG = None

  @classmethod
  def Args(cls, parser, support_l7_internal_load_balancer, support_failover,
           support_logging, support_client_only, support_grpc_protocol):
    """Add all arguments for updating a backend service."""

    flags.GLOBAL_REGIONAL_BACKEND_SERVICE_ARG.AddArgument(
        parser, operation_type='update')
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
    flags.AddNoHealthChecks(parser)
    cls.SECURITY_POLICY_ARG = (
        security_policy_flags.SecurityPolicyArgumentForTargetResource(
            resource='backend service'))
    cls.SECURITY_POLICY_ARG.AddArgument(parser)
    flags.AddTimeout(parser, default=None)
    flags.AddPortName(parser)
    flags.AddProtocol(
        parser, default=None, support_grpc_protocol=support_grpc_protocol)

    flags.AddConnectionDrainingTimeout(parser)
    flags.AddEnableCdn(parser)
    flags.AddCacheKeyIncludeProtocol(parser, default=None)
    flags.AddCacheKeyIncludeHost(parser, default=None)
    flags.AddCacheKeyIncludeQueryString(parser, default=None)
    flags.AddCacheKeyQueryStringList(parser)
    flags.AddSessionAffinity(parser, support_client_only=support_client_only)
    flags.AddAffinityCookieTtl(parser)
    signed_url_flags.AddSignedUrlCacheMaxAge(
        parser, required=False, unspecified_help='')
    if support_failover:
      flags.AddConnectionDrainOnFailover(parser, default=None)
      flags.AddDropTrafficIfUnhealthy(parser, default=None)
      flags.AddFailoverRatio(parser)

    if support_logging:
      flags.AddEnableLogging(parser, default=None)
      flags.AddLoggingSampleRate(parser)

    AddIapFlag(parser)
    flags.AddCustomRequestHeaders(parser, remove_all_flag=True, default=None)

  def __init__(self, support_l7_internal_load_balancer, support_failover,
               support_logging):
    self._support_l7_internal_load_balancer = support_l7_internal_load_balancer
    self._support_failover = support_failover
    self._support_logging = support_logging

  def Modify(self, client, resources, args, existing):
    """Modify Backend Service."""
    replacement = encoding.CopyProtoMessage(existing)

    if args.connection_draining_timeout is not None:
      replacement.connectionDraining = client.messages.ConnectionDraining(
          drainingTimeoutSec=args.connection_draining_timeout)
    if args.no_custom_request_headers is not None:
      replacement.customRequestHeaders = []
    if args.custom_request_header is not None:
      replacement.customRequestHeaders = args.custom_request_header

    if args.IsSpecified('description'):
      replacement.description = args.description

    health_checks = flags.GetHealthCheckUris(args, self, resources)
    if health_checks or args.IsSpecified('no_health_checks'):
      replacement.healthChecks = health_checks

    if args.timeout:
      replacement.timeoutSec = args.timeout

    if args.port_name:
      replacement.portName = args.port_name

    if args.protocol:
      replacement.protocol = (
          client.messages.BackendService.ProtocolValueValuesEnum(args.protocol))

    if args.enable_cdn is not None:
      replacement.enableCDN = args.enable_cdn

    if args.session_affinity is not None:
      replacement.sessionAffinity = (
          client.messages.BackendService.SessionAffinityValueValuesEnum(
              args.session_affinity))

    if args.affinity_cookie_ttl is not None:
      replacement.affinityCookieTtlSec = args.affinity_cookie_ttl

    if args.connection_draining_timeout is not None:
      replacement.connectionDraining = client.messages.ConnectionDraining(
          drainingTimeoutSec=args.connection_draining_timeout)

    backend_services_utils.ApplyCdnPolicyArgs(
        client,
        args,
        replacement,
        is_update=True,
        apply_signed_url_cache_max_age=True)

    self._ApplyIapArgs(client, args.iap, existing, replacement)

    cleared_fields = []
    if not replacement.customRequestHeaders:
      cleared_fields.append('customRequestHeaders')

    backend_services_utils.ApplyFailoverPolicyArgs(
        client.messages,
        args,
        replacement,
        support_failover=self._support_failover)

    backend_services_utils.ApplyLogConfigArgs(
        client.messages,
        args,
        replacement,
        support_logging=self._support_logging)

    return replacement, cleared_fields

  def ValidateArgs(self, args):
    """Validate arguments."""
    if not any([
        args.IsSpecified('affinity_cookie_ttl'),
        args.IsSpecified('connection_draining_timeout'),
        args.IsSpecified('no_custom_request_headers'),
        args.IsSpecified('custom_request_header'),
        args.IsSpecified('description'),
        args.IsSpecified('enable_cdn'),
        args.IsSpecified('cache_key_include_protocol'),
        args.IsSpecified('cache_key_include_host'),
        args.IsSpecified('cache_key_include_query_string'),
        args.IsSpecified('cache_key_query_string_whitelist'),
        args.IsSpecified('cache_key_query_string_blacklist'),
        args.IsSpecified('signed_url_cache_max_age'),
        args.IsSpecified('http_health_checks'),
        args.IsSpecified('iap'),
        args.IsSpecified('port_name'),
        args.IsSpecified('protocol'),
        args.IsSpecified('security_policy'),
        args.IsSpecified('session_affinity'),
        args.IsSpecified('timeout'),
        args.IsSpecified('connection_drain_on_failover')
        if self._support_failover else False,
        args.IsSpecified('drop_traffic_if_unhealthy')
        if self._support_failover else False,
        args.IsSpecified('failover_ratio') if self._support_failover else False,
        args.IsSpecified('enable_logging') if self._support_logging else False,
        args.IsSpecified('logging_sample_rate')
        if self._support_logging else False,
        args.IsSpecified('health_checks'),
        args.IsSpecified('https_health_checks'),
        args.IsSpecified('no_health_checks')
    ]):
      raise exceptions.ToolException('At least one property must be modified.')

  def GetSetRequest(self, client, backend_service_ref, replacement):
    """Returns a backend service patch request."""

    if (backend_service_ref.Collection() == 'compute.backendServices') and (
        self._support_failover and replacement.failoverPolicy):
      raise exceptions.InvalidArgumentException(
          '--global',
          'cannot specify failover policies for global backend services.')

    if backend_service_ref.Collection() == 'compute.regionBackendServices':
      return (
          client.apitools_client.regionBackendServices,
          'Patch',
          client.messages.ComputeRegionBackendServicesPatchRequest(
              project=backend_service_ref.project,
              region=backend_service_ref.region,
              backendService=backend_service_ref.Name(),
              backendServiceResource=replacement),
      )

    return (
        client.apitools_client.backendServices,
        'Patch',
        client.messages.ComputeBackendServicesPatchRequest(
            project=backend_service_ref.project,
            backendService=backend_service_ref.Name(),
            backendServiceResource=replacement),
    )

  def _GetSetSecurityPolicyRequest(self, client, backend_service_ref,
                                   security_policy_ref):
    backend_service = backend_service_client.BackendService(
        backend_service_ref, compute_client=client)
    return backend_service.MakeSetSecurityPolicyRequestTuple(
        security_policy=security_policy_ref)

  def GetGetRequest(self, client, backend_service_ref):
    """Create Backend Services get request."""
    if backend_service_ref.Collection() == 'compute.regionBackendServices':
      return (
          client.apitools_client.regionBackendServices,
          'Get',
          client.messages.ComputeRegionBackendServicesGetRequest(
              project=backend_service_ref.project,
              region=backend_service_ref.region,
              backendService=backend_service_ref.Name()),
      )
    return (
        client.apitools_client.backendServices,
        'Get',
        client.messages.ComputeBackendServicesGetRequest(
            project=backend_service_ref.project,
            backendService=backend_service_ref.Name()),
    )

  def _ApplyIapArgs(self, client, iap_arg, existing, replacement):
    """Applies IAP args."""
    if iap_arg is not None:
      existing_iap = existing.iap
      replacement.iap = backend_services_utils.GetIAP(
          iap_arg, client.messages, existing_iap_settings=existing_iap)
      if replacement.iap.enabled and not (existing_iap and
                                          existing_iap.enabled):
        log.warning(backend_services_utils.IapBestPracticesNotice())
      if (replacement.iap.enabled and replacement.protocol is
          not client.messages.BackendService.ProtocolValueValuesEnum.HTTPS):
        log.warning(backend_services_utils.IapHttpWarning())

  def Run(self, args, holder):
    """Issues requests necessary to update the Backend Services."""
    self.ValidateArgs(args)

    client = holder.client

    backend_service_ref = (
        flags.GLOBAL_REGIONAL_BACKEND_SERVICE_ARG.ResolveAsResource(
            args,
            holder.resources,
            scope_lister=compute_flags.GetDefaultScopeLister(client)))
    get_request = self.GetGetRequest(client, backend_service_ref)

    objects = client.MakeRequests([get_request])

    new_object, cleared_fields = self.Modify(client, holder.resources, args,
                                             objects[0])

    # If existing object is equal to the proposed object or if
    # Modify() returns None, then there is no work to be done, so we
    # print the resource and return.
    if objects[0] == new_object:
      # Only skip push if security_policy is not set.
      if getattr(args, 'security_policy', None) is None:
        log.status.Print(
            'No change requested; skipping update for [{0}].'.format(
                objects[0].name))
        return objects
      backend_service_result = []
    else:
      backend_service_request = self.GetSetRequest(client, backend_service_ref,
                                                   new_object)
      # Cleared list fields need to be explicitly identified for Patch API.
      with client.apitools_client.IncludeFields(cleared_fields):
        backend_service_result = client.MakeRequests([backend_service_request])

    # Empty string is a valid value.
    if getattr(args, 'security_policy', None) is not None:
      try:
        security_policy_ref = self.SECURITY_POLICY_ARG.ResolveAsResource(
            args, holder.resources).SelfLink()
      # If security policy is an empty string we should clear the current policy
      except resources_exceptions.InvalidResourceException:
        security_policy_ref = None
      security_policy_request = self._GetSetSecurityPolicyRequest(
          client, backend_service_ref, security_policy_ref)
      security_policy_result = client.MakeRequests([security_policy_request])
    else:
      security_policy_result = []

    return backend_service_result + security_policy_result


@base.ReleaseTracks(base.ReleaseTrack.GA)
class UpdateGA(base.UpdateCommand):
  """Update a backend service.

  *{command}* is used to update backend services.
  """

  _support_l7_internal_load_balancer = True
  _support_logging = True
  _support_failover = True
  _support_client_only = False
  _support_grpc_protocol = False

  @classmethod
  def Args(cls, parser):
    UpdateHelper.Args(
        parser,
        support_l7_internal_load_balancer=cls
        ._support_l7_internal_load_balancer,
        support_failover=cls._support_failover,
        support_logging=cls._support_logging,
        support_client_only=cls._support_client_only,
        support_grpc_protocol=cls._support_grpc_protocol)

  def Run(self, args):
    """Issues requests necessary to update the Backend Services."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    return UpdateHelper(self._support_l7_internal_load_balancer,
                        self._support_failover,
                        self._support_logging).Run(args, holder)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBeta(UpdateGA):
  """Update a backend service.

  *{command}* is used to update backend services.
  """

  _support_client_only = False
  _support_grpc_protocol = False


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(UpdateGA):
  """Update a backend service.

  *{command}* is used to update backend services.
  """

  _support_client_only = True
  _support_grpc_protocol = True
