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
"""Create command for the Label Manager - Label Keys CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.labelmanager import service as labelmanager
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.labelmanager import arguments
from googlecloudsdk.command_lib.labelmanager import operations


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.Command):
  r"""Creates a LabelKey resource under the specified label parent.

  ## EXAMPLES

  To create a LabelKey with the name env under 'organizations/123' with
  description 'description', run:

        $ {command} env --label_parent='organizations/123'
        --description='description'
  """

  @staticmethod
  def Args(parser):
    group = parser.add_argument_group('LabelKey.', required=True)
    arguments.AddLabelParentArgToParser(group, required=True)
    arguments.AddDisplayNameArgToParser(group)
    arguments.AddDescriptionArgToParser(parser)
    arguments.AddAsyncArgToParser(parser)

  def Run(self, args):
    labelkeys_service = labelmanager.LabelKeysService()
    labelmanager_messages = labelmanager.LabelManagerMessages()

    display_name = args.DISPLAY_NAME
    label_parent = args.label_parent
    description = args.description

    create_request = labelmanager_messages.LabelKey(
        displayName=display_name, parent=label_parent, description=description)
    op = labelkeys_service.Create(create_request)

    if args.async_:
      return op
    else:
      done_op = operations.WaitForOperation(
          op,
          'Waiting for LabelKey [{}] to be created with [{}]'.format(
              display_name, op.name),
          service=labelkeys_service)
      return done_op
