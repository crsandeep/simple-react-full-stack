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
"""Command to create Cloud Firestore Database in Native mode."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.firestore import create_util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.Command):
  """Create a Google Cloud Firestore Native database."""
  product_name = 'Google Cloud Firestore Native'
  enum_value = core_apis.GetMessagesModule(
      'appengine', 'v1').Application.DatabaseTypeValueValuesEnum.CLOUD_FIRESTORE
  detailed_help = {
      'DESCRIPTION':
          """\
          {description}
          """,
      'EXAMPLES':
          """\
          To create Google Cloud Firestore Native database

              $ {command}

          To create an app in the us-central region, run:

              $ {command} --region=us-central

          """,
  }

  def Run(self, args):
    create_util.create(args, self.product_name, self.enum_value)

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--region',
        help=(
            'The region to create the {product_name} database within. '
            'Use `gcloud app regions list` to list available regions.').format(
                product_name=Create.product_name))
