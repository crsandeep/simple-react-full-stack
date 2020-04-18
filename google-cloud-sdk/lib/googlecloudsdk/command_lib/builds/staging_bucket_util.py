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
"""Support library to handle the staging bucket."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties


def GetDefaultStagingBucket():
  """Returns the default bucket stage files.

  Returns:
    GCS bucket name.
  """
  safe_project = (properties.VALUES.core.project.Get(required=True)
                  .replace(':', '_')
                  .replace('.', '_')
                  # The string 'google' is not allowed in bucket names.
                  .replace('google', 'elgoog'))

  return safe_project + '_cloudbuild'


def BucketIsInProject(gcs_client, bucket_name):
  """Returns true if the provided bucket is in the user's project, else False.

  Args:
    gcs_client: Client used to make calls to GCS.
    bucket_name: Bucket name to check.

  Returns:
    True or False.
  """
  project = properties.VALUES.core.project.Get(required=True)
  bucket_list_req = gcs_client.messages.StorageBucketsListRequest(
      project=project, prefix=bucket_name)
  bucket_list = gcs_client.client.buckets.List(bucket_list_req)
  return any(
      bucket.id == bucket_name for bucket in bucket_list.items)
