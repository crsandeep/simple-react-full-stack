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
"""List command for the Label Manager - Label Bindings CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.labelmanager import service as labelmanager
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.labelmanager import arguments
from googlecloudsdk.command_lib.labelmanager import utils


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
# TODO(b/145234946): Add e2e test for ListLabelBindings and test --uri flag.
class List(base.ListCommand):
  """Lists LabelBindings bound to the specified resource or LabelValue.

    Only a resource or a LabelValue should be specified. When specifying
    a resource, the full name of the resource must be used. See:
    https://cloud.google.com/apis/design/resource_names#full_resource_name.
    The LabelValue can be represented with it's numeric id or with it's display
    name along with details on the parent LabelKey. The LabelKey's details
    can be passed as a numeric id or the display name along with the
    label-parent.
  """

  detailed_help = {
      'EXAMPLES':
          """
          To list LabelBindings for '//cloudresourcemanager.googleapis.com/projects/123' run:

            $ {command} --resource='//cloudresourcemanager.googleapis.com/projects/123'

          To list LabelBindings for labelValues/456 run:

            $ {command} labelValues/456

          To list LabelBindings for LabelValue 'test' under LabelKey 'labelKeys/789'
          run:

            $ {command} test --label-key='labelKeys/789'

          To list LabelBindings for LabelValue 'test' under LabelKey 'env' that
          lives under 'organizations/999' run:

            $ {command} test --label-key='env' --label-parent='organizations/999'
          """
  }

  @staticmethod
  def Args(parser):
    # Does nothing for us, included in base.ListCommand
    base.URI_FLAG.RemoveFromParser(parser)

    mutex_group = parser.add_argument_group(
        'ListLabelBindings.', required=True, mutex=True)
    label_group = mutex_group.add_argument_group('LabelValue.', required=False)
    arguments.AddLabelValueIdArgToParser(label_group)
    arguments.AddLabelKeyArgToParser(
        label_group,
        required=False,
        message=(' --label-key is required when using display name instead '
                 'of numeric id for LABEL_VALUE_ID.'))
    arguments.AddLabelParentArgToParser(
        label_group,
        required=False,
        message=(' --label-parent is required when using display name instead '
                 'of numeric id for the --label-key.'))
    arguments.AddResourceArgToParser(
        mutex_group,
        required=False,
        message=('Full resource name of the resource that the LabelValue is '
                 'bound to.'))

  def Run(self, args):
    labelbindings_service = labelmanager.LabelBindingsService()
    labelmanager_messages = labelmanager.LabelManagerMessages()

    if args.IsSpecified('resource'):
      request = (
          labelmanager_messages.LabelmanagerLabelBindingsListRequest(
              filter='resource:'+args.resource))
    else:
      label_value = utils.GetLabelValueIfArgsAreValid(args)
      request = (
          labelmanager_messages.LabelmanagerLabelBindingsListRequest(
              filter='labelValue:'+label_value))
    return labelbindings_service.List(request)
