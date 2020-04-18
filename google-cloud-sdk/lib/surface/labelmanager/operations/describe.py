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
"""Describe command for the Label Manager - Operations CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.labelmanager import service as labelmanager
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.labelmanager import arguments


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.Command):
  r"""Describes a LabelManager long running operation.

  ## EXAMPLES

  To get details about a LabelManager long running operation with name
  'operations/clk.12345', run:

        $ {command} operations/clk.12345
  """

  @staticmethod
  def Args(parser):
    arguments.AddOperationNameArgToParser(parser)

  def Run(self, args):
    operations_service = labelmanager.OperationsService()
    labelmanager_messages = labelmanager.LabelManagerMessages()
    operation_name = args.OPERATION_NAME

    get_request = labelmanager_messages.LabelmanagerOperationsGetRequest(
        name=operation_name)
    return operations_service.Get(get_request)
