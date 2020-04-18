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
"""Create command for the Label Manager - Label Values CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.labelmanager import service as labelmanager
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.labelmanager import arguments
from googlecloudsdk.command_lib.labelmanager import operations
from googlecloudsdk.command_lib.labelmanager import utils


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.Command):
  """Creates a LabelValue resource.

    Creates a LabelValue resource given the display name and description as
    well as details on the parent of the LabelValue. The parent of the
    LabelValue is always a LabelKey and the LabelKey's details can be passed as
    a numeric id or the display name along with the label-parent.
  """

  detailed_help = {
      'EXAMPLES':
          """
          To create a LabelValue with the display name 'test' and the
          description 'description' under a LabelKey with display name 'env'
          under 'organizations/123', run:

            $ {command} test --label-key='env'
                --label-parent='organizations/123' --description='description'

          To create a LabelValue with the display name 'test' under LabelKey
          with id '456', run:

            $ {command} test --label-key='labelKeys/456'
                --description='description'
          """
  }

  @staticmethod
  def Args(parser):
    group = parser.add_argument_group('LabelValue.', required=False)
    arguments.AddLabelParentArgToParser(
        group,
        required=False,
        message=(' --label-parent is required when using display name instead '
                 'of numeric id for the --label-key flag.'))
    arguments.AddDisplayNameArgToParser(group)
    arguments.AddLabelKeyArgToParser(group)
    arguments.AddDescriptionArgToParser(parser)
    arguments.AddAsyncArgToParser(parser)

  def Run(self, args):
    labelvalues_service = labelmanager.LabelValuesService()
    labelmanager_messages = labelmanager.LabelManagerMessages()

    if args.IsSpecified('label_parent'):
      label_key = utils.GetLabelKeyFromDisplayName(args.label_key,
                                                   args.label_parent)
    else:
      label_key = args.label_key

    create_request = labelmanager_messages.LabelValue(
        displayName=args.DISPLAY_NAME,
        parent=label_key,
        description=args.description)
    op = labelvalues_service.Create(create_request)

    if args.async_:
      return op
    else:
      return operations.WaitForOperation(
          op,
          'Waiting for LabelValue [{}] to be created with [{}]'.format(
              args.DISPLAY_NAME, op.name),
          service=labelvalues_service)
