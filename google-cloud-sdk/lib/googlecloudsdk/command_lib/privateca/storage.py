# Lint as: python3
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
"""Helpers for dealing with storage buckets."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import uuid

from googlecloudsdk.api_lib.storage import storage_util

_BUCKET_NAMING_PATTERN = 'privateca_content_{uuid}'


def CreateBucketForCertificateAuthority(ca_ref):
  """Creates a GCS bucket for use by the given Certificate Authority."""
  client = storage_util.GetClient()
  messages = storage_util.GetMessages()

  location = ca_ref.Parent().Name()
  project = ca_ref.Parent().Parent().Name()
  bucket_name = _BUCKET_NAMING_PATTERN.format(uuid=uuid.uuid4())

  client.buckets.Insert(
      messages.StorageBucketsInsertRequest(
          project=project,
          bucket=messages.Bucket(
              name=bucket_name,
              location=location,
              versioning=messages.Bucket.VersioningValue(enabled=True))))

  return storage_util.BucketReference(bucket_name)
