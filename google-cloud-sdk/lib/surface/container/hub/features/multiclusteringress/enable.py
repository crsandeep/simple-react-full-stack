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
"""The command to enable MultiClusterIngress Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import textwrap
import time

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.command_lib.container.hub.features import base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.core.util import retry


CONFIG_MEMBERSHIP_FLAG = '--config-membership'


class Enable(base.EnableCommand):
  """Enable MultiClusterIngress Feature.

  This command enables MultiClusterIngress Feature in Hub.

  ## Examples

  Enable MultiClusterIngress Feature:

    $ {command} --config-membership=CONFIG_MEMBERSHIP
  """

  FEATURE_NAME = 'multiclusteringress'
  FEATURE_DISPLAY_NAME = 'MultiClusterIngress'

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        CONFIG_MEMBERSHIP_FLAG,
        type=str,
        help=textwrap.dedent("""\
            Membership resource representing the cluster which hosts
            the MultiClusterIngress and MultiClusterService CustomResourceDefinitions.
            """),
    )

  def Run(self, args):
    project = properties.VALUES.core.project.GetOrFail()
    if not args.config_membership:
      memberships = base.ListMemberships(project)
      if not memberships:
        raise exceptions.Error('No Memberships available in Hub.')
      index = console_io.PromptChoice(
          options=memberships,
          message='Please specify a config membership:\n')
      config_membership = memberships[index]
    else:
      config_membership = args.config_membership
    config_membership = ('projects/{0}/locations/global/memberships/{1}'
                         .format(project,
                                 os.path.basename(config_membership)))
    result = self.RunCommand(args, multiclusteringressFeatureSpec=(
        base.CreateMultiClusterIngressFeatureSpec(
            config_membership)))

    # We only want to poll for usability if everything above succeeded.
    if result is not None:
      self.PollForUsability()

  # Continuously poll the top-level Feature status until it has the "OK"
  # code. This ensures that MCI is actually usable and that the user gets
  # clear synchronous feedback on this.
  def PollForUsability(self):
    message = 'Waiting for controller to start...'
    aborted_message = 'Aborting wait for controller to start.\n'
    timeout = 120000
    timeout_message = ('Please use the `describe` command to check Feature'
                       'state for debugging information.\n')

    project = properties.VALUES.core.project.GetOrFail()
    feature_name = 'projects/{}/locations/global/features/{}'.format(
        project, self.FEATURE_NAME)

    client = core_apis.GetClientInstance('gkehub', 'v1alpha1')
    ok_code = client.MESSAGES_MODULE.FeatureStateDetails.CodeValueValuesEnum.OK

    try:
      with progress_tracker.ProgressTracker(
          message, aborted_message=aborted_message) as tracker:

        # Sleeping before polling for usability ensures the Feature was created
        # in the backend.
        time.sleep(5)

        # Prints status update to console. We use the default spinning wheel.
        def _StatusUpdate(unused_result, unused_status):
          tracker.Tick()

        retryer = retry.Retryer(
            # It should take no more than 2 mins for the "OK" status to appear.
            max_wait_ms=timeout,
            # Wait no more than 1 seconds before retrying.
            wait_ceiling_ms=1000,
            status_update_func=_StatusUpdate)

        def _PollFunc():
          return base.GetFeature(feature_name)

        def _IsNotDone(feature, unused_state):
          feature_state = feature.featureState
          if feature_state is None or feature_state.details is None:
            return True
          return feature_state.details.code != ok_code

        return retryer.RetryOnResult(
            func=_PollFunc, should_retry_if=_IsNotDone, sleep_ms=500)

    except retry.WaitException:
      raise exceptions.Error(
          'Controller did not start in {} minutes. {}'.format(
              timeout / 60000, timeout_message))
