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
"""Command to analyze IAM policy in the specified root asset."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.asset import client_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.asset import utils as asset_utils
from googlecloudsdk.core import log

OPERATION_DESCRIBE_COMMAND = 'gcloud asset operations describe'


def AddOrganizationArgs(parser, required=True):
  parser.add_argument(
      '--organization',
      metavar='ORGANIZATION_ID',
      required=required,
      help='The organization ID to perform the analysis.')


def AddFolderArgs(parser):
  parser.add_argument(
      '--folder',
      metavar='FOLDER_ID',
      help='The folder ID to perform the analysis.')


def AddParentArgs(parser):
  parent_group = parser.add_mutually_exclusive_group(required=True)
  AddOrganizationArgs(parent_group, required=False)
  AddFolderArgs(parent_group)


def AddResourceSelectorGroup(parser):
  resource_selector_group = parser.add_group(
      mutex=False,
      required=False,
      help='Specifies a resource for analysis. Leaving it empty means ANY.')
  AddFullResourceNameArgs(resource_selector_group)


def AddFullResourceNameArgs(parser):
  parser.add_argument('--full-resource-name', help='The full resource name.')


def AddIdentitySelectorGroup(parser):
  identity_selector_group = parser.add_group(
      mutex=False,
      required=False,
      help='Specifies an identity for analysis. Leaving it empty means ANY.')
  AddIdentityArgs(identity_selector_group)


def AddIdentityArgs(parser):
  parser.add_argument(
      '--identity',
      help=('The identity appearing in the form of members in the IAM policy '
            'binding.'))


def AddAccessSelectorGroup(parser):
  access_selector_group = parser.add_group(
      mutex=False,
      required=False,
      help=('Specifies roles or permissions for analysis. Leaving it empty '
            'means ANY.'))
  AddRolesArgs(access_selector_group)
  AddPermissionsArgs(access_selector_group)


def AddRolesArgs(parser):
  parser.add_argument(
      '--roles',
      metavar='ROLES',
      type=arg_parsers.ArgList(),
      help='The roles to appear in the result.')


def AddPermissionsArgs(parser):
  parser.add_argument(
      '--permissions',
      metavar='PERMISSIONS',
      type=arg_parsers.ArgList(),
      help='The permissions to appear in the result.')


def AddOptionsGroup(parser):
  """Adds a group of options."""
  options_group = parser.add_group(
      mutex=False, required=False, help='The analysis options.')
  AddExpandGroupsArgs(options_group)
  AddExpandRolesArgs(options_group)
  AddExpandResourcesArgs(options_group)
  AddOutputResourceEdgesArgs(options_group)
  AddOutputGroupEdgesArgs(options_group)


def AddExpandGroupsArgs(parser):
  parser.add_argument(
      '--expand-groups',
      action='store_true',
      help=(
          'If true, the identities section of the result will expand any '
          'Google groups appearing in an IAM policy binding. Default is false.'
      ))
  parser.set_defaults(expand_groups=False)


def AddExpandRolesArgs(parser):
  parser.add_argument(
      '--expand-roles',
      action='store_true',
      help=('If true, the access section of result will expand any roles '
            'appearing in IAM policy bindings to include their permissions. '
            'Default is false.'))
  parser.set_defaults(expand_roles=False)


def AddExpandResourcesArgs(parser):
  parser.add_argument(
      '--expand-resources',
      action='store_true',
      help=('If true, the resource section of the result will expand any '
            'resource attached to an IAM policy to include resources lower in '
            'the resource hierarchy. Default is false.'))
  parser.set_defaults(expand_resources=False)


def AddOutputResourceEdgesArgs(parser):
  parser.add_argument(
      '--output-resource-edges',
      action='store_true',
      help=('If true, the result will output resource edges, starting '
            'from the policy attached resource, to any expanded resources. '
            'Default is false.'))
  parser.set_defaults(output_resource_edges=False)


def AddOutputGroupEdgesArgs(parser):
  parser.add_argument(
      '--output-group-edges',
      action='store_true',
      help=('If true, the result will output group identity edges, starting '
            "from the binding's group members, to any expanded identities. "
            'Default is false.'))
  parser.set_defaults(output_group_edges=False)


def AddOutputPartialResultBeforeTimeoutArgs(parser):
  parser.add_argument(
      '--output-partial-result-before-timeout',
      action='store_true',
      help=(
          'If true, you will get a response with a partial result instead of '
          'a DEADLINE_EXCEEDED error when your request processing takes longer '
          'than the deadline. Default is false.'))
  parser.set_defaults(output_partial_result_before_timeout=False)


def AddDestinationArgs(parser):
  destination_group = parser.add_group(
      mutex=True,
      required=True,
      help='The destination path for exporting IAM policy analysis.')
  AddOutputPathArgs(destination_group)


def AddOutputPathArgs(parser):
  parser.add_argument(
      '--output-path',
      metavar='OUTPUT_PATH',
      required=True,
      type=arg_parsers.RegexpValidator(
          r'^gs://.*',
          '--output-path must be a Google Cloud Storage URI starting with '
          '"gs://". For example, "gs://bucket_name/object_name"'),
      help='Google Cloud Storage URI where the results will go. '
      'URI must start with "gs://". For example, "gs://bucket_name/object_name"'
  )


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ExportIamPolicyAnalysisBeta(base.Command):
  """Export IAM policy analysis that match a request to Google Cloud Storage."""

  detailed_help = {
      'DESCRIPTION':
          """\
      Export IAM policy analysis that matches a request to Google Cloud Storage.
      """,
      'EXAMPLES':
          """\
          To find out which users have been granted the
          iam.serviceAccounts.actAs permission on a service account, run:

            $ {command} --organization=YOUR_ORG_ID --full-resource-name=YOUR_SERVICE_ACCOUNT_FULL_RESOURCE_NAME --permissions='iam.serviceAccounts.actAs' --output-path='gs://YOUR_BUCKET_NAME/YOUR_OBJECT_NAME'

          To find out which resources a user can access, run:

            $ {command} --organization=YOUR_ORG_ID --identity='user:u1@foo.com' --output-path='gs://YOUR_BUCKET_NAME/YOUR_OBJECT_NAME'

          To find out which roles or permissions a user has been granted on a
          project, run:

            $ {command} --organization=YOUR_ORG_ID --full-resource-name=YOUR_PROJECT_FULL_RESOURCE_NAME --identity='user:u1@foo.com' --output-path='gs://YOUR_BUCKET_NAME/YOUR_OBJECT_NAME'
      """
  }

  @staticmethod
  def Args(parser):
    AddParentArgs(parser)
    AddResourceSelectorGroup(parser)
    AddIdentitySelectorGroup(parser)
    AddAccessSelectorGroup(parser)
    AddDestinationArgs(parser)
    AddOptionsGroup(parser)

  def Run(self, args):
    parent = asset_utils.GetParentNameForAnalyzeIamPolicy(
        args.organization, args.folder)
    client = client_util.IamPolicyAnalysisExportClient(parent)
    operation = client.Export(args)

    log.ExportResource(parent, is_async=True, kind='root asset')
    log.status.Print('Use [{} {}] to check the status of the operation.'.format(
        OPERATION_DESCRIBE_COMMAND, operation.name))
