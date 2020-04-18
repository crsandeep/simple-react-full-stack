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
"""Contains hooks to be executed along with Cloud Workflows gcloud commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import log

import six


def print_describe_instruction(response, args):
  """Prints describe execution command for just created execution of a workflow.

  Function to be used as a response hook
  (go/gcloud-declarative-commands#response)

  Args:
    response: API response
    args: gcloud command arguments

  Returns:
    response: API response
  """
  cmd_base = " ".join(args.command_path[:-1])
  execution_id = six.text_type(response.name).split("/")[-1]
  log.status.Print(
      "\nTo view the workflow status, you can use following command:")
  log.status.Print("{} executions describe {} --workflow {}".format(
      cmd_base, execution_id, args.workflow))
  return response
