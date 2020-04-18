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
"""Delete an Artifact Registry container image."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.artifacts import docker_util
from googlecloudsdk.command_lib.artifacts import flags
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Delete(base.Command):
  """Delete an Artifact Registry container image.

  A valid container image has the format of

    LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY-ID/IMAGE

  A valid container image that can be referenced by tag or digest, has the
  format of

    LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY-ID/IMAGE:tag
    LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY-ID/IMAGE@sha256:digest

  This command can fail for the following reasons:
    * Trying to delete an image by digest when the image is still tagged. Add
    --delete-tags to delete the digest and the tags.
    * Trying to delete an image by tag when the image has other tags. Add
    --delete-tags to delete all tags.
    * A valid repository format was not provided.
    * The specified image does not exist.
    * The active account does not have permission to delete images.
  """

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
    To delete image `busy-box` in `us-west1` and all of its digests and tags:

        $ {command} us-west1-docker.pkg.dev/my-project/my-repository/busy-box

    To delete image digest `abcxyz` under image `busy-box`:

        $ {command} us-west1-docker.pkg.dev/my-project/my-repository/busy-box@sha256:abcxyz

    To delete image digest `abcxyz` under image `busy-box` while there're other tags associate with the digest:

        $ {command} us-west1-docker.pkg.dev/my-project/my-repository/busy-box@sha256:abcxyz --delete-tags

    To delete an image digest and its only tag `my-tag` under image `busy-box`:

        $ {command} us-west1-docker.pkg.dev/my-project/my-repository/busy-box:my-tag
    """,
  }

  @staticmethod
  def Args(parser):
    base.ASYNC_FLAG.AddToParser(parser)
    flags.GetDeleteTagsFlag().AddToParser(parser)
    flags.GetImageRequiredArg().AddToParser(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      DeleteVersion operation.
    """
    op = docker_util.DeleteDockerImage(args)
    if args.async_:
      log.status.Print(
          'Delete request issued.\nCheck operation [{}] for status.'.format(
              op.name))
    else:
      log.status.Print('Delete request issued.')
      docker_util.WaitForOperation(
          op, 'Waiting for operation [{}] to complete'.format(op.name))
