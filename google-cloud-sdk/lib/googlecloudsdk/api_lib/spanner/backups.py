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
"""Cloud Spanner backups API helper."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import exceptions as c_exceptions
from googlecloudsdk.core.util import times


# General Utils
def ParseExpireTime(expiration_value):
  """Parse flag value into Datetime format for expireTime."""
  # expiration_value could be in Datetime format or Duration format.
  datetime = (
      times.ParseDuration(expiration_value).GetRelativeDateTime(
          times.Now(times.UTC)))
  parsed_datetime = times.FormatDateTime(
      datetime, '%Y-%m-%dT%H:%M:%S.%6f%Ez', tzinfo=times.UTC)
  return parsed_datetime


def CheckAndGetExpireTime(args):
  """Check if fields for expireTime are correctly specified and parse value."""

  # User can only specify either expiration_date or retention_period, not both.
  if (args.IsSpecified('expiration_date') and
      args.IsSpecified('retention_period')) or not(
          args.IsSpecified('expiration_date') or
          args.IsSpecified('retention_period')):
    raise c_exceptions.InvalidArgumentException(
        '--expiration-date or --retention-period',
        'Must specify either --expiration-date or --retention-period.')
  if args.expiration_date:
    return args.expiration_date
  elif args.retention_period:
    return ParseExpireTime(args.retention_period)


def GetBackup(backup_ref):
  """Get a backup."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  req = msgs.SpannerProjectsInstancesBackupsGetRequest(
      name=backup_ref.RelativeName())
  return client.projects_instances_backups.Get(req)


# Create Command Utils
def ModifyCreateRequest(backup_ref, args, req):
  """Parse arguments and construct create backup request."""
  req.parent = backup_ref.Parent().RelativeName()
  req.backupId = args.backup
  req.backup.database = req.parent + '/databases/'  + args.database
  req.backup.expireTime = CheckAndGetExpireTime(args)
  return req


def ModifyUpdateMetadataRequest(backup_ref, args, req):
  """Parse arguments and construct update backup request."""
  req.backup.name = backup_ref.Parent().RelativeName(
  ) + '/backups/' + args.backup
  req.backup.expireTime = CheckAndGetExpireTime(args)
  req.updateMask = 'expire_time'
  return req


def ModifyListRequest(instance_ref, args, req):
  """Parse arguments and construct list backups request."""
  req.parent = instance_ref.RelativeName()
  if args.database:
    database = instance_ref.RelativeName() + '/databases/' + args.database
    req.filter = 'database="{}"'.format(database)
  return req


def CheckBackupExists(backup_ref, _, req):
  """Checks if backup exists, if so, returns request."""

  # The delete API returns a 200 regardless of whether the backup being
  # deleted exists. In order to show users feedback for incorrectly
  # entered backup names, we have to make a request to check if the backup
  # exists. If the backup exists, it's deleted, otherwise, we display the
  # error from backups.Get.
  GetBackup(backup_ref)
  return req
