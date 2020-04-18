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

from googlecloudsdk.api_lib.events import source
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.events import eventflow_operations
from googlecloudsdk.command_lib.events import exceptions
from googlecloudsdk.command_lib.events import flags
from googlecloudsdk.command_lib.events import resource_args
from googlecloudsdk.command_lib.events import stages
from googlecloudsdk.command_lib.events import util
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import flags as serverless_flags
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core.console import progress_tracker


_SOURCE_NAME_PATTERN = 'source-for-{trigger}'


class Create(base.Command):
  """Create a trigger."""

  detailed_help = {
      'DESCRIPTION': """\
          {description}
          """,
      'EXAMPLES': """\
          To create a trigger for a Cloud Pub/Sub event type:

              $ {command} TRIGGER --type=com.google.cloud.pubsub.topic.publish
                  --parameters="topic=my-topic" --target-service=my-service
          """,
  }

  @staticmethod
  def CommonArgs(parser):
    # Flags specific to connecting to a cluster
    cluster_group = serverless_flags.GetClusterArgGroup(parser)
    flags.AddBrokerFlag(cluster_group)

    # Flags not specific to any platform
    flags.AddEventTypeFlagArg(parser)
    flags.AddTargetServiceFlag(parser, required=True)
    mutual_with_source_group = parser.add_mutually_exclusive_group()
    flags.AddCustomEventTypeFlag(mutual_with_source_group)
    source_group = mutual_with_source_group.add_group(
        'Configuration parameters for the event source.')
    flags.AddSourceFlag(source_group)
    flags.AddParametersFlags(source_group)
    flags.AddSecretsFlag(source_group)
    trigger_presentation = presentation_specs.ResourcePresentationSpec(
        'trigger',
        resource_args.GetTriggerResourceSpec(),
        'Name of the trigger to create',
        required=True)
    concept_parsers.ConceptParser([trigger_presentation]).AddToParser(parser)

  @staticmethod
  def Args(parser):
    Create.CommonArgs(parser)

  def Run(self, args):
    conn_context = connection_context.GetConnectionContext(
        args, serverless_flags.Product.EVENTS, self.ReleaseTrack())

    trigger_ref = args.CONCEPTS.trigger.Parse()
    namespace_ref = trigger_ref.Parent()
    with eventflow_operations.Connect(conn_context) as client:
      if args.custom_type:
        event_type = args.type
        source_obj = None
        tracker_stages = stages.TriggerStages()
      else:
        source_crds = client.ListSourceCustomResourceDefinitions()
        event_type = util.EventTypeFromTypeString(
            source_crds, args.type, args.source)
        source_obj = source.Source.New(client.client, namespace_ref.Name(),
                                       event_type.crd.source_kind,
                                       event_type.crd.source_api_category)
        source_obj.name = _SOURCE_NAME_PATTERN.format(
            trigger=trigger_ref.Name())
        parameters = flags.GetAndValidateParameters(args, event_type)
        tracker_stages = stages.TriggerAndSourceStages()

      trigger_obj = client.GetTrigger(trigger_ref)
      if trigger_obj is not None:
        if args.custom_type:
          # If custom type, no need to check idempotency since there's only
          # a trigger to worry about.
          raise exceptions.TriggerCreationError(
              'Trigger [{}] already exists.'.format(trigger_obj.name))
        else:
          # If trigger already exists, validate it has the attributes we're
          # trying to set right now to see if this is a case of idempotency.
          try:
            util.ValidateTrigger(trigger_obj, source_obj, event_type)
          except AssertionError:
            raise exceptions.TriggerCreationError(
                'Trigger [{}] already exists with attributes not '
                'matching this event type.'.format(trigger_obj.name))
          # If the trigger has the right attributes, check if there's already
          # a source that matches the attributes as well.
          source_ref = util.GetSourceRef(
              source_obj.name, source_obj.namespace, event_type.crd)
          if client.GetSource(source_ref, event_type.crd) is not None:
            raise exceptions.TriggerCreationError(
                'Trigger [{}] already exists.'.format(trigger_obj.name))

      # Create the trigger and source
      with progress_tracker.StagedProgressTracker(
          'Initializing trigger...',
          tracker_stages,
          failure_message='Trigger creation failed') as tracker:
        if trigger_obj is None:
          trigger_obj = client.CreateTrigger(
              trigger_ref, source_obj,
              event_type if args.custom_type else event_type.type,
              args.target_service, args.broker)
        if not args.custom_type:
          client.CreateSource(source_obj, event_type.crd, trigger_obj,
                              namespace_ref, args.broker, parameters)
          client.PollSource(source_obj, event_type, tracker)
        client.PollTrigger(trigger_ref, tracker)
