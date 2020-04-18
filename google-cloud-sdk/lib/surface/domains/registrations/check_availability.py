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
"""`gcloud domains registrations check-availability` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.domains import registrations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.domains import resource_args


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CheckAvailability(base.DescribeCommand):
  """Check availability of a specific domain.

  This command checks availability of a single domain and provides additional
  information such as pricing, supported WHOIS privacy modes & notices.

  ## EXAMPLES

  To check if example.com is available for registration, run:

    $ {command} example.com
  """

  @staticmethod
  def Args(parser):
    resource_args.AddLocationResourceArg(parser)
    base.Argument(
        'domain',
        help='Domain to check availability for.',
    ).AddToParser(parser)

  def Run(self, args):
    """Run the check availability command."""
    client = registrations.RegistrationsClient()

    location_ref = args.CONCEPTS.location.Parse()

    return client.CheckAvailability(location_ref, args.domain).availability
