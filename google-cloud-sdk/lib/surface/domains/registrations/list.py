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
"""`gcloud domains registrations list` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from googlecloudsdk.api_lib.domains import registrations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.domains import resource_args
from googlecloudsdk.command_lib.domains import util

_FORMAT = """\
table(
    name.scope("registrations"):label=DOMAIN,
    state:label=STATE,
    expireTime:label=EXPIRE_TIME
)
"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List Cloud Domains registrations.

  List Cloud Domains registrations in the project.

  ## EXAMPLES

  To list all registrations in the project, run:

    $ {command}
  """

  @staticmethod
  def Args(parser):
    resource_args.AddLocationResourceArg(parser, 'to list registrations for')
    parser.display_info.AddFormat(_FORMAT)
    parser.display_info.AddUriFunc(util.RegistrationsUriFunc)

  def Run(self, args):
    """Run the list command."""
    client = registrations.RegistrationsClient()

    location_ref = args.CONCEPTS.location.Parse()

    # TODO(b/110077203): Add server-side filtering.
    return client.List(location_ref, args.limit, args.page_size)
