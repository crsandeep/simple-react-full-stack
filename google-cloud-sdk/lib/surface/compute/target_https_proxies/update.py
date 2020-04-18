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
"""Command for updating target HTTPS proxies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import target_proxies_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
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
          'Update a target HTTPS proxy.',
      'DESCRIPTION':
          """
      *{command}* is used to change the SSL certificate and/or URL map of
      existing target HTTPS proxies. A target HTTPS proxy is referenced by
      one or more forwarding rules which specify the network traffic that
      the proxy is responsible for routing. The target HTTPS proxy in turn
      points to a URL map that defines the rules for routing the requests.
      The URL map's job is to map URLs to backend services which handle
      the actual requests. The target HTTPS proxy also points to at most
      15 SSL certificates used for server-side authentication. The target
      HTTPS proxy can be associated with at most one SSL policy.
      """,
      'EXAMPLES':
          """
      Update the URL map of a global target HTTPS proxy by running:

        $ {command} PROXY_NAME --url-map=URL_MAP

      Update the SSL certificate of a global target HTTPS proxy by running:

        $ {command} PROXY_NAME --ssl-certificates=SSL_CERTIFIFCATE

      Update the URL map of a global target HTTPS proxy by running:

        $ {command} PROXY_NAME --url-map=URL_MAP --region=REGION_NAME

      Update the SSL certificate of a global target HTTPS proxy by running:

        $ {command} PROXY_NAME --ssl-certificates=SSL_CERTIFIFCATE --region=REGION_NAME
      """,
  }


def _CheckMissingArgument(args):
  if not sum(
      args.IsSpecified(arg) for arg in [
          'ssl_certificates', 'url_map', 'quic_override', 'ssl_policy',
          'clear_ssl_policy'
      ]):
    raise exceptions.ToolException(
        'You must specify at least one of [--ssl-certificates], '
        '[--url-map], [--quic-override], [--ssl-policy] or '
        '[--clear-ssl-policy].')


def _Run(args, holder, ssl_certificates_arg, target_https_proxy_arg,
         url_map_arg, ssl_policy_arg):
  """Issues requests necessary to update Target HTTPS Proxies."""
  client = holder.client

  requests = []
  target_https_proxy_ref = target_https_proxy_arg.ResolveAsResource(
      args,
      holder.resources,
      default_scope=compute_scope.ScopeEnum.GLOBAL,
      scope_lister=compute_flags.GetDefaultScopeLister(client))

  if args.ssl_certificates:
    ssl_cert_refs = target_https_proxies_utils.ResolveSslCertificates(
        args, ssl_certificates_arg, target_https_proxy_ref, holder.resources)
    if target_https_proxies_utils.IsRegionalTargetHttpsProxiesRef(
        target_https_proxy_ref):
      requests.append((
          client.apitools_client.regionTargetHttpsProxies, 'SetSslCertificates',
          client.messages
          .ComputeRegionTargetHttpsProxiesSetSslCertificatesRequest(
              project=target_https_proxy_ref.project,
              region=target_https_proxy_ref.region,
              targetHttpsProxy=target_https_proxy_ref.Name(),
              regionTargetHttpsProxiesSetSslCertificatesRequest=(
                  client.messages
                  .RegionTargetHttpsProxiesSetSslCertificatesRequest(
                      sslCertificates=[ref.SelfLink()
                                       for ref in ssl_cert_refs])))))
    else:
      requests.append((
          client.apitools_client.targetHttpsProxies, 'SetSslCertificates',
          client.messages.ComputeTargetHttpsProxiesSetSslCertificatesRequest(
              project=target_https_proxy_ref.project,
              targetHttpsProxy=target_https_proxy_ref.Name(),
              targetHttpsProxiesSetSslCertificatesRequest=(
                  client.messages.TargetHttpsProxiesSetSslCertificatesRequest(
                      sslCertificates=[ref.SelfLink()
                                       for ref in ssl_cert_refs])))))

  if args.url_map:
    url_map_ref = target_https_proxies_utils.ResolveTargetHttpsProxyUrlMap(
        args, url_map_arg, target_https_proxy_ref, holder.resources)
    if target_https_proxies_utils.IsRegionalTargetHttpsProxiesRef(
        target_https_proxy_ref):
      requests.append(
          (client.apitools_client.regionTargetHttpsProxies, 'SetUrlMap',
           client.messages.ComputeRegionTargetHttpsProxiesSetUrlMapRequest(
               project=target_https_proxy_ref.project,
               region=target_https_proxy_ref.region,
               targetHttpsProxy=target_https_proxy_ref.Name(),
               urlMapReference=client.messages.UrlMapReference(
                   urlMap=url_map_ref.SelfLink()))))
    else:
      requests.append(
          (client.apitools_client.targetHttpsProxies, 'SetUrlMap',
           client.messages.ComputeTargetHttpsProxiesSetUrlMapRequest(
               project=target_https_proxy_ref.project,
               targetHttpsProxy=target_https_proxy_ref.Name(),
               urlMapReference=client.messages.UrlMapReference(
                   urlMap=url_map_ref.SelfLink()))))

  if args.IsSpecified('quic_override'):
    quic_override = (
        client.messages.TargetHttpsProxiesSetQuicOverrideRequest
        .QuicOverrideValueValuesEnum(args.quic_override))
    requests.append(
        (client.apitools_client.targetHttpsProxies, 'SetQuicOverride',
         client.messages.ComputeTargetHttpsProxiesSetQuicOverrideRequest(
             project=target_https_proxy_ref.project,
             targetHttpsProxy=target_https_proxy_ref.Name(),
             targetHttpsProxiesSetQuicOverrideRequest=(
                 client.messages.TargetHttpsProxiesSetQuicOverrideRequest(
                     quicOverride=quic_override)))))

  ssl_policy = client.messages.SslPolicyReference(
      sslPolicy=ssl_policy_arg.ResolveAsResource(args, holder.resources)
      .SelfLink()) if args.IsSpecified('ssl_policy') else None
  clear_ssl_policy = args.IsSpecified('clear_ssl_policy')

  if ssl_policy or clear_ssl_policy:
    requests.append(
        (client.apitools_client.targetHttpsProxies, 'SetSslPolicy',
         client.messages.ComputeTargetHttpsProxiesSetSslPolicyRequest(
             project=target_https_proxy_ref.project,
             targetHttpsProxy=target_https_proxy_ref.Name(),
             sslPolicyReference=ssl_policy)))

  return client.MakeRequests(requests)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Update(base.SilentCommand):
  """Update a target HTTPS proxy."""

  # TODO(b/144022508): Remove _include_l7_internal_load_balancing
  _include_l7_internal_load_balancing = True

  SSL_CERTIFICATES_ARG = None
  TARGET_HTTPS_PROXY_ARG = None
  URL_MAP_ARG = None
  SSL_POLICY_ARG = None
  detailed_help = _DetailedHelp()

  @classmethod
  def Args(cls, parser):
    cls.SSL_CERTIFICATES_ARG = (
        ssl_certificates_flags.SslCertificatesArgumentForOtherResource(
            'target HTTPS proxy',
            required=False,
            include_l7_internal_load_balancing=cls
            ._include_l7_internal_load_balancing))
    cls.SSL_CERTIFICATES_ARG.AddArgument(parser, cust_metavar='SSL_CERTIFICATE')

    cls.TARGET_HTTPS_PROXY_ARG = flags.TargetHttpsProxyArgument(
        include_l7_internal_load_balancing=cls
        ._include_l7_internal_load_balancing)
    cls.TARGET_HTTPS_PROXY_ARG.AddArgument(parser, operation_type='update')

    cls.URL_MAP_ARG = url_map_flags.UrlMapArgumentForTargetProxy(
        required=False,
        proxy_type='HTTPS',
        include_l7_internal_load_balancing=cls
        ._include_l7_internal_load_balancing)
    cls.URL_MAP_ARG.AddArgument(parser)

    group = parser.add_mutually_exclusive_group()
    cls.SSL_POLICY_ARG = (
        ssl_policies_flags.GetSslPolicyArgumentForOtherResource(
            'HTTPS', required=False))
    cls.SSL_POLICY_ARG.AddArgument(group)
    ssl_policies_flags.GetClearSslPolicyArgumentForOtherResource(
        'HTTPS', required=False).AddToParser(group)

    target_proxies_utils.AddQuicOverrideUpdateArgs(parser)

  def Run(self, args):
    _CheckMissingArgument(args)
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    return _Run(args, holder, self.SSL_CERTIFICATES_ARG,
                self.TARGET_HTTPS_PROXY_ARG, self.URL_MAP_ARG,
                self.SSL_POLICY_ARG)
