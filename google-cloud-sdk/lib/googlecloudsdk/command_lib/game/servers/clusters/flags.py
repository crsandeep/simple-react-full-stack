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
"""Flags and helpers for Cloud Gaming commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


def AddDryrunArg(parser):
  """Add a dryrun arg."""
  parser.add_argument('--dry-run',
                      action='store_true',
                      required=True,
                      help='Validate the operation, but do not execute it.')


def AddPreviewTimeArg(parser):
  """Add a preview_time arg."""
  parser.add_argument(
      '--preview-time',
      required=False,
      help='This attribute is only relevant for preview (--dry-run).' +
      ' It is used to validate the state for a future time.')
