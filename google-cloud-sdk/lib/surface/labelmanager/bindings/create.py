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
"""Create command for the Label Manager - Label Bindings CLI."""

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
class Create(base.Command):
  """Creates a LabelBinding.

    Creates a LabelBinding given the LabelValue and the cloud resource the
    LabelValue will be bound to. The LabelValue can be represented with it's
    numeric id or with it's display name along with details on the parent of the
    LabelValue. The parent of the LabelValue is always a LabelKey and the
    LabelKey's details can be passed as a numeric id or the display name along
    with the label-parent. The resource should be represented with it's full
    resource name. See:
    https://cloud.google.com/apis/design/resource_names#full_resource_name.
  """

  detailed_help = {
      'EXAMPLES':
          """
          To create a LabelBinding between 'labelValue/123' and Project with name
          '//cloudresourcemanager.googleapis.com/projects/1234' run:

            $ {command} labelValue/123 --resource='//cloudresourcemanager.googleapis.com/projects/1234'

          To create a LabelBinding between LabelValue 'test' under 'labelKeys/456' and
          Project with name '//cloudresourcemanager.googleapis.com/projects/1234' run:

            $ {command} test --label-key='labelKeys/456' --resource='//cloudresourcemanager.googleapis.com/projects/1234'

          To create a LabelBinding between LabelValue 'test' under LabelKey 'env' and
          Project with name '//cloudresourcemanager.googleapis.com/projects/1234' run:

            $ {command} test --label-key='env' --label-parent='organizations/789' --resource='//cloudresourcemanager.googleapis.com/projects/1234'
          """
  }

  @staticmethod
  def Args(parser):
    group = parser.add_argument_group('LabelValue.', required=False)
    arguments.AddLabelValueIdArgToParser(group)
    arguments.AddLabelKeyArgToParser(
        group,
        required=False,
        message=(' --label-key is required when using display name instead '
                 'of numeric id for LABEL_VALUE_ID.'))
    arguments.AddLabelParentArgToParser(
        group,
        required=False,
        message=(' --label-parent is required when using display name instead '
                 'of numeric id for the --label-key.'))
    arguments.AddResourceArgToParser(parser)

  def Run(self, args):
    labelbindings_service = labelmanager.LabelBindingsService()
    labelmanager_messages = labelmanager.LabelManagerMessages()

    label_value = utils.GetLabelValueIfArgsAreValid(args)

    binding = labelmanager_messages.LabelBinding(
        labelValue=label_value, resource=args.resource)

    op = labelbindings_service.Create(binding)

    if op.response is not None:
      response_dict = encoding.MessageToPyValue(op.response)
      del response_dict['@type']
      return response_dict
    else:
      raise operations.OperationError(op.error.message)
