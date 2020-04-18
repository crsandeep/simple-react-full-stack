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
"""List all tags associated with a container image in Artifact Registry."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.artifacts import docker_util
from googlecloudsdk.command_lib.artifacts import flags

TAG_LIST_FORMAT = """\
    table(
      tag.basename(),
      image,
      version.basename():label=DIGEST
    )"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class List(base.ListCommand):
  """List all tags associated with a container image in Artifact Registry.

  A valid Docker top layer image has the format of

    [<location>-]docker.pkg.dev/PROJECT-ID/REPOSITORY-ID/IMAGE_PATH

  A valid container image can be referenced by tag or digest, has the format of

    [<location>-]docker.pkg.dev/PROJECT-ID/REPOSITORY-ID/IMAGE_PATH:tag
    [<location>-]docker.pkg.dev/PROJECT-ID/REPOSITORY-ID/IMAGE_PATH@sha256:digest

  To specify the maximum number of repositories to list, use the --limit flag.
  """

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
  To list all tags under the current project, repository, and location:

    $ {command}

  To list all tags under the `my-project`, `my-repository`, across all locations:

    $ {command} docker.pkg.dev/my-project/my-repository

  To list all tags in repository `my-repository` in `us-west1`:

    $ {command} us-west1-docker.pkg.dev/my-project/my-repository

  To list tags for image `busy-box` in `us-west1`:

    $ {command} us-west1-docker.pkg.dev/my-project/my-repository/busy-box
""",
  }

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(TAG_LIST_FORMAT)
    base.URI_FLAG.RemoveFromParser(parser)
    flags.GetImagePathOptionalArg().AddToParser(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      A list of Docker tags, sorted by Docker image name.
    """
    return docker_util.ListDockerTags(args)
