# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Flags for commands in cloudasset."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util.apis import yaml_data
from googlecloudsdk.command_lib.util.args import common_args
from googlecloudsdk.command_lib.util.args import resource_args
from googlecloudsdk.command_lib.util.concepts import concept_parsers


def AddOrganizationArgs(parser, help_text):
  parser.add_argument(
      '--organization', metavar='ORGANIZATION_ID', help=help_text)


def AddFolderArgs(parser, help_text):
  parser.add_argument('--folder', metavar='FOLDER_ID', help=help_text)


def AddParentArgs(parser, project_help_text, org_help_text, folder_help_text):
  parent_group = parser.add_mutually_exclusive_group(required=True)
  common_args.ProjectArgument(
      help_text_to_prepend=project_help_text).AddToParser(parent_group)
  AddOrganizationArgs(parent_group, org_help_text)
  AddFolderArgs(parent_group, folder_help_text)


def AddSnapshotTimeArgs(parser):
  parser.add_argument(
      '--snapshot-time',
      type=arg_parsers.Datetime.Parse,
      help=('Timestamp to take a snapshot on assets. This can only be a '
            'current or past time. If not specified, the current time will be '
            'used. Due to delays in resource data collection and indexing, '
            'there is a volatile window during which running the same query at '
            'different times may return different results. '
            'See $ gcloud topic datetimes for information on time formats.'))


def AddAssetTypesArgs(parser):
  parser.add_argument(
      '--asset-types',
      metavar='ASSET_TYPES',
      type=arg_parsers.ArgList(),
      default=[],
      help=(
          'A list of asset types (i.e., "compute.googleapis.com/Disk") to take '
          'a snapshot. If specified and non-empty, only assets matching the '
          'specified types will be returned. '
          'See https://cloud.google.com/resource-manager/docs/'
          'cloud-asset-inventory/overview '
          'for supported asset types.'))


def AddContentTypeArgs(parser, required):
  """--content-type argument for asset export and get-history."""
  if required:
    help_text = (
        'Asset content type. Specifying `resource` will export resource '
        'metadata, specifying `iam-policy` will export the IAM policy for each '
        'child asset, specifying `org-policy` will export the Org Policy set on'
        ' child assets, and specifying `access-policy` will export the Access '
        'Policy set on child assets.')
  else:
    help_text = (
        'Asset content type. If specified, only content matching the '
        'specified type will be returned. Otherwise, no content but the '
        'asset name will be returned. Specifying `resource` will export '
        'resource metadata, specifying `iam-policy` will export the IAM policy '
        'for each child asset, specifying `org-policy` will export the Org '
        'Policy set on child assets, and specifying `access-policy` will '
        'export the Access Policy set on child assets.')

  parser.add_argument(
      '--content-type',
      required=required,
      choices=['resource', 'iam-policy', 'org-policy', 'access-policy'],
      help=help_text)


def AddOutputPathArgs(parser, required):
  parser.add_argument(
      '--output-path',
      metavar='OUTPUT_PATH',
      required=required,
      type=arg_parsers.RegexpValidator(
          r'^gs://.*',
          '--output-path must be a Google Cloud Storage URI starting with '
          '"gs://". For example, "gs://bucket_name/object_name"'),
      help='Google Cloud Storage URI where the results will go. '
      'URI must start with "gs://". For example, "gs://bucket_name/object_name"'
  )


def AddOutputPathPrefixArgs(parser):
  parser.add_argument(
      '--output-path-prefix',
      type=arg_parsers.RegexpValidator(
          r'^gs://.*/.*',
          '--output-path-prefix must be a Google Cloud Storage URI starting '
          'with "gs://". For example, "gs://bucket_name/object_name_prefix"'),
      help=(
          'Google Cloud Storage URI where the results will go. '
          'URI must start with "gs://". For example, '
          '"gs://bucket_name/object_name_prefix", in which case each exported '
          'object uri is in format: '
          '"gs://bucket_name/object_name_prefix/<asset type>/<shard number>" '
          'and it only contains assets for that type.'))


def AddOutputPathBigQueryArgs(parser):
  """Add BigQuery destination args to argument list."""
  bigquery_group = parser.add_group(
      mutex=False,
      required=False,
      help='The BigQuery destination for exporting assets.')
  resource = yaml_data.ResourceYAMLData.FromPath('bq.table')
  table_dic = resource.GetData()
  # Update the name 'dataset' in table_ref to 'bigquery-dataset'
  attributes = table_dic['attributes']
  for attr in attributes:
    if attr['attribute_name'] == 'dataset':
      attr['attribute_name'] = 'bigquery-dataset'
  arg_specs = [
      resource_args.GetResourcePresentationSpec(
          verb='export to',
          name='bigquery-table',
          required=True,
          prefixes=False,
          positional=False,
          resource_data=table_dic)
  ]
  concept_parsers.ConceptParser(arg_specs).AddToParser(bigquery_group)
  base.Argument(
      '--output-bigquery-force',
      action='store_true',
      dest='force_',
      default=False,
      required=False,
      help=(
          'If the destination table already exists and this flag is specified, '
          'the table will be overwritten by the contents of assets snapshot. '
          'If the flag is not specified and the destination table already exists, '
          'the export call returns an error.')).AddToParser(bigquery_group)


def AddDestinationArgs(parser):
  destination_group = parser.add_group(
      mutex=True,
      required=True,
      help='The destination path for exporting assets.')
  AddOutputPathArgs(destination_group, required=False)
  AddOutputPathPrefixArgs(destination_group)
  AddOutputPathBigQueryArgs(destination_group)


def AddAssetNamesArgs(parser):
  parser.add_argument(
      '--asset-names',
      metavar='ASSET_NAMES',
      required=True,
      type=arg_parsers.ArgList(),
      help=
      ('A list of full names of the assets to get the history for. See '
       'https://cloud.google.com/apis/design/resource_names#full_resource_name '
       'for name format.'))


def AddStartTimeArgs(parser):
  parser.add_argument(
      '--start-time',
      required=True,
      type=arg_parsers.Datetime.Parse,
      help=('Start time of the time window (inclusive) for the asset history. '
            'Must be later than 2018-10-02T00:00:00Z. '
            'See $ gcloud topic datetimes for information on time formats.'))


def AddEndTimeArgs(parser):
  parser.add_argument(
      '--end-time',
      required=False,
      type=arg_parsers.Datetime.Parse,
      help=('End time of the time window (exclusive) for the asset history. '
            'Defaults to current time if not specified. '
            'See $ gcloud topic datetimes for information on time formats.'))


def AddOperationArgs(parser):
  parser.add_argument(
      'id',
      metavar='OPERATION_NAME',
      help='Name of the operation to describe.')


def AddListContentTypeArgs(parser):
  help_text = (
      'Asset content type. If not specified, no content but the asset name and'
      ' type will be returned in the feed. To read more see '
      'https://cloud.google.com/resource-manager/docs/cloud-asset-inventory/overview#asset_content_type'
  )
  parser.add_argument('--content-type', choices=['resource'], help=help_text)


def AddFeedIdArgs(parser, help_text):
  parser.add_argument('feed', metavar='FEED_ID', help=help_text)


def AddFeedNameArgs(parser, help_text):
  parser.add_argument('name', help=help_text)


def AddFeedAssetTypesArgs(parser):
  parser.add_argument(
      '--asset-types',
      metavar='ASSET_TYPES',
      type=arg_parsers.ArgList(),
      default=[],
      help=(
          'A comma-separated list of types of the assets types to receive '
          'updates. For example: '
          '`compute.googleapis.com/Disk,compute.googleapis.com/Network` See '
          'https://cloud.google.com/resource-manager/docs/cloud-asset-inventory/overview'
          ' for all supported asset types.'))


def AddFeedAssetNamesArgs(parser):
  parser.add_argument(
      '--asset-names',
      metavar='ASSET_NAMES',
      type=arg_parsers.ArgList(),
      default=[],
      help=(
          'A comma-separated list of the full names of the assets to '
          'receive updates. For example: '
          '`//compute.googleapis.com/projects/my_project_123/zones/zone1/instances/instance1`.'
          ' See https://cloud.google.com/apis/design/resource_names#full_resource_name'
          ' for more information.'))


def AddFeedCriteriaArgs(parser):
  parent_group = parser.add_group(mutex=False, required=True)
  AddFeedAssetTypesArgs(parent_group)
  AddFeedAssetNamesArgs(parent_group)


def FeedContentTypeArgs(parser, help_text):
  parser.add_argument(
      '--content-type',
      choices=['resource', 'iam-policy', 'org-policy', 'access-policy'],
      help=help_text)


def AddFeedContentTypeArgs(parser):
  help_text = (
      'Asset content type. If not specified, no content but the asset name and'
      ' type will be returned in the feed. To read more see '
      'https://cloud.google.com/resource-manager/docs/cloud-asset-inventory/overview#asset_content_type'
  )

  FeedContentTypeArgs(parser, help_text)


def AddFeedPubSubTopicArgs(parser, required):
  parser.add_argument(
      '--pubsub-topic',
      metavar='PUBSUB_TOPIC',
      required=required,
      help=('Name of the Cloud Pub/Sub topic to publish to, of the form '
            '`projects/PROJECT_ID/topics/TOPIC_ID`. '
            'You can list existing topics with '
            '`gcloud pubsub topics list  --format="text(name)"`'))


def AddChangeFeedContentTypeArgs(parser):
  help_text = (
      'Asset content type to overwrite the existing one. To read more see: '
      'https://cloud.google.com/resource-manager/docs/cloud-asset-inventory/overview#asset_content_type'
  )

  FeedContentTypeArgs(parser, help_text)


def AddClearFeedContentTypeArgs(parser):
  parser.add_argument(
      '--clear-content-type',
      action='store_true',
      help=('Clear any existing content type setting on the feed. '
            'Content type will be unspecified, no content but'
            ' the asset name and type will be returned in the feed.'))


def AddUpdateFeedContentTypeArgs(parser):
  parent_group = parser.add_group(mutex=True)
  AddChangeFeedContentTypeArgs(parent_group)
  AddClearFeedContentTypeArgs(parent_group)
