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
"""The command to update MultiClusterIngress Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.command_lib.container.hub.features import base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io


MEMBERSHIP_FLAG = '--membership'


class Delete(base.UpdateCommand):
  """Remove Configmanagement Feature Spec for the given membership.

  This command remove Configmanagement Feature Spec for the given membership.

  ## Examples

  Apply ConfigManagement yaml file:

    $ {command} --membership=CLUSTER_NAME
  """

  FEATURE_NAME = 'configmanagement'
  FEATURE_DISPLAY_NAME = 'Config Management'

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        MEMBERSHIP_FLAG,
        type=str,
        help=textwrap.dedent("""\
            The Membership name provided during registration.
            """),
    )

  def Run(self, args):
    project = properties.VALUES.core.project.GetOrFail()
    memberships = base.ListMemberships(project)
    if not memberships:
      raise exceptions.Error('No Memberships available in Hub.')
    # User should choose an existing membership if not provide one
    if not args.membership:
      index = console_io.PromptChoice(
          options=memberships,
          message='Please specify a membership to delete configmanagement:\n')
      membership = memberships[index]
    else:
      membership = args.membership
      if membership not in memberships:
        raise exceptions.Error(
            'Membership {} is not in Hub.'.format(membership))

    client = core_apis.GetClientInstance('gkehub', 'v1alpha1')
    msg = client.MESSAGES_MODULE
    applied_config = msg.ConfigManagementFeatureSpec.MembershipConfigsValue.AdditionalProperty(
        key=membership, value=msg.MembershipConfig())
    m_configs = msg.ConfigManagementFeatureSpec.MembershipConfigsValue(
        additionalProperties=[applied_config])

    self.RunCommand(
        'configmanagement_feature_spec.membership_configs',
        configmanagementFeatureSpec=msg.ConfigManagementFeatureSpec(
            membershipConfigs=m_configs))
