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
"""Command for compute reservations create."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.reservations import flags
from googlecloudsdk.command_lib.compute.reservations import resource_args
from googlecloudsdk.command_lib.compute.reservations import util


def _MakeCreateRequest(args, messages, project, reservation_ref):
  """Common routine for creating reservation request."""
  reservation = util.MakeReservationMessageFromArgs(messages, args,
                                                    reservation_ref)
  reservation.description = args.description
  return messages.ComputeReservationsInsertRequest(
      reservation=reservation, project=project, zone=reservation_ref.zone)


def _RunCreate(compute_api, args):
  """Common routine for creating reservation."""
  resources = compute_api.resources
  reservation_ref = resource_args.GetReservationResourceArg().ResolveAsResource(
      args,
      resources,
      scope_lister=compute_flags.GetDefaultScopeLister(compute_api.client))

  messages = compute_api.client.messages
  project = reservation_ref.project
  create_request = _MakeCreateRequest(args, messages, project, reservation_ref)

  service = compute_api.client.apitools_client.reservations
  return compute_api.client.MakeRequests([(service, 'Insert', create_request)])


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a Compute Engine reservation."""
  _support_location_hint = False

  @classmethod
  def Args(cls, parser):
    resource_args.GetReservationResourceArg().AddArgument(
        parser, operation_type='create')
    flags.AddCreateFlags(
        parser, support_location_hint=cls._support_location_hint)

  def Run(self, args):
    return _RunCreate(base_classes.ComputeApiHolder(base.ReleaseTrack.GA), args)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create a Compute Engine reservation."""
  _support_location_hint = False

  @classmethod
  def Args(cls, parser):
    resource_args.GetReservationResourceArg().AddArgument(
        parser, operation_type='create')
    flags.AddCreateFlags(
        parser, support_location_hint=cls._support_location_hint)

  def Run(self, args):
    return _RunCreate(
        base_classes.ComputeApiHolder(base.ReleaseTrack.BETA), args)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(CreateBeta):
  """Create a Compute Engine reservation."""
  _support_location_hint = True

  @classmethod
  def Args(cls, parser):
    resource_args.GetReservationResourceArg().AddArgument(
        parser, operation_type='create')
    flags.AddCreateFlags(
        parser, support_location_hint=cls._support_location_hint)

  def Run(self, args):
    return _RunCreate(
        base_classes.ComputeApiHolder(base.ReleaseTrack.ALPHA), args)


Create.detailed_help = {
    'brief':
        'Create a Compute Engine reservation.',
    'EXAMPLES':
        """
        To create a Compute Engine reservation, run:

            $ {command} my-reservation --zone=fake-zone --vm-count=1 --machine-type=n1-standard-1 --min-cpu-platform="Intel Haswell"
        """
}
