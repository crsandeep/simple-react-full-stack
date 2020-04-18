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
from googlecloudsdk.core import yaml
from googlecloudsdk.core.console import console_io

MEMBERSHIP_FLAG = '--membership'
CONFIG_YAML_FLAG = '--config'
membership = None


class Apply(base.UpdateCommand):
  r"""Update Configmanagement Feature Spec.

  This command apply ConfigManagement CR with user-specified config yaml file.

  ## Examples

  Apply ConfigManagement yaml file:

    $ {command} --membership=CLUSTER_NAME \
    --config=/path/to/config-management.yaml
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
    parser.add_argument(
        CONFIG_YAML_FLAG,
        type=str,
        help=textwrap.dedent("""\
            The path to config-management.yaml.
            """),
        required=True)

  def Run(self, args):
    project = properties.VALUES.core.project.GetOrFail()
    memberships = base.ListMemberships(project)
    if not memberships:
      raise exceptions.Error('No Memberships available in Hub.')
    # User should choose an existing membership if not provide one
    global membership
    if not args.membership:
      index = console_io.PromptChoice(
          options=memberships,
          message='Please specify a membership to apply {}:\n'.format(
              args.config))
      membership = memberships[index]
    else:
      membership = args.membership
      if membership not in memberships:
        raise exceptions.Error(
            'Membership {} is not in Hub.'.format(membership))

    try:
      loaded_cm = yaml.load_path(args.config)
    except yaml.Error as e:
      raise exceptions.Error(
          'Invalid config yaml file {}'.format(args.config), e)
    client = core_apis.GetClientInstance('gkehub', 'v1alpha1')
    msg = client.MESSAGES_MODULE
    git_config = msg.GitConfig()
    _parse_config(loaded_cm, git_config)
    applied_config = msg.ConfigManagementFeatureSpec.MembershipConfigsValue.AdditionalProperty(
        key=membership,
        value=msg.MembershipConfig(configSync=msg.ConfigSync(git=git_config)))
    # UpdateFeature uses patch method to update membership_configs map,
    # there's no need to get the existing feature spec
    m_configs = msg.ConfigManagementFeatureSpec.MembershipConfigsValue(
        additionalProperties=[applied_config])
    self.RunCommand(
        'configmanagement_feature_spec.membership_configs',
        configmanagementFeatureSpec=msg.ConfigManagementFeatureSpec(
            membershipConfigs=m_configs))


def _parse_config(configmanagement, git_config):
  """Load GitConfig with the parsed configmanagement yaml.

  Args:
    configmanagement: The dict loaded from yaml.
    git_config: The GitConfig to hold configmanagement.spec.git being used in
      feature spec
  """
  if not isinstance(configmanagement, dict):
    raise exceptions.Error('Invalid Configmanagement template.')
  if('spec' not in configmanagement or 'git' not in configmanagement['spec']):
    raise exceptions.Error('Missing .spec.git in Configmanagement template')
  if ('apiVersion' not in configmanagement or
      configmanagement['apiVersion'] != 'configmanagement.gke.io/v1'):
    raise exceptions.Error(
        'Only support "apiVersion: configmanagement.gke.io/v1"')
  if ('kind' not in configmanagement or
      configmanagement['kind'] != 'ConfigManagement'):
    raise exceptions.Error('Only support "kind: ConfigManagement"')
  for field in configmanagement['spec']:
    if field != 'git':
      raise exceptions.Error(
          'Please remove illegal field .spec.{}'.format(field))
  spec_git = configmanagement['spec']['git']
  # https://cloud.google.com/anthos-config-management/docs/how-to/installing#configuring-git-repo
  # Required field
  for field in ['syncRepo', 'secretType']:
    if field not in spec_git:
      raise exceptions.Error('Missing required field [{}].'.format(field))
  for field in [
      'policyDir', 'secretType', 'syncBranch', 'syncRepo', 'syncRev', 'syncWait'
  ]:
    if field in spec_git:
      setattr(git_config, field, spec_git[field])
