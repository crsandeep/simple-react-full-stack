# -*- coding: utf-8 -*- #
# Copyright 2020 Google Inc. All Rights Reserved.
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
"""services api-keys list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.services import apikeys
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


def _GetUriFunction(resource):
  return resources.REGISTRY.ParseRelativeName(
      resource.name, collection='apikeys.projects.keys').SelfLink()


class List(base.ListCommand):
  """Lists API keys.

  Lists all of the API keys that are active in a given project.
  You can add the state filter `state:DELETED` to list api keys that were
  deleted within past 30 days.

  ## EXAMPLES

   List active keys:

    $ {command}

   List keys that were deleted in past 30 days of a given project.:

    $ {command} --deleted --project=my_project
  """

  @staticmethod
  def Args(parser):

    parser.add_argument(
        '--deleted',
        action='store_true',
        help=('Return the keys that were deleted in past 30 days'))

    parser.display_info.AddFormat("""
          table(
            name:label=NAME,
            displayName:label=DISPLAY_NAME,
            updateTime:label=LAST_UPDATE:sort=1:reverse
          )
        """)
    parser.display_info.AddUriFunc(_GetUriFunction)

  def Run(self, args):
    """Run command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The list of api keys.
    """

    project_id = properties.VALUES.core.project.GetOrFail()
    return apikeys.ListKeys(project_id, args.deleted, args.page_size,
                            args.limit)
