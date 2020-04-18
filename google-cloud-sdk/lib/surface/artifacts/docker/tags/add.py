# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Add a tag to a container image in Artifact Registry."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.artifacts import docker_util
from googlecloudsdk.command_lib.artifacts import flags


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Add(base.Command):
  """Add a tag to a container image in Artifact Registry.

  Create or update a tag for a container image in Artifact Registry.

  A valid Docker tag has the format of

    LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY-ID/IMAGE:tag

  A valid container image that can be referenced by tag or digest, has the
  format of

    LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY-ID/IMAGE:tag
    LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY-ID/IMAGE@sha256:digest
  """

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
  To add tag `my-tag` to image `busy-box` referenced by digest `abcxyz` in `us-west1`:

    $ {command} us-west1-docker.pkg.dev/my-project/my-repository/busy-box@sha256:abcxyz us-west1-docker.pkg.dev/my-project/my-repository/busy-box:my-tag

  To add tag `my-tag` to image `busy-box` referenced by tag `latest` in `us-west1`:

    $ {command} us-west1-docker.pkg.dev/my-project/my-repository/busy-box:latest us-west1-docker.pkg.dev/my-project/my-repository/busy-box:my-tag
  """,
  }

  @staticmethod
  def Args(parser):
    flags.GetDockerImageRequiredArg().AddToParser(parser)
    flags.GetTagRequiredArg().AddToParser(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.
    """
    docker_util.AddDockerTag(args)
