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
"""Common utilities and shared helpers for secrets."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import files

DEFAULT_MAX_BYTES = 65536


def ReadFileOrStdin(path, max_bytes=None):
  """Read data from the given file path or from stdin.

  This is similar to the cloudsdk built in ReadFromFileOrStdin, except that it
  limits the total size of the file and it returns None if given a None path.
  This makes the API in command surfaces a bit cleaner.

  Args:
      path (str): path to the file on disk or "-" for stdin
      max_bytes (int): maximum number of bytes

  Returns:
      result (str): result of reading the file
  """
  if not path:
    return None

  max_bytes = max_bytes or DEFAULT_MAX_BYTES

  try:
    data = console_io.ReadFromFileOrStdin(path, binary=True)
    if len(data) > max_bytes:
      raise exceptions.BadFileException(
          'The file [{path}] is larger than the maximum size of {max_bytes} '
          'bytes.'.format(path=path, max_bytes=max_bytes))
    return data
  except files.Error as e:
    raise exceptions.BadFileException(
        'Failed to read file [{path}]: {e}'.format(path=path, e=e))


def GetVersionFromReleasePath(release_track):
  """Converts a ReleaseTrack to a version string used to initialize clients.

  If the release track is unknown, default to v1 rather than raise an exception.
  This should never happen as we only support BETA and GA, but if it somehow
  does, it shouldn't break the user's ability to use the gcloud SDK.

  Args:
      release_track (base.ReleaseTrack): Release track to get version string for

  Returns:
      result (str): version string corresponding to the given release_track.
      Defaults to v1 (GA) if unrecognized.
  """
  if release_track == base.ReleaseTrack.BETA:
    return 'v1beta1'
  return 'v1'
