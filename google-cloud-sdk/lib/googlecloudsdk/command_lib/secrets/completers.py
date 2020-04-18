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
"""Completers to help with tab-completing."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.util import completers
from googlecloudsdk.core import resources


class BetaSecretsCompleter(completers.ListCommandCompleter):
  """A secrets completer for a resource argument.

  The Complete() method override bypasses the completion cache.
  """

  def __init__(self, **kwargs):
    super(BetaSecretsCompleter, self).__init__(
        collection='secretmanager.projects.secrets',
        list_command='beta secrets list --uri',
        **kwargs)

  def Complete(self, prefix, parameter_info):
    """Bypasses the cache and returns completions matching prefix."""
    # TODO(b/148274973): use built in completers once the cache stops
    # differentiating between project IDs and project numbers
    command = self.GetListCommand(parameter_info)
    items = self.GetAllItems(command, parameter_info)

    if not items:
      return

    # We only want to get the secret name from the response, which returns
    # projects/PROJECT_NUMBER/secrets/SECRET_NAME
    def _parse(item):
      return resources.REGISTRY.Parse(
          item, collection='secretmanager.projects.secrets').Name()

    return [
        x for x in (_parse(item) for item in items)
        if x and x.startswith(prefix)
    ]


class SecretsCompleter(completers.ListCommandCompleter):
  """A secrets completer for a resource argument.

  The Complete() method override bypasses the completion cache.
  """

  def __init__(self, **kwargs):
    super(SecretsCompleter, self).__init__(
        collection='secretmanager.projects.secrets',
        list_command='secrets list --uri',
        **kwargs)

  def Complete(self, prefix, parameter_info):
    """Bypasses the cache and returns completions matching prefix."""
    command = self.GetListCommand(parameter_info)
    items = self.GetAllItems(command, parameter_info)

    if not items:
      return

    # We only want to get the secret name from the response, which returns
    # projects/PROJECT_NUMBER/secrets/SECRET_NAME
    def _parse(item):
      return resources.REGISTRY.Parse(
          item, collection='secretmanager.projects.secrets').Name()

    return [
        x for x in (_parse(item) for item in items)
        if x and x.startswith(prefix)
    ]
