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
"""Command for listing existing triggers."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.events import trigger
from googlecloudsdk.command_lib.events import eventflow_operations
from googlecloudsdk.command_lib.events import flags
from googlecloudsdk.command_lib.run import commands
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import flags as serverless_flags
from googlecloudsdk.command_lib.run import pretty_print
from googlecloudsdk.command_lib.run import resource_args
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


class List(commands.List):
  """List existing triggers."""

  detailed_help = {
      'DESCRIPTION': """\
          {description}
          """,
      'EXAMPLES': """\
          To list existing triggers:

              $ {command}
          """,
  }

  @classmethod
  def CommonArgs(cls, parser):
    # Flags specific to connecting to a cluster
    cluster_group = serverless_flags.GetClusterArgGroup(parser)
    namespace_presentation = presentation_specs.ResourcePresentationSpec(
        '--namespace',
        resource_args.GetNamespaceResourceSpec(),
        'Namespace to list triggers in.',
        required=True,
        prefixes=False)
    concept_parsers.ConceptParser(
        [namespace_presentation]).AddToParser(cluster_group)

    # Flags not specific to any platform
    flags.AddTargetServiceFlag(parser)
    parser.display_info.AddFormat("""table(
        {ready_column},
        firstof(id,metadata.name):label=TRIGGER,
        filter_attributes.extract({type_field}).join():label="EVENT TYPE",
        subscriber:label=TARGET)""".format(
            ready_column=pretty_print.READY_COLUMN,
            type_field=trigger.EVENT_TYPE_FIELD))
    parser.display_info.AddUriFunc(cls._GetResourceUri)

  @classmethod
  def Args(cls, parser):
    cls.CommonArgs(parser)

  def Run(self, args):
    conn_context = connection_context.GetConnectionContext(
        args, serverless_flags.Product.EVENTS, self.ReleaseTrack())

    namespace_ref = args.CONCEPTS.namespace.Parse()
    with eventflow_operations.Connect(conn_context) as client:
      self.SetCompleteApiEndpoint(conn_context.endpoint)
      triggers = client.ListTriggers(namespace_ref)
      if args.target_service:
        triggers = [t for t in triggers if t.subscriber == args.target_service]
      return triggers
