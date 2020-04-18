# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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

"""'logging sinks create' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class Create(base.CreateCommand):
  # pylint: disable=line-too-long
  """Creates a sink.

  Creates a sink used to export entries from one or more logs to a destination.
  A sink exports all logs that matches *--log-filter* flag.
  An empty filter matches all logs.
  The sink's destination can be a Cloud Storage bucket, a BigQuery dataset,
  or a Cloud Pub/Sub topic.
  The destination must already exist and Stackdriver Logging must have
  permission to write to it.
  Log entries are exported as soon as the sink is created.
  See https://cloud.google.com/logging/docs/export/configure_export_v2#dest-auth.

  ## EXAMPLES

  To export all Google Compute Engine logs to BigQuery, run:

    $ {command} my-bq-sink bigquery.googleapis.com/projects/my-project/datasets/my_dataset --log-filter='resource.type="gce_instance"'

  To export "syslog" from App Engine Flexible to Cloud Storage, run:

    $ {command} my-gcs-sink storage.googleapis.com/my-bucket --log-filter='logName="projects/my-project/appengine.googleapis.com%2Fsyslog"'

  To export Google App Engine logs with ERROR severity, run:

    $ {command} my-error-logs bigquery.googleapis.com/projects/my-project/datasets/my_dataset --log-filter='resource.type="gae_app" AND severity=ERROR'

  Detailed information about filters can be found at:
  [](https://cloud.google.com/logging/docs/view/advanced_filters)
  """
  # pylint: enable=line-too-long

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument(
        'sink_name', help='The name for the sink.')
    parser.add_argument(
        'destination', help='The destination for the sink.')
    parser.add_argument(
        '--log-filter', required=False,
        help=('A filter expression for the sink. If present, the filter '
              'specifies which log entries to export.'))
    parser.add_argument(
        '--include-children', required=False, action='store_true',
        help=('Whether to export logs from all child projects and folders. '
              'Only applies to sinks for organizations and folders.'))
    util.AddParentArgs(parser, 'Create a sink')
    parser.display_info.AddCacheUpdater(None)

  def CreateSink(self, parent, sink_data):
    """Creates a v2 sink specified by the arguments."""
    messages = util.GetMessages()
    return util.GetClient().projects_sinks.Create(
        messages.LoggingProjectsSinksCreateRequest(
            parent=parent, logSink=messages.LogSink(**sink_data),
            uniqueWriterIdentity=True))

  def _Run(self, args, is_alpha=False):
    if not args.log_filter:
      # Attempt to create a sink with an empty filter.
      console_io.PromptContinue(
          'Sink with empty filter matches all entries.', cancel_on_no=True)

    if args.include_children and not (args.organization or args.folder):
      log.warning('include-children only has an effect for sinks at the folder '
                  'or organization level')

    sink_ref = util.GetSinkReference(args.sink_name, args)

    sink_data = {
        'name': sink_ref.sinksId,
        'destination': args.destination,
        'filter': args.log_filter,
        'includeChildren': args.include_children
    }

    dlp_options = {}
    if is_alpha:
      if args.IsSpecified('dlp_inspect_template'):
        dlp_options['inspectTemplateName'] = args.dlp_inspect_template
      if args.IsSpecified('dlp_deidentify_template'):
        dlp_options['deidentifyTemplateName'] = args.dlp_deidentify_template
      if dlp_options:
        sink_data['dlpOptions'] = dlp_options

      if args.IsSpecified('use_partitioned_tables'):
        bigquery_options = {}
        bigquery_options['usePartitionedTables'] = args.use_partitioned_tables
        sink_data['bigqueryOptions'] = bigquery_options

      if args.IsSpecified('exclusion'):
        sink_data['exclusions'] = args.exclusion

      if args.IsSpecified('description'):
        sink_data['description'] = args.description

      if args.IsSpecified('disabled'):
        sink_data['disabled'] = args.disabled

    result = self.CreateSink(util.GetParentFromArgs(args), sink_data)

    log.CreatedResource(sink_ref)
    self._epilog_result_destination = result.destination
    self._epilog_writer_identity = result.writerIdentity
    self._epilog_is_dlp_sink = bool(dlp_options)
    return result

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The created sink with its destination.
    """
    return self._Run(args)

  def Epilog(self, unused_resources_were_displayed):
    util.PrintPermissionInstructions(self._epilog_result_destination,
                                     self._epilog_writer_identity,
                                     self._epilog_is_dlp_sink)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(Create):
  # pylint: disable=line-too-long
  """Creates a sink.

  Creates a sink used to export entries from one or more logs to a destination.
  A sink exports all logs that matches *--log-filter* flag.
  An empty filter matches all logs.
  The sink's destination can be a Cloud Storage bucket, a BigQuery dataset,
  or a Cloud Pub/Sub topic.
  The destination must already exist and Stackdriver Logging must have
  permission to write to it.
  Log entries are exported as soon as the sink is created.
  See https://cloud.google.com/logging/docs/export/configure_export_v2#dest-auth.

  ## EXAMPLES

  To export all Google Compute Engine logs to BigQuery, run:

    $ {command} my-bq-sink bigquery.googleapis.com/projects/my-project/datasets/my_dataset --log-filter='resource.type="gce_instance"'

  To export "syslog" from App Engine Flexible to Cloud Storage, run:

    $ {command} my-gcs-sink storage.googleapis.com/my-bucket --log-filter='logName="projects/my-project/appengine.googleapis.com%2Fsyslog"'

  To export Google App Engine logs with ERROR severity, run:

    $ {command} my-error-logs bigquery.googleapis.com/projects/my-project/datasets/my_dataset --log-filter='resource.type="gae_app" AND severity=ERROR'

  To export all logs to a Logs bucket in a different project, run:

    $ {command} my-sink logging.googleapis.com/projects/my-central-project/locations/global/buckets/my-central-bucket

  Detailed information about filters can be found at:
  [](https://cloud.google.com/logging/docs/view/advanced_filters)
  """
  # pylint: enable=line-too-long

  @staticmethod
  def Args(parser):
    Create.Args(parser)
    dlp_group = parser.add_argument_group(
        help='Settings for Cloud DLP enabled sinks.')
    dlp_group.add_argument(
        '--dlp-inspect-template',
        required=True,
        help=('Relative path to a Cloud DLP inspection template resource. For '
              'example "projects/my-project/inspectTemplates/my-template" or '
              '"organizations/my-org/inspectTemplates/my-template".'))
    dlp_group.add_argument(
        '--dlp-deidentify-template',
        required=True,
        help=('Relative path to a Cloud DLP de-identification template '
              'resource. For example '
              '"projects/my-project/deidentifyTemplates/my-template" or '
              '"organizations/my-org/deidentifyTemplates/my-template".'))

    bigquery_group = parser.add_argument_group(
        help='Settings for sink exporting data to BigQuery.')
    bigquery_group.add_argument(
        '--use-partitioned-tables', required=False, action='store_true',
        help=('If specified, use BigQuery\'s partitioned tables. By default, '
              'Logging creates dated tables based on the log entries\' '
              'timestamps, e.g. \'syslog_20170523\'. Partitioned tables remove '
              'the suffix and special query syntax '
              '(https://cloud.google.com/bigquery/docs/'
              'querying-partitioned-tables) must be used.'))

    parser.add_argument(
        '--exclusion', action='append',
        type=arg_parsers.ArgDict(
            spec={
                'name': str,
                'description': str,
                'filter': str,
                'disabled': bool
            },
            required_keys=['name', 'filter']
        ),
        help=('Specify an exclusion filter for a log entry that is not to be '
              'exported. This flag can be repeated.\n\n'
              'The ``name\'\' and ``filter\'\' attributes are required. The '
              'following keys are accepted:\n\n'
              '*name*::: An identifier, such as ``load-balancer-exclusion\'\'. '
              'Identifiers are limited to 100 characters and can include only '
              'letters, digits, underscores, hyphens, and periods.\n\n'
              '*description*::: A description of this exclusion.\n\n'
              '*filter*::: An advanced log filter that matches the log entries '
              'to be excluded.\n\n'
              '*disabled*::: If this exclusion should be disabled and not '
              'exclude the log entries.'))

    parser.add_argument(
        '--description',
        help='Description of the sink.')

    parser.add_argument(
        '--disabled', action='store_true',
        help=('Sink will be disabled. Disabled sinks do not export logs.'))

  def Run(self, args):
    return self._Run(args, is_alpha=True)
