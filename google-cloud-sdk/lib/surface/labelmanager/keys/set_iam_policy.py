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
"""SetIamPolicy command for the Label Manager - Label Keys CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.labelmanager import service as labelmanager
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.command_lib.labelmanager import arguments
from googlecloudsdk.command_lib.labelmanager import utils


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class SetIamPolicy(base.Command):
  """Sets IAM policy for a LabelKey resource.

    Sets the IAM policy for a LabelKey resource given the LabelKey's display
    name and parent or the LabelKey's numeric id and a file encoded in
    JSON or YAML that contains the IAM policy.
  """

  detailed_help = {
      'EXAMPLES':
          """
          To set the IAM policy for a LabelKey with id '123' and IAM policy
          defined in a YAML file '/path/to/my_policy.yaml', run:

            $ {command} labelKeys/123 /path/to/my_policy.yaml

          To set the IAM policy for a LabelKey with the name 'env' under
          'organization/456' and IAM policy defined in a JSON file
          '/path/to/my_policy.json', run:

            $ {command} env /path/to/my_policy.json --label-parent='organizations/456'
          """
  }

  @staticmethod
  def Args(parser):
    group = parser.add_argument_group('LabelKey.', required=True)
    arguments.AddLabelParentArgToParser(
        group,
        message=('This field is required if LABEL_KEY_ID is a display name '
                 'instead of a numeric id.'))
    arguments.AddLabelKeyIdArgToParser(group)
    arguments.AddPolicyFileArgToParser(parser)

  def Run(self, args):
    labelkeys_service = labelmanager.LabelKeysService()
    labelmanager_messages = labelmanager.LabelManagerMessages()

    if args.IsSpecified('label_parent'):
      label_key = utils.GetLabelKeyFromDisplayName(args.LABEL_KEY_ID,
                                                   args.label_parent)
    else:
      label_key = args.LABEL_KEY_ID

    policy = iam_util.ParsePolicyFile(args.POLICY_FILE,
                                      labelmanager_messages.Policy)
    policy.version = iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION

    set_iam_policy_request = labelmanager_messages.SetIamPolicyRequest(
        policy=policy)

    request = labelmanager_messages.LabelmanagerLabelKeysSetIamPolicyRequest(
        resource=label_key, setIamPolicyRequest=set_iam_policy_request)
    result = labelkeys_service.SetIamPolicy(request)
    iam_util.LogSetIamPolicy(label_key, 'LabelKey')
    return result
