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
"""Helper functions for GKE deploy."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import logging
import re
import subprocess

from googlecloudsdk.core.util import encoding

_GIT_PENDING_CHANGE_PATTERN = ('^# *('
                               'Untracked files|'
                               'Changes to be committed|'
                               'Changes not staged for commit'
                               '):')


def IsGithubRepository(source_directory):
  """Checks if the directory is within a valid git repo.

  Args:
    source_directory: The path a directory.

  Returns:
    True if the directory is within a valid git repo.
  """
  status = _CallGit(source_directory, 'status')
  return status is not None


def HasPendingChanges(source_directory):
  """Checks if the git repo in a directory has any pending changes.

  Args:
    source_directory: The path to directory containing the source code.

  Returns:
    True if there are any uncommitted or untracked changes in the local repo
    for the given directory.
  """
  status = _CallGit(source_directory, 'status')
  return re.search(_GIT_PENDING_CHANGE_PATTERN, status, flags=re.MULTILINE)


def GetGitHeadRevision(source_directory):
  """Finds the current HEAD revision for the given source directory.

  Args:
    source_directory: The path to directory containing the source code.

  Returns:
    The HEAD revision of the current branch, or None if the command failed.
  """
  raw_output = _CallGit(source_directory, 'rev-parse', 'HEAD')
  return raw_output.strip() if raw_output else None


def _CallGit(cwd, *args):
  """Calls git with the given args, in the given working directory.

  Args:
    cwd: The working directory for the command.
    *args: Any arguments for the git command.

  Returns:
    The raw output of the command, or None if the command failed.
  """
  try:
    return encoding.Decode(
        subprocess.check_output(['git'] + list(args), cwd=cwd))
  except (OSError, subprocess.CalledProcessError) as e:
    logging.debug('Could not call git with args %s: %s', args, e)
    return None
