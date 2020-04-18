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

"""'logging cmek-settings describe' command."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.resource_manager import completers


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.DescribeCommand):
  # pylint: disable=line-too-long
  """Displays the CMEK settings for the Stackdriver Logs Router.

  If *kmsKeyName* is present in the output, then CMEK is enabled for your
  organization.  You can also find the Logs Router service account using this
  command.

  Customer-managed encryption keys (CMEK) for the Logs Router can currently
  only be configured at the organization-level and will apply to all projects
  in the organization.

  ## EXAMPLE

  To describe the Logs Router CMEK settings for an organization, run:

    $ {command} --organization=[ORGANIZATION_ID]

    kmsKeyName: 'projects/my-project/locations/my-location/keyRings/my-keyring/cryptoKeys/key'
    name: 'organizations/[ORGANIZATION_ID]/cmekSettings'
    serviceAccountId: '[SERVICE_ACCOUNT_ID]@gcp-sa-logging.iam.gserviceaccount.com'
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument(
        '--organization',
        required=True,
        metavar='ORGANIZATION_ID',
        completer=completers.OrganizationCompleter,
        help='Organization to show CMEK settings for.')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The CMEK settings for the specified organization.
    """
    parent_name = util.GetParentFromArgs(args)
    return util.GetClient().organizations.GetCmekSettings(
        util.GetMessages().LoggingOrganizationsGetCmekSettingsRequest(
            name=parent_name))
