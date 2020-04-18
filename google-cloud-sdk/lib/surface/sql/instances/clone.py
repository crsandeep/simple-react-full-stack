# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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
"""Clones a Cloud SQL instance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.api_lib.sql import exceptions
from googlecloudsdk.api_lib.sql import instances as instance_util
from googlecloudsdk.api_lib.sql import operations
from googlecloudsdk.api_lib.sql import validate
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.sql import flags
from googlecloudsdk.command_lib.sql import instances as command_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


def _GetInstanceRefsFromArgs(args, client):
  """Get validated refs to source and destination instances from args."""

  validate.ValidateInstanceName(args.source)
  validate.ValidateInstanceName(args.destination)
  source_instance_ref = client.resource_parser.Parse(
      args.source,
      params={'project': properties.VALUES.core.project.GetOrFail},
      collection='sql.instances')
  destination_instance_ref = client.resource_parser.Parse(
      args.destination,
      params={'project': properties.VALUES.core.project.GetOrFail},
      collection='sql.instances')

  _CheckSourceAndDestination(source_instance_ref, destination_instance_ref)
  return source_instance_ref, destination_instance_ref


def _CheckSourceAndDestination(source_instance_ref, destination_instance_ref):
  """Verify that the source and destination instance ids are different."""

  if source_instance_ref.project != destination_instance_ref.project:
    raise exceptions.ArgumentError(
        'The source and the clone instance must belong to the same project:'
        ' "{src}" != "{dest}".'.format(
            src=source_instance_ref.project,
            dest=destination_instance_ref.project))


def _UpdateRequestFromArgs(request, args, sql_messages, supports_point_in_time):
  """Update request with point-in-time recovery options."""

  if args.bin_log_file_name and args.bin_log_position:
    clone_context = request.instancesCloneRequest.cloneContext
    clone_context.binLogCoordinates = sql_messages.BinLogCoordinates(
        binLogFileName=args.bin_log_file_name,
        binLogPosition=args.bin_log_position)
  elif supports_point_in_time and args.point_in_time:
    clone_context = request.instancesCloneRequest.cloneContext
    clone_context.pointInTime = args.point_in_time.strftime(
        '%Y-%m-%dT%H:%M:%S.%fZ')


def RunBaseCloneCommand(args, supports_point_in_time=False):
  """Clones a Cloud SQL instance.

  Args:
    args: argparse.Namespace, The arguments used to invoke this command.
    supports_point_in_time: bool, Whether the point_in_time field is supported.

  Returns:
    A dict object representing the operations resource describing the
    clone operation if the clone was successful.
  Raises:
    ArgumentError: The arguments are invalid for some reason.
  """

  client = api_util.SqlClient(api_util.API_VERSION_DEFAULT)
  sql_client = client.sql_client
  sql_messages = client.sql_messages

  source_instance_ref, destination_instance_ref = (
      _GetInstanceRefsFromArgs(args, client))

  request = sql_messages.SqlInstancesCloneRequest(
      project=source_instance_ref.project,
      instance=source_instance_ref.instance,
      instancesCloneRequest=sql_messages.InstancesCloneRequest(
          cloneContext=sql_messages.CloneContext(
              kind='sql#cloneContext',
              destinationInstanceName=destination_instance_ref.instance)))

  _UpdateRequestFromArgs(request, args, sql_messages, supports_point_in_time)

  # Check if source is V1; raise error if so.
  # Check if source has customer-managed key; show warning if so.
  try:
    source_instance_resource = sql_client.instances.Get(
        sql_messages.SqlInstancesGetRequest(
            project=source_instance_ref.project,
            instance=source_instance_ref.instance))

    # TODO(b/122660263): Remove when V1 instances are no longer supported.
    if instance_util.IsInstanceV1(sql_messages, source_instance_resource):
      raise exceptions.ArgumentError(
          'First Generation instances can no longer be created.')
    if source_instance_resource.diskEncryptionConfiguration:
      command_util.ShowCmekWarning('clone', 'the source instance')
  except apitools_exceptions.HttpError:
    # This is for informational purposes, so don't throw an error if failure.
    pass

  result = sql_client.instances.Clone(request)

  operation_ref = client.resource_parser.Create(
      'sql.operations',
      operation=result.name,
      project=destination_instance_ref.project)

  if args.async_:
    if not args.IsSpecified('format'):
      args.format = 'default'
    return sql_client.operations.Get(
        sql_messages.SqlOperationsGetRequest(
            project=operation_ref.project, operation=operation_ref.operation))
  operations.OperationsV1Beta4.WaitForOperation(sql_client, operation_ref,
                                                'Cloning Cloud SQL instance')
  log.CreatedResource(destination_instance_ref)
  rsource = sql_client.instances.Get(
      sql_messages.SqlInstancesGetRequest(
          project=destination_instance_ref.project,
          instance=destination_instance_ref.instance))
  rsource.kind = None
  return rsource


def AddBaseArgs(parser, pitr_options_group):
  """Add args common to all release tracks to parser."""
  base.ASYNC_FLAG.AddToParser(parser)
  parser.display_info.AddFormat(flags.GetInstanceListFormat())
  parser.add_argument(
      'source',
      completer=flags.InstanceCompleter,
      help='Cloud SQL instance ID of the source.')
  parser.add_argument('destination', help='Cloud SQL instance ID of the clone.')
  bin_log_group = pitr_options_group.add_group(
      mutex=False,
      required=False,
      help='Binary log coordinates for point-in-time recovery.')
  bin_log_group.add_argument(
      '--bin-log-file-name',
      required=True,
      help="""\
      The name of the binary log file. Enable point-in-time recovery on the
      source instance to create a binary log file. If specified with
      <--bin-log-position> to form a valid binary log coordinate, it defines an
      earlier point in time to clone a source instance from.
      For example, mysql-bin.000001.
      """)
  bin_log_group.add_argument(
      '--bin-log-position',
      type=int,
      required=True,
      help="""\
      Represents the state of an instance at any given point in time inside a
      binary log file. If specified along with <--bin-log-file-name> to form a
      valid binary log coordinate, it defines an earlier point in time to clone
      a source instance from.
      For example, 123 (a numeric value).
      """)


def AddAlphaArgs(pitr_options_group):
  """Add args for the alpha release track to parser."""
  pitr_options_group.add_argument(
      '--point-in-time',
      type=arg_parsers.Datetime.Parse,
      required=False,
      help="""\
      Represents the state of an instance at any given point in time inside a
      write-ahead log file. Enable point-in-time recovery on the source
      instance to create a write-ahead log file. Uses RFC 3339 format in UTC
      timezone. If specified, defines a past state of your instance to clone.
      For example, '2012-11-15T16:19:00.094Z'.
      """)


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class Clone(base.CreateCommand):
  # pylint: disable=line-too-long
  """Clones a Cloud SQL instance.

  *{command}* creates a clone of the Cloud SQL instance. The source and the
  destination instances must be in the same project. Once created, the clone is
  an independent Cloud SQL instance.

  The binary log coordinates, if specified, act as the point up to which the
  source instance is cloned. If not specified, the source instance is
  cloned up to the most recent binary log coordinates at the time the command is
  executed.

  ## EXAMPLES

  To clone a source instance to the most recent binary log coordinates:

    $ {command} instance-foo instance-bar

  To clone at specific binary log coordinates:

    $ {command} instance-foo instance-bar --bin-log-file-name mysql-bin.000020 --bin-log-position 170
  """

  @classmethod
  def Args(cls, parser):
    """Declare flag and positional arguments for the command parser."""
    pitr_options_group = parser.add_group(mutex=True, required=False)
    AddBaseArgs(parser, pitr_options_group)
    parser.display_info.AddCacheUpdater(flags.InstanceCompleter)

  def Run(self, args):
    return RunBaseCloneCommand(args)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CloneAlpha(base.CreateCommand):
  # pylint: disable=line-too-long
  """Clones a Cloud SQL instance.

  *{command}* creates a clone of a Cloud SQL instance. The clone is an
  independent copy of the source instance with the same data and settings.
  Source and destination instances must be in the same project. You can clone
  the current state of an instance, or from an earlier point in time.

  For MySQL: The binary log coordinates, if specified, act as the point in time
  the source instance is cloned from. If not specified, you clone the current
  state.

  For PostgreSQL: The point in time, if specified, defines a past state of your
  instance to clone.

  ## EXAMPLES

  To clone a MySQL instance from its current state (most recent binary log
  coordinates):

    $ {command} instance-foo instance-bar

  To clone a MySQL instance from an earlier point in time (past binary log
  coordinates):

    $ {command} instance-foo instance-bar --bin-log-file-name mysql-bin.000020 --bin-log-position 170

  To clone a PostgreSQL source instance at a specific point in time:

    $ {command} instance-foo instance-bar --point-in-time '2012-11-15T16:19:00.094Z'
  """

  @classmethod
  def Args(cls, parser):
    pitr_options_group = parser.add_group(mutex=True, required=False)
    AddBaseArgs(parser, pitr_options_group)
    AddAlphaArgs(pitr_options_group)
    parser.display_info.AddCacheUpdater(flags.InstanceCompleter)

  def Run(self, args):
    return RunBaseCloneCommand(args, supports_point_in_time=True)
