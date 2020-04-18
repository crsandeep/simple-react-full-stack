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
"""`gcloud access-context-manager perimeters dry-run update` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.accesscontextmanager import util
from googlecloudsdk.api_lib.accesscontextmanager import zones as zones_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.accesscontextmanager import perimeters
from googlecloudsdk.command_lib.accesscontextmanager import policies
from googlecloudsdk.command_lib.util.args import repeated


def _GetBaseConfig(perimeter):
  """Returns the base config to use for the update operation."""
  if perimeter.useExplicitDryRunSpec:
    return perimeter.spec
  return perimeter.status


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdatePerimeterDryRunBeta(base.UpdateCommand):
  """Updates the dry-run mode configuration for a Service Perimeter."""
  _API_VERSION = 'v1'

  @staticmethod
  def Args(parser):
    perimeters.AddResourceArg(parser, 'to update')
    repeated.AddPrimitiveArgs(
        parser,
        'Service Perimeter',
        'resources',
        'Resources',
        include_set=False)
    repeated.AddPrimitiveArgs(
        parser,
        'Service Perimeter',
        'restricted-services',
        'Restricted Services',
        include_set=False)
    repeated.AddPrimitiveArgs(
        parser,
        'Service Perimeter',
        'access-levels',
        'Access Level',
        include_set=False)
    vpc_group = parser.add_argument_group(
        'Arguments for configuring VPC accessible service restrictions.')
    vpc_group.add_argument(
        '--enable-vpc-accessible-services',
        action='store_true',
        help="""When specified restrict API calls within the Service Perimeter to the
        set of vpc allowed services. To disable use
        '--no-enable-vpc-accessible-services'.""")
    repeated.AddPrimitiveArgs(
        vpc_group,
        'Service Perimeter',
        'vpc-allowed-services',
        'VPC Allowed Services',
        include_set=False)
    parser.add_argument(
        '--async',
        action='store_true',
        help="""Return immediately, without waiting for the operation in
                progress to complete.""")

  def Run(self, args):
    client = zones_api.Client(version=self._API_VERSION)
    messages = util.GetMessages(version=self._API_VERSION)
    perimeter_ref = args.CONCEPTS.perimeter.Parse()
    policies.ValidateAccessPolicyArg(perimeter_ref, args)
    original_perimeter = client.Get(perimeter_ref)
    base_config = _GetBaseConfig(original_perimeter)
    updated_resources = repeated.ParsePrimitiveArgs(
        args, 'resources', lambda: base_config.resources or [])
    updated_restricted_services = repeated.ParsePrimitiveArgs(
        args, 'restricted-services',
        lambda: base_config.restrictedServices or [])
    updated_access_levels = repeated.ParsePrimitiveArgs(
        args, 'access-levels', lambda: base_config.accessLevels or [])
    base_vpc_config = base_config.vpcAccessibleServices
    if base_vpc_config is None:
      base_vpc_config = messages.VpcAccessibleServices()
    updated_vpc_services = repeated.ParsePrimitiveArgs(
        args, 'vpc-allowed-services',
        lambda: base_vpc_config.allowedServices or [])
    if args.IsSpecified('enable_vpc_accessible_services'):
      updated_vpc_enabled = args.enable_vpc_accessible_services
    elif base_config.vpcAccessibleServices is not None:
      updated_vpc_enabled = base_vpc_config.enableRestriction
    else:
      updated_vpc_enabled = None
    return client.PatchDryRunConfig(
        perimeter_ref,
        resources=updated_resources,
        levels=updated_access_levels,
        restricted_services=updated_restricted_services,
        vpc_allowed_services=updated_vpc_services,
        enable_vpc_accessible_services=updated_vpc_enabled)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdatePerimeterDryRunAlpha(UpdatePerimeterDryRunBeta):
  """Updates the dry-run mode configuration for a Service Perimeter."""
  _API_VERSION = 'v1alpha'


detailed_help = {
    'brief':
        'Update the dry-run mode configuration for a Service Perimeter.',
    'DESCRIPTION':
        ('This command updates the dry-run mode configuration (`spec`) for a '
         'Service Perimeter.\n\nFor Service Perimeters with an explicitly '
         'defined dry-run mode configuration (i.e. an explicit `spec`), this '
         'operation updates that configuration directly, ignoring enforcement '
         'mode configuration.\n\nService Perimeters that do not have explict '
         'dry-run mode configuration will inherit the enforcement mode '
         'configuration in the dry-run mode. Therefore, this command '
         'effectively clones the enforcement mode configuration, then applies '
         'the update on that configuration, and uses that as the explicit '
         'dry-run mode configuration.'),
    'EXAMPLES':
        ('To update the dry-run mode configuration for a Service Perimeter:\n\n'
         '  $ {command} my-perimeter '
         '--add-resources="projects/123,projects/456" '
         '--remove-restricted-services="storage.googleapis.com" '
         '--add-access-levels="accessPolicies/123/accessLevels/a_level" '
         '--enable-vpc-accessible-services '
         '--clear-vpc-allowed-services')
}

UpdatePerimeterDryRunAlpha.detailed_help = detailed_help
UpdatePerimeterDryRunBeta.detailed_help = detailed_help
