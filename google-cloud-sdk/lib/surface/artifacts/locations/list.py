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
"""List Artifact Registry resource locations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.artifacts import util


DEFAULT_LIST_FORMAT = """\
    table(
      name:label=LOCATIONS
    )"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class List(base.ListCommand):
  """List all Artifact Registry supported locations."""

  detailed_help = {
      "DESCRIPTION":
          "{description}",
      "EXAMPLES":
          """\
    To list all supported locations:

        $ {command}
    """,
  }

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(DEFAULT_LIST_FORMAT)
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided
        to this command invocation.

    Returns:
      A list of all supported locations.
    """

    return [{"name": loc} for loc in util.GetLocationList(args)]
