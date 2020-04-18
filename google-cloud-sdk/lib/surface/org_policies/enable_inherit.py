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
"""Enable-inherit command for the Org Policy CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.org_policies import interfaces


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class EnableInherit(interfaces.OrgPolicyGetAndUpdateCommand):
  r"""Enable inheritance of policy behavior from parent resources.

  Enables inheritance of policy behavior from parent resources.

  ## EXAMPLES

  To enable inheritance of policy behavior on the policy associated with the
  constraint 'gcp.resourceLocations' and the Project 'foo-project', run:

    $ {command} gcp.resourceLocations --project=foo-project
  """

  def UpdatePolicy(self, policy, args):
    """Sets the inheritFromParent field on the policy to True.

    Args:
      policy: messages.GoogleCloudOrgpolicyV2alpha1Policy, The policy to be
        updated.
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the Args method.

    Returns:
      The updated policy.
    """
    new_policy = copy.deepcopy(policy)
    new_policy.spec.inheritFromParent = True

    return new_policy
