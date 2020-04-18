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
"""Describe command for the Label Manager - Label Keys CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.labelmanager import service as labelmanager
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.labelmanager import arguments
from googlecloudsdk.command_lib.labelmanager import utils


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.Command):
  """Describes a LabelKey resource.

    Gets metadata for a LabelKey resource given the LabelKey's display name
    and parent or the LabelKey's numeric id.
  """

  detailed_help = {
      'EXAMPLES':
          """
          To describe a LabelKey with id '123', run:

            $ {command} labelKeys/123

          To describe a LabelKey with the name 'env' under 'organizations/123',
          run:

            $ {command} env --label_parent='organizations/123'
          """
  }

  @staticmethod
  def Args(parser):
    group = parser.add_argument_group('LabelKey.')
    arguments.AddLabelParentArgToParser(
        group,
        message=('This field is required if LABEL_KEY_ID is a display name '
                 'instead of a numeric id.'))
    arguments.AddLabelKeyIdArgToParser(group)

  def Run(self, args):
    labelkeys_service = labelmanager.LabelKeysService()
    labelmanager_messages = labelmanager.LabelManagerMessages()

    label_key_id = args.LABEL_KEY_ID

    if args.IsSpecified('label_parent'):
      label_key = utils.GetLabelKeyFromDisplayName(label_key_id,
                                                   args.label_parent)
    else:
      label_key = label_key_id

    get_request = labelmanager_messages.LabelmanagerLabelKeysGetRequest(
        name=label_key)
    return labelkeys_service.Get(get_request)
