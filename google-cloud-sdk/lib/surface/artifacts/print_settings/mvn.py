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
"""Print a snippet to add a Maven repository to the pom.xml file."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.artifacts import flags
from googlecloudsdk.command_lib.artifacts import settings_util
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Maven(base.Command):
  """Print a snippet to add a Maven repository to the pom.xml file."""

  detailed_help = {
      "DESCRIPTION":
          "{description}",
      "EXAMPLES":
          """\
    To print a snippet for the repository set in the `artifacts/repository`
    property in the default location:

      $ {command}

    To print a snippet for repository `my-repository` in the default location:

      $ {command} --repository="my-repository"
    """,
  }

  @staticmethod
  def Args(parser):
    flags.GetRepoFlag().AddToParser(parser)
    parser.display_info.AddFormat("value(mvn)")

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      A maven pom snippet.
    """

    log.status.Print("Note: Language package support is in Alpha.\n")
    return {"mvn": settings_util.GetMavenSnippet(args)}

