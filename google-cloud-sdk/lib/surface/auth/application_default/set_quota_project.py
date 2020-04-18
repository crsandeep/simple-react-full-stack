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
"""Update or add a quota project in application default credentials json."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exc
from googlecloudsdk.command_lib.resource_manager import completers
from googlecloudsdk.core import config
from googlecloudsdk.core import log
from googlecloudsdk.core.credentials import creds as c_creds

from oauth2client import client


class SetQuotaProject(base.SilentCommand):
  """Update or add a quota project in application default credentials (ADC).

  Before running this command, an ADC must already be generated using
  $gcloud auth application-default login. The quota project can be used by
  Google client libraries for billing purpose.

  ## EXAMPLES

  To update the quota project in application default credentials to
  ``my-quota-project'', run:

    $ {command} my-quota-project
  """

  @staticmethod
  def Args(parser):
    base.Argument(
        'quota_project_id',
        metavar='QUOTA_PROJECT_ID',
        completer=completers.ProjectCompleter,
        help='Quota project ID to add to application default credentials. If '
        'a quota project already exists, it will be updated.').AddToParser(
            parser)

  def Run(self, args):
    cred_file = config.ADCFilePath()
    if not os.path.isfile(cred_file):
      raise c_exc.BadFileException(
          'Application default credentials have not been set up. '
          'Run $gcloud auth application-default login to set it up before '
          'running this command.')

    creds = client.GoogleCredentials.from_stream(cred_file)
    if creds.serialization_data['type'] != 'authorized_user':
      raise c_exc.BadFileException(
          'The credentials are not user credentials, quota project '
          'cannot be inserted.')
    c_creds.ADC(creds).DumpExtendedADCToFile(
        quota_project=args.quota_project_id)
    log.status.Print("Updated the quota project in application default "
                     "credentials (ADC) to '{}'.".format(args.quota_project_id))
