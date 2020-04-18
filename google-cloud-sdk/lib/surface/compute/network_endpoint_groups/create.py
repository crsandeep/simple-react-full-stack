# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Create network endpoint group command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import network_endpoint_groups
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.network_endpoint_groups import flags
from googlecloudsdk.core import log

DETAILED_HELP = {
    'EXAMPLES': """
To create a network endpoint group:

  $ {command} my-neg --zone=us-central1-a --network=my-network --subnet=my-subnetwork
""",
}


def _GetValidScopesErrorMessage(network_endpoint_type, valid_scopes):
  valid_scopes_error_message = ''
  if network_endpoint_type in valid_scopes:
    valid_scopes_error_message = (
        ' Type {0} must be specified in the {1} scope.').format(
            network_endpoint_type,
            _JoinWithOr(valid_scopes[network_endpoint_type]))
  return valid_scopes_error_message


def _Invert(dic):
  new_dic = collections.OrderedDict()
  for key, values in dic.items():
    for value in values:
      new_dic.setdefault(value, list()).append(key)
  return new_dic


def _JoinWithOr(strings):
  """Joins strings, for example, into a string like 'A or B' or 'A, B, or C'."""
  if not strings:
    return ''
  elif len(strings) == 1:
    return strings[0]
  elif len(strings) == 2:
    return strings[0] + ' or ' + strings[1]
  else:
    return ', '.join(strings[:-1]) + ', or ' + strings[-1]


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a Google Compute Engine network endpoint group."""

  detailed_help = DETAILED_HELP
  support_global_scope = True
  support_regional_scope = False
  support_neg_type = False
  support_hybrid_neg = False
  support_l4ilb_neg = False

  @classmethod
  def Args(cls, parser):
    flags.MakeNetworkEndpointGroupsArg(
        support_global_scope=cls.support_global_scope,
        support_regional_scope=cls.support_regional_scope).AddArgument(parser)
    flags.AddCreateNegArgsToParser(
        parser,
        support_neg_type=cls.support_neg_type,
        support_global_scope=cls.support_global_scope,
        support_hybrid_neg=cls.support_hybrid_neg,
        support_l4ilb_neg=cls.support_l4ilb_neg,
        support_regional_scope=cls.support_regional_scope)

  def Run(self, args):
    """Issues the request necessary for adding the network endpoint group."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = holder.client.messages
    resources = holder.resources
    neg_client = network_endpoint_groups.NetworkEndpointGroupsClient(
        client, messages, resources)
    neg_ref = flags.MakeNetworkEndpointGroupsArg(
        support_global_scope=self.support_global_scope,
        support_regional_scope=self.support_regional_scope).ResolveAsResource(
            args,
            holder.resources,
            default_scope=compute_scope.ScopeEnum.ZONE,
            scope_lister=compute_flags.GetDefaultScopeLister(holder.client))

    self._ValidateNEG(args, neg_ref)

    if self.support_regional_scope:
      result = neg_client.Create(
          neg_ref,
          args.network_endpoint_type,
          default_port=args.default_port,
          network=args.network,
          subnet=args.subnet,
          cloud_run_service=args.cloud_run_service,
          cloud_run_tag=args.cloud_run_tag,
          cloud_run_url_mask=args.cloud_run_url_mask,
          app_engine_app=args.app_engine_app,
          app_engine_service=args.app_engine_service,
          app_engine_version=args.app_engine_version,
          app_engine_url_mask=args.app_engine_url_mask,
          cloud_function_name=args.cloud_function_name,
          cloud_function_url_mask=args.cloud_function_url_mask)
    else:
      result = neg_client.Create(
          neg_ref,
          args.network_endpoint_type,
          default_port=args.default_port,
          network=args.network,
          subnet=args.subnet)
    log.CreatedResource(neg_ref.Name(), 'network endpoint group')
    return result

  def _ValidateNEG(self, args, neg_ref):
    """Validate NEG input before making request."""
    is_zonal = hasattr(neg_ref, 'zone')
    is_regional = hasattr(neg_ref, 'region')
    network_endpoint_type = args.network_endpoint_type

    valid_scopes = collections.OrderedDict()
    valid_scopes['gce-vm-ip-port'] = ['zonal']
    valid_scopes['internet-ip-port'] = ['global']
    valid_scopes['internet-fqdn-port'] = ['global']
    valid_scopes['serverless'] = ['regional']

    if self.support_hybrid_neg:
      valid_scopes['non-gcp-private-ip-port'] = ['zonal']
    if self.support_l4ilb_neg:
      valid_scopes['gce-vm-primary-ip'] = ['zonal']

    valid_scopes_inverted = _Invert(valid_scopes)

    if is_zonal:
      valid_zonal_types = valid_scopes_inverted['zonal']
      if network_endpoint_type not in valid_zonal_types:
        raise exceptions.InvalidArgumentException(
            '--network-endpoint-type',
            'Zonal NEGs only support network endpoints of type {0}.{1}'.format(
                _JoinWithOr(valid_zonal_types),
                _GetValidScopesErrorMessage(network_endpoint_type,
                                            valid_scopes)))
    elif is_regional:
      valid_regional_types = valid_scopes_inverted['regional']
      if network_endpoint_type not in valid_regional_types:
        raise exceptions.InvalidArgumentException(
            '--network-endpoint-type',
            'Regional NEGs only support network endpoints of type {0}.{1}'
            .format(
                _JoinWithOr(valid_regional_types),
                _GetValidScopesErrorMessage(network_endpoint_type,
                                            valid_scopes)))
    else:
      valid_global_types = valid_scopes_inverted['global']
      if network_endpoint_type not in valid_global_types:
        raise exceptions.InvalidArgumentException(
            '--network-endpoint-type',
            'Global NEGs only support network endpoints of type {0}.{1}'.format(
                _JoinWithOr(valid_global_types),
                _GetValidScopesErrorMessage(network_endpoint_type,
                                            valid_scopes)))
      if args.network is not None:
        raise exceptions.InvalidArgumentException(
            '--network', 'Global NEGs cannot specify network.')


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(Create):
  """Create a Google Compute Engine network endpoint group."""

  support_regional_scope = True
  support_hybrid_neg = True
  support_l4ilb_neg = True
  support_neg_type = True
