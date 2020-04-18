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
"""Describe local Anthos package."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.anthos import anthoscli_backend
from googlecloudsdk.command_lib.anthos import flags


class Describe(base.BinaryBackedCommand):
  """Describe local Anthos package.

   Display package description.
  """
  detailed_help = {
      'EXAMPLES': """
      To describe current directory:

          $ {command}

      To describe package `my-foo` in user HOME dir:

          $ {command} ~/my-foo

      """,
  }

  @staticmethod
  def Args(parser):
    flags.GetLocalDirFlag(
        help_override='The local of package directory.').AddToParser(parser)

  def Run(self, args):
    command_executor = anthoscli_backend.AnthosCliWrapper()
    response = command_executor(command='desc',
                                local_dir=args.LOCAL_DIR,
                                env=anthoscli_backend.GetEnvArgsForCommand(),
                                show_exec_error=args.show_exec_error)
    return self._DefaultOperationResponseHandler(response)
