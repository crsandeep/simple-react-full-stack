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
"""RemoveIamPolicyBinding command for the Label Manager - Label Keys CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.labelmanager import service as labelmanager
from googlecloudsdk.api_lib.util import http_retry
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.command_lib.labelmanager import arguments
from googlecloudsdk.command_lib.labelmanager import utils

import six.moves.http_client


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class RemoveIamPolicyBinding(base.Command):
  """Removes a policy binding from the IAM policy of a LabelKey.

     Removes an IAM policy binding for a LabelKey resource given the binding
     and an identifier for the LabelKey. The identifier can be the LabelKey's
     display name and parent or the LabelKey's ID in the form:
     labelKeys/{numeric_id}.
  """

  detailed_help = {
      'EXAMPLES':
          """
          To remove an IAM policy binding for the role of 'roles/editor' for the
          user 'test-user@gmail.com' on the LabelKey 'labelKeys/123', run:

            $ {command} labelKeys/123 --member='user:test-user@gmail.com' --role='roles/editor'

          To remove an IAM policy binding for a LabelKey with the name 'env'
          under 'organization/456' for the role of
          'roles/labelmanager.labelUser' for the user 'test-user@gmail.com',
          run:

            $ {command} env --label-parent='organizations/456' --member='user:test-user@gmail.com' --role='roles/labelmanager.labelUser'

          See https://cloud.google.com/iam/docs/managing-policies for details of
          policy role and member types.

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
    iam_util.AddArgsForRemoveIamPolicyBinding(parser, add_condition=True)

  # Allow for retries due to etag-based optimistic concurrency control
  @http_retry.RetryOnHttpStatus(six.moves.http_client.CONFLICT)
  def Run(self, args):
    labelkeys_service = labelmanager.LabelKeysService()
    labelmanager_messages = labelmanager.LabelManagerMessages()

    if args.IsSpecified('label_parent'):
      label_key = utils.GetLabelKeyFromDisplayName(args.LABEL_KEY_ID,
                                                   args.label_parent)
    else:
      label_key = args.LABEL_KEY_ID

    get_iam_policy_req = (
        labelmanager_messages.LabelmanagerLabelKeysGetIamPolicyRequest(
            resource=label_key))
    policy = labelkeys_service.GetIamPolicy(get_iam_policy_req)
    condition = iam_util.ValidateAndExtractConditionMutexRole(args)
    iam_util.RemoveBindingFromIamPolicyWithCondition(policy, args.member,
                                                     args.role, condition,
                                                     args.all)

    set_iam_policy_request = labelmanager_messages.SetIamPolicyRequest(
        policy=policy)
    request = labelmanager_messages.LabelmanagerLabelKeysSetIamPolicyRequest(
        resource=label_key, setIamPolicyRequest=set_iam_policy_request)
    result = labelkeys_service.SetIamPolicy(request)
    iam_util.LogSetIamPolicy(label_key, 'LabelKey')
    return result
