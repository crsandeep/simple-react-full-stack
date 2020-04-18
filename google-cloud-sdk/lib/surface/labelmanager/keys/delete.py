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
"""Delete command for the Label Manager - Label Keys CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.labelmanager import service as labelmanager
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.labelmanager import arguments
from googlecloudsdk.command_lib.labelmanager import operations
from googlecloudsdk.command_lib.labelmanager import utils


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Delete(base.Command):
  """Deletes the specified LabelKey resource.

    Deletes the LabelKey resource given the LabelKey's display name
    and parent or the LabelKey's numeric id.
  """

  detailed_help = {
      'EXAMPLES':
          """
          To delete a LabelKey with id '123', run:

            $ {command} labelKeys/123

          To delete a LabelKey with the 'name' env under 'organization/456',
          run:

            $ {command} env --label_parent='organizations/456'
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

    if args.IsSpecified('label_parent'):
      label_key = utils.GetLabelKeyFromDisplayName(args.LABEL_KEY_ID,
                                                   args.label_parent)
    else:
      label_key = args.LABEL_KEY_ID

    delete_request = labelmanager_messages.LabelmanagerLabelKeysDeleteRequest(
        name=label_key)
    op = labelkeys_service.Delete(delete_request)

    if op.response is not None:
      response_dict = encoding.MessageToPyValue(op.response)
      del response_dict['@type']
      return response_dict
    else:
      raise operations.OperationError(op.error.message)
