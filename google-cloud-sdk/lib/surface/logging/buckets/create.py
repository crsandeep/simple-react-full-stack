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

"""'logging buckets create' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Creates a bucket.
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument(
        'BUCKET_ID', help='ID of the bucket to create.')
    parser.add_argument(
        '--description',
        help='A textual description for the bucket.')
    parser.add_argument(
        '--retention-days', type=int,
        help='The period logs will be retained, after which logs will '
        'automatically be deleted. The default is 30 days.')
    util.AddBucketLocationArg(
        parser, True,
        'Location in which to create the bucket. Once the bucket is created, '
        'the location cannot be changed.')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The created bucket.
    """
    bucket_data = {}
    if args.IsSpecified('retention_days'):
      bucket_data['retentionDays'] = args.retention_days
    if args.IsSpecified('description'):
      bucket_data['description'] = args.description

    return util.GetClient().projects_locations_buckets.Create(
        util.GetMessages().LoggingProjectsLocationsBucketsCreateRequest(
            bucketId=args.BUCKET_ID,
            parent=util.CreateResourceName(
                util.GetProjectResource(args.project).RelativeName(),
                'locations',
                args.location),
            logBucket=util.GetMessages().LogBucket(**bucket_data)))
