# -*- coding: utf-8 -*- #
# Copyright 2020 Google Inc. All Rights Reserved.
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
"""Command for updating security policies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.security_policies import client
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute.security_policies import flags
from googlecloudsdk.command_lib.compute.security_policies import security_policies_utils


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(base.UpdateCommand):
  """Update a Google Compute Engine security policy.

  *{command}* is used to update security policies.

  ## EXAMPLES

  To update the description run this:

    $ {command} SECURITY_POLICY --description='new description'
  """

  SECURITY_POLICY_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.SECURITY_POLICY_ARG = flags.SecurityPolicyArgument()
    cls.SECURITY_POLICY_ARG.AddArgument(parser, operation_type='update')
    parser.add_argument(
        '--description',
        help=('An optional, textual description for the security policy.'))

    parser.add_argument(
        '--enable-ml',
        action='store_true',
        default=None,
        help=('Whether to enable Cloud Armor Adaptive Protection'))

  def _ValidateArgs(self, args):
    """Validates that at least one field to update is specified.

    Args:
      args: The arguments given to the update-backend command.
    """

    if not (args.IsSpecified('description') or args.IsSpecified('enable_ml')):
      parameter_names = ['--description', '--enable_ml']
      raise exceptions.MinimumArgumentException(
          parameter_names, 'Please specify at least one property to update')

  def Run(self, args):
    self._ValidateArgs(args)

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    ref = self.SECURITY_POLICY_ARG.ResolveAsResource(
        args, holder.resources)
    security_policy = client.SecurityPolicy(
        ref=ref, compute_client=holder.client)
    existing_security_policy = security_policy.Describe()[0]
    description = existing_security_policy.description
    cloud_armor_config = existing_security_policy.cloudArmorConfig
    if args.description is not None:
      description = args.description
    if args.enable_ml is not None:
      cloud_armor_config = security_policies_utils.CreateCloudArmorConfig(
          holder.client, args)
    updated_security_policy = holder.client.messages.SecurityPolicy(
        description=description,
        cloudArmorConfig=cloud_armor_config,
        fingerprint=existing_security_policy.fingerprint)

    return security_policy.Patch(security_policy=updated_security_policy)
