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
"""Access a secret version's data."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.secrets import api as secrets_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.secrets import args as secrets_args
from googlecloudsdk.command_lib.secrets import fmt as secrets_fmt
from googlecloudsdk.command_lib.secrets import util as secrets_util


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Access(base.DescribeCommand):
  r"""Access a secret version's data.

  Access the data for the specified secret version.

  ## EXAMPLES

  Access the data for version 123 of the secret 'my-secret':

    $ {command} 123 --secret=my-secret
  """

  @staticmethod
  def Args(parser):
    secrets_args.AddVersion(
        parser, purpose='to access', positional=True, required=True)
    secrets_fmt.UseSecretData(parser)

  def Run(self, args):
    version_ref = args.CONCEPTS.version.Parse()
    return secrets_api.Versions(
        version=secrets_util.GetVersionFromReleasePath(
            self.ReleaseTrack())).Access(version_ref)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class AccessBeta(Access):
  r"""Access a secret version's data.

  Access the data for the specified secret version.

  ## EXAMPLES

  Access the data for version 123 of the secret 'my-secret':

    $ {command} 123 --secret=my-secret
  """

  @staticmethod
  def Args(parser):
    secrets_args.AddBetaVersion(
        parser, purpose='to access', positional=True, required=True)
    secrets_fmt.UseSecretData(parser)
