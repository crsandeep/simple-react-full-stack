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
"""List Artifact Registry and Container Registry repositories."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.artifacts import flags
from googlecloudsdk.command_lib.artifacts import util
from googlecloudsdk.core import log

DEFAULT_LIST_FORMAT = """\
    multi[separator='\n'](
      AR:format="table[title="ARTIFACT_REGISTRY"](
         name.basename():label=REPOSITORY,
         format:label=FORMAT,
         description:label=DESCRIPTION,
         name.segment(3):label=LOCATION,
         createTime.date(tz=LOCAL),
         updateTime.date(tz=LOCAL))",

      GCR:format="table[title="CONTAINER_REGISTRY"](
         name.basename():label=REPOSITORY,
         format:label=FORMAT,
         name.segment(3):label=LOCATION
      )"
    )"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class List(base.ListCommand):
  """List repositories in the specified project.

  List all Artifact Registry and Container Registry repositories in the
  specified project.

  To perform actions on the Container Registry repositories, use `gcloud
  container images`.

  To specify the maximum number of repositories to list, use the --limit flag.
  """

  detailed_help = {
      "DESCRIPTION":
          "{description}",
      "EXAMPLES":
          """\
    The following command lists a maximum of five repositories:

        $ {command} --limit=5
    """,
  }

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(DEFAULT_LIST_FORMAT)
    base.URI_FLAG.RemoveFromParser(parser)
    flags.GetOptionalLocationFlag().AddToParser(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      A list of Docker images.
    """
    repos, buckets, project = util.ListRepositories(args)
    gcr_repos = util.GetGCRRepos(buckets, project)
    if gcr_repos:
      log.status.Print(
          "Note: To perform actions on the Container Registry repositories "
          "listed below please use 'gcloud container images'.\n")
    return {"AR": repos, "GCR": gcr_repos}
