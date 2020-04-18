# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""List the subordinate certificate authorities within a project."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.api_lib.util import common_args
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.privateca import text_utils
from googlecloudsdk.core import properties


class List(base.ListCommand):
  """List the subordinate certificate authorities within a location."""

  @staticmethod
  def Args(parser):
    base.Argument(
        '--location',
        help='Location of the certificate authorities.'
    ).AddToParser(parser)
    base.PAGE_SIZE_FLAG.SetDefault(parser, 100)
    base.FILTER_FLAG.RemoveFromParser(parser)

    parser.display_info.AddFormat("""
        table(
          name.basename(),
          name.scope().segment(-3):label=LOCATION,
          state,
          ca_certificate_description.subject_description.not_before_time():label=NOT_BEFORE,
          ca_certificate_description.subject_description.not_after_time():label=NOT_AFTER)
        """)
    parser.display_info.AddTransforms({
        'not_before_time': text_utils.TransformNotBeforeTime,
        'not_after_time': text_utils.TransformNotAfterTime
    })

  def Run(self, args):
    client = privateca_base.GetClientInstance()
    messages = privateca_base.GetMessagesModule()

    location = args.location if args.IsSpecified('location') else '-'
    # TODO(b/150170650): Add location validation.

    parent_resource = 'projects/{}/locations/{}'.format(
        properties.VALUES.core.project.GetOrFail(),
        location)

    request = messages.PrivatecaProjectsLocationsCertificateAuthoritiesListRequest(
        parent=parent_resource,
        filter='type:SUBORDINATE',
        orderBy=common_args.ParseSortByArg(args.sort_by),
        pageSize=args.page_size)

    return list_pager.YieldFromList(
        client.projects_locations_certificateAuthorities,
        request,
        field='certificateAuthorities',
        limit=args.limit,
        batch_size_attribute='pageSize')
