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
"""Command for obtaining details about a given service."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.events import eventflow_operations
from googlecloudsdk.command_lib.events import flags
from googlecloudsdk.command_lib.events import util
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import flags as serverless_flags


class Describe(base.Command):
  """Get the details about a given event type."""

  detailed_help = {
      'DESCRIPTION': """\
          {description}
          """,
      'EXAMPLES': """\
          To get the details about a given event type:

              $ {command} EVENT_TYPE
          """,
  }

  @staticmethod
  def CommonArgs(parser):
    flags.AddEventTypePositionalArg(parser)
    flags.AddSourceFlag(parser)
    parser.display_info.AddFormat("""multi[separator='\n'](
        details:format="yaml",
        crd.properties:format="table[title='Parameter(s) to create a trigger for this event type:'](
          required.yesno(yes='Yes', no=''):sort=1:reverse,
          name:label=PARAMETER:sort=2,
          description:wrap)",
        crd.secret_properties:format="table[title='Secret parameter(s) to create a trigger for this event type:'](
          required.yesno(yes='Yes', no=''):sort=1:reverse,
          name:label=PARAMETER:sort=2,
          description:wrap)")""")

  @staticmethod
  def Args(parser):
    Describe.CommonArgs(parser)

  def Run(self, args):
    conn_context = connection_context.GetConnectionContext(
        args, serverless_flags.Product.EVENTS, self.ReleaseTrack())

    with eventflow_operations.Connect(conn_context) as client:
      source_crds = client.ListSourceCustomResourceDefinitions()
      return util.EventTypeFromTypeString(
          source_crds, args.event_type, args.source)
