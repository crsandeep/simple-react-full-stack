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
"""Implementation of gcloud dataflow flex_template run command.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataflow import apis
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataflow import dataflow_util
from googlecloudsdk.core import properties


def _CommonRun(args):
  """Runs the command.

  Args:
    args: The arguments that were provided to this command invocation.

  Returns:
    A Job message.
  """
  arguments = apis.TemplateArguments(
      project_id=properties.VALUES.core.project.Get(required=True),
      region_id=dataflow_util.GetRegion(args),
      job_name=args.job_name,
      gcs_location=args.template_file_gcs_location,
      parameters=args.parameters)
  return apis.Templates.CreateJobFromFlexTemplate(arguments)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class RunBeta(base.Command):
  """Runs a job from the specified path."""

  detailed_help = {
      'DESCRIPTION':
          'Runs a job from the specified flex template gcs path.',
      'EXAMPLES':
          """\
          To run a job from the flex template, run:

            $ {command} my-job \
              --template-file-gcs-location=gs://flex-template-path \
              --region=europe-west1 \
              --parameters=input="gs://input",output="gs://output-path",\
              max_num_workers=5
          """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'job_name',
        metavar='JOB_NAME',
        help='The unique name to assign to the job.')

    parser.add_argument(
        '--template-file-gcs-location',
        help=('The Google Cloud Storage location of the flex template to run. '
              "(Must be a URL beginning with 'gs://'.)"),
        type=arg_parsers.RegexpValidator(r'^gs://.*',
                                         'Must begin with \'gs://\''),
        required=True)

    parser.add_argument(
        '--region',
        metavar='REGION_ID',
        help=('The region ID of the job\'s regional endpoint. ' +
              dataflow_util.DEFAULT_REGION_MESSAGE))

    parser.add_argument(
        '--parameters',
        metavar='PARAMETERS',
        type=arg_parsers.ArgDict(),
        action=arg_parsers.UpdateAction,
        help=
        ('The parameters to pass to the job.'
         'All pipeline options should be passed via parameters flag.\n'
         'Use right casing format according to the sdk.\n'
         'Example: --parameters=maxNumWorkers=5 for java sdk 1.X and '
         '--parameters=max_num_workers=5 for python sdk.\n'
         'For all the parameter options please refer\n'
         'https://cloud.google.com/dataflow/docs/guides/specifying-exec-params'
         '#setting-other-cloud-dataflow-pipeline-options'))

  def Run(self, args):
    return _CommonRun(args)
