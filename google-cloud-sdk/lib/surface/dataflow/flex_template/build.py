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
"""Implementation of gcloud dataflow flex_template build command.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataflow import apis
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties


def _CommonRun(args):
  """Runs the command.

  Args:
    args: The arguments that were provided to this command invocation.

  Returns:
    A Job message.
  """
  return apis.Templates.BuildAndStoreFlexTemplateFile(
      args.template_file_gcs_path, args.image, args.metadata_file,
      args.sdk_language, args.print_only)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class RunBeta(base.Command):
  """Builds a flex template file from the specified parameters."""

  detailed_help = {
      'DESCRIPTION':
          'Builds a flex template file from the specified parameters.',
      'EXAMPLES':
          """\
          To build and store a the flex template json file, run:

            $ {command} gs://template-file-gcs-path --image=gcr://image-path \
              --metadata-file=/local/path/to/metadata.json --sdk-language=JAVA
          """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'template_file_gcs_path',
        metavar='TEMPLATE_FILE_GCS_PATH',
        help=('The Google Cloud Storage location of the flex template file.'
              'Overrides if file already exists.'),
        type=arg_parsers.RegexpValidator(r'^gs://.*',
                                         'Must begin with \'gs://\''))

    parser.add_argument(
        '--image',
        help=('Path to the any image registry location of the flex template '
              'image.'),
        required=True)

    parser.add_argument(
        '--sdk-language',
        help=('SDK language of the flex template job.'),
        choices=['JAVA', 'PYTHON'],
        required=True)

    parser.add_argument(
        '--metadata-file',
        help='Local path to the metadata json file for the flex template.',
        type=arg_parsers.FileContents())

    parser.add_argument(
        '--print-only',
        help=('Prints the container spec to stdout. Does not save in '
              'Google Cloud Storage.'),
        default=False,
        action=actions.StoreBooleanProperty(
            properties.VALUES.dataflow.print_only))

  def Run(self, args):
    return _CommonRun(args)
