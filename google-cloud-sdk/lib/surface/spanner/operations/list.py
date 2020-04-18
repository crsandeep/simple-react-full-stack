# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Command for spanner operations list."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.spanner import backup_operations
from googlecloudsdk.api_lib.spanner import database_operations
from googlecloudsdk.api_lib.spanner import instance_operations
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exceptions
from googlecloudsdk.command_lib.spanner import flags


def _TransformOperationDone(resource):
  """Shows value for done in table."""
  return 'done' in resource


def _TransformDatabaseId(resource):
  """Gets database ID depending on operation type."""
  metadata = resource.get('metadata')
  base_type = 'type.googleapis.com/google.spanner.admin.database.v1.{}'
  op_type = metadata.get('@type')

  if op_type == base_type.format(
      'RestoreDatabaseMetadata') or op_type == base_type.format(
          'OptimizeRestoredDatabaseMetadata'):
    return metadata.get('name')
  return metadata.get('database')


class List(base.ListCommand):
  """List the Cloud Spanner operations on the given instance or database."""

  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""\
        To list Cloud Spanner instance operations for an instance, run:

          $ {command} --instance=my-instance-id --type=INSTANCE

        To list Cloud Spanner backup operations for an instance, run:

          $ {command} --instance=my-instance-id --type=BACKUP

        To list Cloud Spanner database operations for an instance, run:

          $ {command} --instance=my-instance-id --type=DATABASE

        To list Cloud Spanner database operations for a database, run:

          $ {command} --instance=my-instance-id --database=my-database-id --type=DATABASE

        To list Cloud Spanner backup operations for a database, run:

          $ {command} --instance=my-instance-id --database=my-database-id --type=BACKUP

        To list Cloud Spanner backup operations for a backup, run:

          $ {command} --instance=my-instance-id --backup=my-backup-id --type=BACKUP
        """),
  }

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Please add arguments in alphabetical order except for no- or a clear-
    pair for that argument which can follow the argument itself.
    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    flags.Instance(
        positional=False,
        text='The ID of the instance the operations are executing on.'
    ).AddToParser(parser)
    flags.Database(
        positional=False,
        required=False,
        text='For database operations, the name of the database '
        'the operations are executing on.').AddToParser(parser)
    flags.Backup(
        positional=False,
        required=False,
        text='For backup operations, the name of the backup '
        'the operations are executing on.').AddToParser(parser)

    type_choices = {
        'INSTANCE':
            'Returns instance operations for the given instance. '
            'Note, type=INSTANCE does not work with --database or --backup.',
        'DATABASE':
            'If only the instance is specified (--instance), returns all '
            'database operations associated with the databases in the '
            'instance. When a database is specified (--database), the command '
            'would return database operations for the given database.',
        'BACKUP':
            'If only the instance is specified (--instance), returns all '
            'backup operations associated with backups in the instance. When '
            'a backup is specified (--backup), only the backup operations for '
            'the given backup are returned.',
        'DATABASE_RESTORE':
            'Database restore operations are returned for all databases in '
            'the given instance (--instance only) or only those associated '
            'with the given database (--database)',
        'DATABASE_CREATE':
            'Database create operations are returned for all databases in '
            'the given instance (--instance only) or only those associated '
            'with the given database (--database)',
        'DATABASE_UPDATE_DDL':
            'Database update DDL operations are returned for all databases in '
            'the given instance (--instance only) or only those associated '
            'with the given database (--database)'
    }

    parser.add_argument(
        '--type',
        default='',
        type=lambda x: x.upper(),
        choices=type_choices,
        help='(optional) List only the operations of the given type.')

    parser.display_info.AddFormat("""
          table(
            name.basename():label=OPERATION_ID,
            metadata.statements.join(sep="\n"),
            done():label=DONE,
            metadata.'@type'.split('.').slice(-1:).join()
          )
        """)
    parser.display_info.AddCacheUpdater(None)
    parser.display_info.AddTransforms({'done': _TransformOperationDone})
    parser.display_info.AddTransforms({'database': _TransformDatabaseId})

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    is_database_type = (
        args.type == 'DATABASE_RESTORE' or args.type == 'DATABASE' or
        args.type == 'DATABASE_CREATE' or args.type == 'DATABASE_UPDATE_DDL')

    if args.backup or args.type == 'BACKUP':
      # Update output table for backup operations.
      # pylint:disable=protected-access
      args._GetParser().ai.display_info.AddFormat("""
          table(
            name.basename():label=OPERATION_ID,
            done():label=DONE,
            metadata.'@type'.split('.').slice(-1:).join(),
            metadata.name.split('/').slice(-1:).join():label=BACKUP,
            metadata.database.split('/').slice(-1).join():label=SOURCE_DATABASE,
            metadata.progress.startTime:label=START_TIME,
            metadata.progress.endTime:label=END_TIME
          )
        """)

    if args.type == 'DATABASE_RESTORE':
      # Update output table for restore operations.
      # pylint:disable=protected-access
      args._GetParser().ai.display_info.AddFormat("""
          table(
            name.basename():label=OPERATION_ID,
            done():label=DONE,
            metadata.'@type'.split('.').slice(-1:).join(),
            metadata.name.split('/').slice(-1:).join():label=RESTORED_DATABASE,
            metadata.backupInfo.backup.split('/').slice(-1).join():label=SOURCE_BACKUP,
            metadata.progress.startTime:label=START_TIME,
            metadata.progress.endTime:label=END_TIME
          )
        """)
    elif is_database_type:
      # Update output table for database operations.
      # pylint:disable=protected-access
      args._GetParser().ai.display_info.AddFormat("""
          table(
            name.basename():label=OPERATION_ID,
            metadata.statements.join(sep="\n"),
            done():label=DONE,
            metadata.'@type'.split('.').slice(-1:).join(),
            database().split('/').slice(-1:).join():label=DATABASE_ID
          )
        """)

    # Checks that user only specified either database or backup flag.
    if (args.IsSpecified('database') and args.IsSpecified('backup')):
      raise c_exceptions.InvalidArgumentException(
          '--database or --backup',
          'Must specify either --database or --backup. To search backups for a '
          'specifc database, use the --database flag with --type=BACKUP')

    # Checks that the user did not specify the backup flag with the type filter
    # set to a database operation type.
    if (args.IsSpecified('backup') and is_database_type):
      raise c_exceptions.InvalidArgumentException(
          '--backup or --type',
          'The backup flag cannot be used with the type flag set to a '
          'database operation type.'
      )

    if args.type == 'BACKUP':
      if args.database:
        db_filter = backup_operations.BuildDatabaseFilter(
            args.instance, args.database)
        return backup_operations.List(args.instance, db_filter)
      if args.backup:
        return backup_operations.ListGeneric(args.instance, args.backup)
      return backup_operations.List(args.instance)

    if is_database_type:
      type_filter = database_operations.BuildDatabaseOperationTypeFilter(
          args.type)
      return database_operations.ListDatabaseOperations(args.instance,
                                                        args.database,
                                                        type_filter)

    if args.backup:
      return backup_operations.ListGeneric(args.instance, args.backup)
    if args.database:
      return database_operations.List(args.instance, args.database)

    return instance_operations.List(args.instance)
