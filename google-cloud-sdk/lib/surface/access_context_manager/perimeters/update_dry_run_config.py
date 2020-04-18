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
"""`gcloud access-context-manager perimeters update-dry-run-config` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.accesscontextmanager import zones as zones_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.accesscontextmanager import perimeters
from googlecloudsdk.command_lib.accesscontextmanager import policies
from googlecloudsdk.command_lib.util.args import repeated


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.Deprecate(
    is_removed=False,
    warning=('This command is deprecated. Please use '
             '`gcloud beta access-context-manager perimeters dry-run` to '
             'manage dry-run state.'))
class UpdatePerimetersAlpha(base.UpdateCommand):
  """Update the dry-run config for an existing Service Perimeter.

  {command} updates the dry run config (`spec`) on the service perimeter
  resource. The dry run config will not be enforced, but will be dry run. This
  allows for testing the config before rolling it out.

  Note: The `dry_run` field will be set to `true` unless the `--clear` flag is
  specified, in which case all dry run config values will be removed.

  For more information, see:
  https://cloud.google.com/access-context-manager/docs/reference/rest/v1alpha/accessPolicies.servicePerimeters
  """
  _INCLUDE_UNRESTRICTED = False
  _API_VERSION = 'v1alpha'

  @staticmethod
  def Args(parser):
    perimeters.AddResourceArg(parser, 'to update')
    perimeters.AddPerimeterUpdateDryRunConfigArgs(parser)

  def Run(self, args):
    client = zones_api.Client(version=self._API_VERSION)
    perimeter_ref = args.CONCEPTS.perimeter.Parse()
    result = repeated.CachedResult.FromFunc(client.Get, perimeter_ref)
    policies.ValidateAccessPolicyArg(perimeter_ref, args)
    return self.Patch(
        client=client, args=args, result=result, perimeter_ref=perimeter_ref)

  def Patch(self, client, args, perimeter_ref, result):
    if args.clear:
      return client.UnsetSpec(perimeter_ref, use_explicit_dry_run_spec=False)

    resources = perimeters.ParseResources(args, result, dry_run=True)
    restricted_services = perimeters.ParseRestrictedServices(
        args, result, dry_run=True)
    levels = perimeters.ParseLevels(
        args, result, perimeter_ref.accessPoliciesId, dry_run=True)
    vpc_allowed_services = perimeters.ParseVpcRestriction(
        args, result, self._API_VERSION, dry_run=True)
    enable_vpc_accessible_services = args.enable_vpc_accessible_services

    return client.PatchDryRunConfig(
        perimeter_ref,
        resources=resources,
        restricted_services=restricted_services,
        levels=levels,
        vpc_allowed_services=vpc_allowed_services,
        enable_vpc_accessible_services=enable_vpc_accessible_services)
