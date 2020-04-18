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
"""List network endpoint groups command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class List(base.ListCommand):
  """Lists Google Compute Engine network endpoint groups."""

  detailed_help = base_classes.GetMultiScopeListerHelp(
      'network endpoint groups',
      [base_classes.ScopeType.zonal_scope, base_classes.ScopeType.global_scope])
  support_global_scope = True
  support_regional_scope = False

  @classmethod
  def Args(cls, parser):
    parser.display_info.AddFormat("""\
        table(
            name,
            selfLink.scope().segment(-3).yesno(no="global"):label=LOCATION,
            networkEndpointType:label=ENDPOINT_TYPE,
            size
        )
        """)
    lister.AddMultiScopeListerFlags(
        parser,
        zonal=True,
        regional=cls.support_regional_scope,
        global_=cls.support_global_scope)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    request_data = lister.ParseMultiScopeFlags(args, holder.resources)
    list_implementation = lister.MultiScopeLister(
        client,
        zonal_service=client.apitools_client.networkEndpointGroups,
        regional_service=client.apitools_client.regionNetworkEndpointGroups
        if self.support_regional_scope else None,
        global_service=client.apitools_client.globalNetworkEndpointGroups
        if self.support_global_scope else None,
        aggregation_service=client.apitools_client.networkEndpointGroups)

    return lister.Invoke(request_data, list_implementation)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListAlpha(List):
  """Lists Google Compute Engine network endpoint groups."""

  detailed_help = base_classes.GetMultiScopeListerHelp(
      'network endpoint groups', [
          base_classes.ScopeType.zonal_scope,
          base_classes.ScopeType.regional_scope,
          base_classes.ScopeType.global_scope
      ])
  support_regional_scope = True
