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
"""create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.services import serviceusage
from googlecloudsdk.calliope import base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


class Create(base.CreateCommand):
  """Create a service identity for a consumer.

  This command creates a service identity for a consumer. The supported
  consumers are projects.

  ## EXAMPLES

  To create a service identity for a project, run:

    $ {command} --service=example.googleapis.com --project=helloworld
  """

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    parser.add_argument(
        '--service',
        required=True,
        help='The service to create a service identity for.')

  def Run(self, args):
    """Run 'services identity create'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      Nothing.
    """
    project = properties.VALUES.core.project.Get(required=True)
    email, _ = serviceusage.GenerateServiceIdentity(project, args.service)
    if not email:
      raise exceptions.Error('Service identity not created successfully')
    else:
      log.status.Print('Service identity created: {0}'.format(email))
