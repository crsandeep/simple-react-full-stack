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
"""`gcloud access-context-manager perimeters dry-run describe` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.accesscontextmanager import zones as zones_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.accesscontextmanager import perimeters
from googlecloudsdk.command_lib.accesscontextmanager import policies


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DescribePerimeterDryRunBeta(base.DescribeCommand):
  """Displays the dry-run mode configuration for a Service Perimeter."""
  _API_VERSION = 'v1'

  @staticmethod
  def Args(parser):
    perimeters.AddResourceArg(parser, 'to describe')

  def Run(self, args):
    client = zones_api.Client(version=self._API_VERSION)
    perimeter_ref = args.CONCEPTS.perimeter.Parse()
    policies.ValidateAccessPolicyArg(perimeter_ref, args)
    perimeter = client.Get(perimeter_ref)
    print(perimeters.GenerateDryRunConfigDiff(perimeter, self._API_VERSION))


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DescribePerimeterDryRunAlpha(DescribePerimeterDryRunBeta):
  """Displays the dry-run mode configuration for a Service Perimeter."""
  _API_VERSION = 'v1alpha'


detailed_help = {
    'brief':
        'Display the dry-run mode configuration for a Service Perimeter.',
    'DESCRIPTION':
        ('The dry-run mode configuration is presented as a diff against the '
         'enforcement mode configuration. \'+\' indicates additions, \'-\' '
         'indicates removals and entries without either of those indicate that '
         'they are the same across the dry-run and the enforcement mode '
         'configurations. When a particular field is completely empty, it is '
         'displayed as \'NONE\'.\n\nNote: When this command is executed on a '
         'Service Perimeter with no explicit dry-run mode configuration, the '
         'effective dry-run mode configuration is inherited from the '
         'enforcement mode configuration, and thus, the enforcement mode '
         'configuration is displayed in such cases.'),
    'EXAMPLES': (
        'To display the dry-run mode configuration for a Service Perimeter:\n\n'
        '  $ {command} my-perimeter\n\n'
        'Sample output:\n\n'
        '  name: my_perimeter\n'
        '  title: My Perimeter\n'
        '  type: PERIMETER_TYPE_REGULAR\n'
        '  resources:\n'
        '     +projects/123\n'
        '     -projects/456\n'
        '      projects/789\n'
        '  restrictedServices:\n'
        '    +bigquery.googleapis.com\n'
        '    -storage.googleapis.com\n'
        '     bigtable.googleapis.com\n'
        '  accessLevels:\n'
        '     NONE\n'
        '  vpcAccessibleServices:\n'
        '    enableRestriction: False -> True\n'
        '    allowedServices:\n'
        '      +bigquery.googleapis.com\n'
        '      -storage.googleapis.com\n')
}

DescribePerimeterDryRunAlpha.detailed_help = detailed_help
DescribePerimeterDryRunBeta.detailed_help = detailed_help
