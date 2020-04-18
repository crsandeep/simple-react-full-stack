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
"""List Artifact Registry container images."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.artifacts import docker_util
from googlecloudsdk.command_lib.artifacts import flags

DEFAULT_LIST_FORMAT = """\
    table(
      package:label=IMAGE,
      version.basename():label=DIGEST,
      createTime.date(tz=LOCAL),
      updateTime.date(tz=LOCAL)
    )"""

EXTENDED_LIST_FORMAT = """\
    table(
      package:label=IMAGE,
      version.basename():label=DIGEST,
      tags,
      createTime.date(tz=LOCAL),
      updateTime.date(tz=LOCAL)
    )"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class List(base.ListCommand):
  """List Artifact Registry container images.

  List all Artifact Registry container images in the specified repository or
  image path.

  A valid Docker repository has the format of
  LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY-ID

  A valid image has the format of
  LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY-ID/IMAGE_PATH

  Without location in input path, all images across all locations under all
  matched projects and repositories are listed.

  To specify the maximum number of images to list, use the --limit flag.
  """

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
      To list images under the current project, repository, and location:

          $ {command}

      To list images with tags under the current project, repository, and location:

          $ {command} --include-tags

      To list images under repository `my-repo`, project `my-project`, in `us-central1`:

          $ {command} us-central1-docker.pkg.dev/my-project/my-repo

      To list images under repository `my-repo`, project `my-project` across all locations:

          $ {command} docker.pkg.dev/my-project/my-repo

      To list all image digests under image `busy-box`, in repository `my-repo`, project `my-project` across all locations:

          $ {command} docker.pkg.dev/my-project/my-repo/busy-box

      The following command lists a maximum of five images:

          $ {command} docker.pkg.dev/my-project/my-repo --limit=5
      """,
  }

  @staticmethod
  def Args(parser):
    flags.GetIncludeTagsFlag().AddToParser(parser)
    base.URI_FLAG.RemoveFromParser(parser)
    flags.GetImagePathOptionalArg().AddToParser(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      A list of Docker images.
    """
    if args.include_tags:
      args.GetDisplayInfo().AddFormat(EXTENDED_LIST_FORMAT)
    else:
      args.GetDisplayInfo().AddFormat(DEFAULT_LIST_FORMAT)
    return docker_util.GetDockerImages(args)
