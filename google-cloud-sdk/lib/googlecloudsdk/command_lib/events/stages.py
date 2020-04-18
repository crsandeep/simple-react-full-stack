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
"""Gather stage/condition information for any important objects here."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.core.console import progress_tracker


_TRIGGER_SUBSCRIBED = 'Subscribed'
_TRIGGER_DEPENDENCY = 'DependencyReady'
# Source's only have 1 guaranteed condition, Ready, which is also their terminal
# condition. Because its terminal and not a unique condition name, we'll use
# this stage to manually track it.
SOURCE_READY = 'source_ready'


def TriggerAndSourceStages():
  return [
      progress_tracker.Stage('Creating Event Source...', key=SOURCE_READY)
  ] + TriggerStages()


def TriggerStages():
  return [
      progress_tracker.Stage('Subscribing Service...', key=_TRIGGER_SUBSCRIBED),
      progress_tracker.Stage('Linking Trigger...', key=_TRIGGER_DEPENDENCY),
  ]


def TriggerSourceDependencies():
  return {
      _TRIGGER_SUBSCRIBED: {SOURCE_READY},
      _TRIGGER_DEPENDENCY: {SOURCE_READY}
  }
