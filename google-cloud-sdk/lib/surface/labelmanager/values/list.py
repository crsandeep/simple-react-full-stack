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
"""List command for the Label Manager - Label Values CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.labelmanager import service as labelmanager
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.labelmanager import arguments
from googlecloudsdk.command_lib.labelmanager import utils


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """Lists LabelValues under the specified parent LabelKey.

    The LabelKey's details can be passed as a numeric id
    or the display name along with the label-parent.
  """

  detailed_help = {
      'EXAMPLES':
          """
          To list LabelValues under 'labelKeys/123', run:

            $ {command} --label-key='labelKeys/123'

          To list LabelValues under LabelKey 'env' that lives under
          'organizations/456', run:

            $ {command} --label-key='env' --label-parent='organizations/456'
          """
  }

  @staticmethod
  def Args(parser):
    group = parser.add_argument_group('LabelKey.')
    arguments.AddLabelParentArgToParser(
        group,
        message=('This field is required if --label-key is a display name '
                 'instead of a numeric id.'))
    arguments.AddLabelKeyArgToParser(
        group,
        required=True,
        message=('This flag must be specified.'))
    arguments.AddShowDeletedArgToParser(parser)
    parser.display_info.AddFormat('table(name:sort=1, displayName)')

  def Run(self, args):
    labelvalues_service = labelmanager.LabelValuesService()
    labelmanager_messages = labelmanager.LabelManagerMessages()

    label_key_id = args.label_key

    if args.IsSpecified('label_parent'):
      label_key = utils.GetLabelKeyFromDisplayName(label_key_id,
                                                   args.label_parent)
    else:
      label_key = label_key_id

    list_request = labelmanager_messages.LabelmanagerLabelValuesListRequest(
        parent=label_key, showDeleted=args.show_deleted)
    response = labelvalues_service.List(list_request)
    return response.values
