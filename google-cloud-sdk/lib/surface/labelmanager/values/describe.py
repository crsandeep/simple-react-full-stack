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
"""Describe command for the Label Manager - Label Values CLI."""

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
  """Describes a LabelValue resource.

    Gets metadata for a LabelValue resource given the LabelValue's display name
    and parent or the LabelValue's numeric id. The parent of the LabelValue is
    always a LabelKey and the LabelKey's details can be passed as a numeric id
    or the display name along with the label-parent.
  """

  detailed_help = {
      'EXAMPLES':
          """
          To describe a LabelValue with id '123', run:

            $ {command} labelValues/123

          To describe a LabelValue with the name 'prod' that lives under
          labelKeys/456, run:

            $ {command} prod --label-key='labelKeys/456'

          To describe a LabelValue with the name 'prod' under LabelKey 'env'
          that lives under 'organizations/123', run:

            $ {command} prod --label-key='env' --label-parent='orgainzations/123'
          """
  }

  @staticmethod
  def Args(parser):
    group = parser.add_argument_group('LabelValue.')
    arguments.AddLabelValueIdArgToParser(group)
    arguments.AddLabelKeyArgToParser(
        group,
        required=False,
        message=('This field is required if LABEL_VALUE_ID is a '
                 'display name instead of a numeric id.'))
    arguments.AddLabelParentArgToParser(
        group,
        required=False,
        message=(
            'This field is required if and only if LABEL_VALUE_ID and '
            '--label-key are display names instead of one being a numeric id.'))

  def Run(self, args):
    labelvalues_service = labelmanager.LabelValuesService()
    labelmanager_messages = labelmanager.LabelManagerMessages()

    label_value = utils.GetLabelValueIfArgsAreValid(args)

    get_request = labelmanager_messages.LabelmanagerLabelValuesGetRequest(
        name=label_value)
    return labelvalues_service.Get(get_request)
