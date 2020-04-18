# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Command for listing available event types."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.events import eventflow_operations
from googlecloudsdk.command_lib.events import flags
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import flags as serverless_flags


class List(base.ListCommand):
  """List available event types."""

  detailed_help = {
      'DESCRIPTION': """\
          {description}
          """,
      'EXAMPLES': """\
          To list available event types:

              $ {command}
          """,
  }

  @staticmethod
  def CommonArgs(parser):
    flags.AddSourceFlag(parser)
    base.URI_FLAG.RemoveFromParser(parser)
    parser.display_info.AddFormat("""table(
        details.type:sort=2,
        crd.source_kind:label=SOURCE:sort=1,
        details.description:wrap)""")

  @staticmethod
  def Args(parser):
    List.CommonArgs(parser)

  def Run(self, args):
    conn_context = connection_context.GetConnectionContext(
        args, serverless_flags.Product.EVENTS, self.ReleaseTrack())

    with eventflow_operations.Connect(conn_context) as client:
      source_crds = client.ListSourceCustomResourceDefinitions()
      event_types = []
      for crd in source_crds:
        if not args.IsSpecified('source') or args.source == crd.source_kind:
          event_types.extend(crd.event_types)
      return event_types
