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
"""Command for creating target HTTPS proxies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import target_proxies_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.ssl_certificates import (
    flags as ssl_certificates_flags)
from googlecloudsdk.command_lib.compute.ssl_policies import (flags as
                                                             ssl_policies_flags)
from googlecloudsdk.command_lib.compute.target_https_proxies import flags
from googlecloudsdk.command_lib.compute.target_https_proxies import target_https_proxies_utils
from googlecloudsdk.command_lib.compute.url_maps import flags as url_map_flags


def _DetailedHelp():
  return {
      'brief':
          'Create a target HTTPS proxy.',
      'DESCRIPTION':
          """
      *{command}* is used to create target HTTPS proxies. A target
      HTTPS proxy is referenced by one or more forwarding rules which
      specify the network traffic that the proxy is responsible for
      routing. The target HTTPS proxy points to a URL map that defines
      the rules for routing the requests. The URL map's job is to map
      URLs to backend services which handle the actual requests. The
      target HTTPS proxy also points to at most 15 SSL certificates
      used for server-side authentication. The target HTTPS proxy can
      be associated with at most one SSL policy.
      """,
      'EXAMPLES':
          """
      If there is an already-created URL map with the name URL_MAP
      and a SSL certificate named SSL_CERTIFICATE, create a
      global target HTTPS proxy pointing to this map by running:

        $ {command} PROXY_NAME --url-map=URL_MAP --ssl-certificates=SSL_CERTIFIFCATE

      Create a regional target HTTPS proxy by running:

        $ {command} PROXY_NAME --url-map=URL_MAP --ssl-certificates=SSL_CERTIFIFCATE --region=REGION_NAME
      """,
  }


def _Args(parser,
          include_l7_internal_load_balancing=False,
          traffic_director_security=False):
  """Add the target https proxies comamnd line flags to the parser."""

  parser.display_info.AddFormat(flags.DEFAULT_LIST_FORMAT)
  parser.add_argument(
      '--description',
      help='An optional, textual description for the target HTTPS proxy.')

  parser.display_info.AddCacheUpdater(
      flags.TargetHttpsProxiesCompleterAlpha if
      include_l7_internal_load_balancing else flags.TargetHttpsProxiesCompleter)
  target_proxies_utils.AddQuicOverrideCreateArgs(parser)

  if traffic_director_security:
    flags.AddProxyBind(parser, False)


def _Run(args, holder, target_https_proxy_ref, url_map_ref, ssl_cert_refs,
         ssl_policy_ref, traffic_director_security):
  """Issues requests necessary to create Target HTTPS Proxies."""
  client = holder.client

  if traffic_director_security and args.proxy_bind:
    target_https_proxy = client.messages.TargetHttpsProxy(
        description=args.description,
        name=target_https_proxy_ref.Name(),
        urlMap=url_map_ref.SelfLink(),
        sslCertificates=[ref.SelfLink() for ref in ssl_cert_refs],
        proxyBind=args.proxy_bind)
  else:
    target_https_proxy = client.messages.TargetHttpsProxy(
        description=args.description,
        name=target_https_proxy_ref.Name(),
        urlMap=url_map_ref.SelfLink(),
        sslCertificates=[ref.SelfLink() for ref in ssl_cert_refs])

  if args.IsSpecified('quic_override'):
    quic_enum = client.messages.TargetHttpsProxy.QuicOverrideValueValuesEnum
    target_https_proxy.quicOverride = quic_enum(args.quic_override)

  if ssl_policy_ref:
    target_https_proxy.sslPolicy = ssl_policy_ref.SelfLink()

  if target_https_proxies_utils.IsRegionalTargetHttpsProxiesRef(
      target_https_proxy_ref):
    request = client.messages.ComputeRegionTargetHttpsProxiesInsertRequest(
        project=target_https_proxy_ref.project,
        region=target_https_proxy_ref.region,
        targetHttpsProxy=target_https_proxy)
    collection = client.apitools_client.regionTargetHttpsProxies
  else:
    request = client.messages.ComputeTargetHttpsProxiesInsertRequest(
        project=target_https_proxy_ref.project,
        targetHttpsProxy=target_https_proxy)
    collection = client.apitools_client.targetHttpsProxies

  return client.MakeRequests([(collection, 'Insert', request)])


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a target HTTPS proxy."""

  # TODO(b/144022508): Remove _include_l7_internal_load_balancing
  _include_l7_internal_load_balancing = True
  _traffic_director_security = False

  SSL_CERTIFICATES_ARG = None
  TARGET_HTTPS_PROXY_ARG = None
  URL_MAP_ARG = None
  SSL_POLICY_ARG = None
  detailed_help = _DetailedHelp()

  @classmethod
  def Args(cls, parser):
    ssl_certificates_required = not cls._traffic_director_security

    cls.SSL_CERTIFICATES_ARG = (
        ssl_certificates_flags.SslCertificatesArgumentForOtherResource(
            'target HTTPS proxy',
            required=ssl_certificates_required,
            include_l7_internal_load_balancing=cls
            ._include_l7_internal_load_balancing))
    cls.SSL_CERTIFICATES_ARG.AddArgument(parser, cust_metavar='SSL_CERTIFICATE')

    cls.TARGET_HTTPS_PROXY_ARG = flags.TargetHttpsProxyArgument(
        include_l7_internal_load_balancing=cls
        ._include_l7_internal_load_balancing)
    cls.TARGET_HTTPS_PROXY_ARG.AddArgument(parser, operation_type='create')

    cls.URL_MAP_ARG = url_map_flags.UrlMapArgumentForTargetProxy(
        proxy_type='HTTPS',
        include_l7_internal_load_balancing=cls
        ._include_l7_internal_load_balancing)
    cls.URL_MAP_ARG.AddArgument(parser)

    cls.SSL_POLICY_ARG = (
        ssl_policies_flags.GetSslPolicyArgumentForOtherResource(
            'HTTPS', required=False))
    cls.SSL_POLICY_ARG.AddArgument(parser)

    _Args(
        parser,
        include_l7_internal_load_balancing=cls
        ._include_l7_internal_load_balancing,
        traffic_director_security=cls._traffic_director_security)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    target_https_proxy_ref = self.TARGET_HTTPS_PROXY_ARG.ResolveAsResource(
        args, holder.resources, default_scope=compute_scope.ScopeEnum.GLOBAL)
    url_map_ref = target_https_proxies_utils.ResolveTargetHttpsProxyUrlMap(
        args, self.URL_MAP_ARG, target_https_proxy_ref, holder.resources)
    ssl_cert_refs = target_https_proxies_utils.ResolveSslCertificates(
        args, self.SSL_CERTIFICATES_ARG, target_https_proxy_ref,
        holder.resources)
    ssl_policy_ref = self.SSL_POLICY_ARG.ResolveAsResource(
        args, holder.resources) if args.ssl_policy else None
    return _Run(args, holder, target_https_proxy_ref, url_map_ref,
                ssl_cert_refs, ssl_policy_ref, self._traffic_director_security)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(Create):
  _traffic_director_security = True
