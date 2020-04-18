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

import collections

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.events import eventflow_operations
from googlecloudsdk.command_lib.events import exceptions
from googlecloudsdk.command_lib.events import resource_args
from googlecloudsdk.command_lib.events import util
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import flags as serverless_flags
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import log


SerializedTriggerAndSource = collections.namedtuple(
    'SerializedTriggerAndSource', 'serialized_trigger serialized_source')


class Describe(base.Command):
  """Get details about a given trigger."""

  detailed_help = {
      'DESCRIPTION': """\
          {description}
          """,
      'EXAMPLES': """\
          To get details about a given trigger:

              $ {command} TRIGGER
          """,
  }

  @staticmethod
  def CommonArgs(parser):
    """Defines arguments common to all release tracks."""
    trigger_presentation = presentation_specs.ResourcePresentationSpec(
        'trigger',
        resource_args.GetTriggerResourceSpec(),
        'Name of the trigger to delete',
        required=True)
    concept_parsers.ConceptParser([trigger_presentation]).AddToParser(parser)
    parser.display_info.AddFormat("""multi[separator='\n'](
        serialized_trigger:format="yaml",
        serialized_source:format="yaml(spec)")""")

  @staticmethod
  def Args(parser):
    Describe.CommonArgs(parser)

  def Run(self, args):
    """Executes when the user runs the describe command."""
    conn_context = connection_context.GetConnectionContext(
        args, serverless_flags.Product.EVENTS, self.ReleaseTrack())

    trigger_ref = args.CONCEPTS.trigger.Parse()
    with eventflow_operations.Connect(conn_context) as client:
      trigger_obj = client.GetTrigger(trigger_ref)
      source_obj = None
      if trigger_obj is not None:
        source_crds = client.ListSourceCustomResourceDefinitions()
        source_ref, source_crd = util.GetSourceRefAndCrdForTrigger(
            trigger_obj, source_crds)
        if source_ref and source_crd:
          source_obj = client.GetSource(source_ref, source_crd)

    if not trigger_obj:
      raise exceptions.TriggerNotFound(
          'Trigger [{}] not found.'.format(trigger_ref.Name()))
    if not source_obj:
      log.warning('No matching event source for trigger [{}].'.format(
          trigger_ref.Name()))
    return SerializedTriggerAndSource(
        trigger_obj.MakeSerializable(),
        source_obj.MakeSerializable() if source_obj else None)
