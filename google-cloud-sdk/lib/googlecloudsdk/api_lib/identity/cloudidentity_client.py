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
"""Useful commands for interacting with the Cloud Identity Groups API."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core.credentials import http

from six.moves import urllib

API_NAME = 'cloudidentity'


def GetClient(version):
  """Import and return the appropriate Cloud Identity Groups client.

  Args:
    version: str, the version of the API desired

  Returns:
    Cloud Identity Groups client for the appropriate release track
  """
  return apis.GetClientInstance(API_NAME, version)


def GetMessages(version):
  """Import and return the appropriate Cloud Identity Groups messages module.

  Args:
    version: str, the version of the API desired

  Returns:
    Cloud Identity Groups messages for the appropriate release track
  """
  return apis.GetMessagesModule(API_NAME, version)


def LookupGroupName(version, email):
  """Lookup Group Name for a specified group key id.

  Args:
    version: Release track information
    email: str, group email

  Returns:
    LookupGroupNameResponse: Response message for LookupGroupName operation
    which is containing a resource name of the group in the format:
    'name: groups/{group_id}'
  """

  client = GetClient(version)

  # Following part is added to resolve the gcloud known issue described
  # in this bug: b/141658179
  query_params = [('groupKey.id', email)]
  base_url = client.url
  url = '{}{}/groups:lookup?{}'.format(
      base_url, version, urllib.parse.urlencode(query_params))
  unused_response, raw_content = http.Http().request(uri=url)

  return json.loads(raw_content.decode('utf8'))


def LookupMembershipName(version, group_id, member_email):
  """Lookup membership name for a specific pair of member key id and group email.

  Args:
    version: Release track information
    group_id: str, group id (e.g. groups/03qco8b4452k99t)
    member_email: str, member email
  Returns:
    LookupMembershipNameResponse: Response message for LookupMembershipName
    operation which is containing a resource name of the membership in the
    format:
    'name: members/{member_id}'
  """

  client = GetClient(version)

  # Following part is added to resolve the gcloud known issue described
  # in this bug: b/141658179
  query_params = [('parent', group_id), ('memberKey.id', member_email)]
  base_url = client.url
  url = '{}{}/{}/memberships:lookup?{}'.format(
      base_url, version, group_id, urllib.parse.urlencode(query_params))
  unused_response, raw_content = http.Http().request(uri=url)

  return json.loads(raw_content.decode('utf8'))
