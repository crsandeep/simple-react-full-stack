# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Utilities for parsing arguments to `gcloud tasks` commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.tasks import app
from googlecloudsdk.command_lib.tasks import constants
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import http_encoding

import six  # pylint: disable=unused-import
from six.moves import filter  # pylint:disable=redefined-builtin
from six.moves import map  # pylint:disable=redefined-builtin


_PROJECT = properties.VALUES.core.project.GetOrFail


class NoFieldsSpecifiedError(exceptions.Error):
  """Error for when calling an update method with no fields specified."""


class FullTaskUnspecifiedError(exceptions.Error):
  """Error parsing task without specifing the queue or full path."""


class QueueUpdatableConfiguration(object):
  """Data Class for queue configuration updates."""

  @classmethod
  def FromQueueTypeAndReleaseTrack(cls,
                                   queue_type,
                                   release_track=base.ReleaseTrack.GA):
    """Creates QueueUpdatableConfiguration from the given parameters."""
    config = cls()
    config.retry_config = {}
    config.rate_limits = {}
    config.app_engine_routing_override = {}
    config.stackdriver_logging_config = {}

    config.retry_config_mask_prefix = None
    config.rate_limits_mask_prefix = None
    config.app_engine_routing_override_mask_prefix = None
    config.stackdriver_logging_config_mask_prefix = None

    if queue_type == constants.PULL_QUEUE:
      config.retry_config = {
          'max_attempts': 'maxAttempts',
          'max_retry_duration': 'maxRetryDuration',
      }
      config.retry_config_mask_prefix = 'retryConfig'
    elif queue_type == constants.PUSH_QUEUE:
      if release_track == base.ReleaseTrack.ALPHA:
        config.retry_config = {
            'max_attempts': 'maxAttempts',
            'max_retry_duration': 'maxRetryDuration',
            'max_doublings': 'maxDoublings',
            'min_backoff': 'minBackoff',
            'max_backoff': 'maxBackoff',
        }
        config.rate_limits = {
            'max_tasks_dispatched_per_second': 'maxTasksDispatchedPerSecond',
            'max_concurrent_tasks': 'maxConcurrentTasks',
        }
        config.app_engine_routing_override = {
            'routing_override': 'appEngineRoutingOverride',
        }
        config.retry_config_mask_prefix = 'retryConfig'
        config.rate_limits_mask_prefix = 'rateLimits'
        config.app_engine_routing_override_mask_prefix = 'appEngineHttpTarget'
      elif release_track == base.ReleaseTrack.BETA:
        config.retry_config = {
            'max_attempts': 'maxAttempts',
            'max_retry_duration': 'maxRetryDuration',
            'max_doublings': 'maxDoublings',
            'min_backoff': 'minBackoff',
            'max_backoff': 'maxBackoff',
        }
        config.rate_limits = {
            'max_dispatches_per_second': 'maxDispatchesPerSecond',
            'max_concurrent_dispatches': 'maxConcurrentDispatches',
        }
        config.app_engine_routing_override = {
            'routing_override': 'appEngineRoutingOverride',
        }
        config.stackdriver_logging_config = {
            'log_sampling_ratio': 'samplingRatio',
        }
        config.retry_config_mask_prefix = 'retryConfig'
        config.rate_limits_mask_prefix = 'rateLimits'
        config.app_engine_routing_override_mask_prefix = 'appEngineHttpQueue'
        config.stackdriver_logging_config_mask_prefix = 'stackdriverLoggingConfig'
      else:
        config.retry_config = {
            'max_attempts': 'maxAttempts',
            'max_retry_duration': 'maxRetryDuration',
            'max_doublings': 'maxDoublings',
            'min_backoff': 'minBackoff',
            'max_backoff': 'maxBackoff',
        }
        config.rate_limits = {
            'max_dispatches_per_second': 'maxDispatchesPerSecond',
            'max_concurrent_dispatches': 'maxConcurrentDispatches',
        }
        config.app_engine_routing_override = {
            'routing_override': 'appEngineRoutingOverride',
        }
        config.stackdriver_logging_config = {
            'log_sampling_ratio': 'samplingRatio',
        }
        config.retry_config_mask_prefix = 'retryConfig'
        config.rate_limits_mask_prefix = 'rateLimits'
        config.app_engine_routing_override_mask_prefix = ''
        config.stackdriver_logging_config_mask_prefix = 'stackdriverLoggingConfig'
    return config

  def _InitializedConfigsAndPrefixTuples(self):
    """Returns the initialized configs as a list of (config, prefix) tuples."""
    all_configs_and_prefixes = [
        (self.retry_config, self.retry_config_mask_prefix),
        (self.rate_limits, self.rate_limits_mask_prefix),
        (self.app_engine_routing_override,
         self.app_engine_routing_override_mask_prefix),
        (self.stackdriver_logging_config,
         self.stackdriver_logging_config_mask_prefix),
    ]
    return [(config, prefix)
            for (config, prefix) in all_configs_and_prefixes
            if config]

  def _GetSingleConfigToMaskMapping(self, config, prefix):
    """Build a map from each arg and its clear_ counterpart to a mask field."""
    fields_to_mask = dict()
    for field in config.keys():
      output_field = config[field]
      if prefix:
        fields_to_mask[field] = '{}.{}'.format(prefix, output_field)
      else:
        fields_to_mask[field] = output_field
      fields_to_mask[_EquivalentClearArg(field)] = fields_to_mask[field]
    return fields_to_mask

  def GetConfigToUpdateMaskMapping(self):
    """Builds mapping from config fields to corresponding update mask fields."""
    config_to_mask = dict()
    for (config, prefix) in self._InitializedConfigsAndPrefixTuples():
      config_to_mask.update(self._GetSingleConfigToMaskMapping(config, prefix))
    return config_to_mask

  def AllConfigs(self):
    return (list(self.retry_config.keys()) + list(self.rate_limits.keys()) +
            list(self.app_engine_routing_override.keys()) +
            list(self.stackdriver_logging_config.keys()))


def ParseProject():
  return resources.REGISTRY.Parse(
      _PROJECT(),
      collection=constants.PROJECTS_COLLECTION)


def ParseLocation(location):
  return resources.REGISTRY.Parse(
      location,
      params={'projectsId': _PROJECT},
      collection=constants.LOCATIONS_COLLECTION)


def ParseQueue(queue, location=None):
  """Parses an id or uri for a queue.

  Args:
    queue: An id, self-link, or relative path of a queue resource.
    location: The location of the app associated with the active project.

  Returns:
    A queue resource reference, or None if passed-in queue is Falsy.
  """
  if not queue:
    return None

  queue_ref = None
  try:
    queue_ref = resources.REGISTRY.Parse(queue,
                                         collection=constants.QUEUES_COLLECTION)
  except resources.RequiredFieldOmittedException:
    app_location = location or app.ResolveAppLocation(ParseProject())
    location_ref = ParseLocation(app_location)
    queue_ref = resources.REGISTRY.Parse(
        queue, params={'projectsId': location_ref.projectsId,
                       'locationsId': location_ref.locationsId},
        collection=constants.QUEUES_COLLECTION)
  return queue_ref


def ParseTask(task, queue_ref=None):
  """Parses an id or uri for a task."""
  params = queue_ref.AsDict() if queue_ref else None
  try:
    return resources.REGISTRY.Parse(task,
                                    collection=constants.TASKS_COLLECTION,
                                    params=params)
  except resources.RequiredFieldOmittedException:
    raise FullTaskUnspecifiedError(
        'Must specify either the fully qualified task path or the queue flag.')


def ExtractLocationRefFromQueueRef(queue_ref):
  params = queue_ref.AsDict()
  del params['queuesId']
  location_ref = resources.REGISTRY.Parse(
      None, params=params, collection=constants.LOCATIONS_COLLECTION)
  return location_ref


def ParseCreateOrUpdateQueueArgs(args,
                                 queue_type,
                                 messages,
                                 is_update=False,
                                 release_track=base.ReleaseTrack.GA):
  """Parses queue level args."""
  if release_track == base.ReleaseTrack.ALPHA:
    return messages.Queue(
        retryConfig=_ParseRetryConfigArgs(args, queue_type, messages,
                                          is_update, is_alpha=True),
        rateLimits=_ParseAlphaRateLimitsArgs(args, queue_type, messages,
                                             is_update),
        pullTarget=_ParsePullTargetArgs(args, queue_type, messages, is_update),
        appEngineHttpTarget=_ParseAppEngineHttpTargetArgs(
            args, queue_type, messages, is_update))
  elif release_track == base.ReleaseTrack.BETA:
    return messages.Queue(
        retryConfig=_ParseRetryConfigArgs(args, queue_type, messages,
                                          is_update, is_alpha=False),
        rateLimits=_ParseRateLimitsArgs(args, queue_type, messages, is_update),
        stackdriverLoggingConfig=_ParseStackdriverLoggingConfigArgs(
            args, queue_type, messages, is_update),
        appEngineHttpQueue=_ParseAppEngineHttpQueueArgs(args, queue_type,
                                                        messages, is_update))
  else:
    return messages.Queue(
        retryConfig=_ParseRetryConfigArgs(
            args, queue_type, messages, is_update, is_alpha=False),
        rateLimits=_ParseRateLimitsArgs(args, queue_type, messages, is_update),
        stackdriverLoggingConfig=_ParseStackdriverLoggingConfigArgs(
            args, queue_type, messages, is_update),
        appEngineRoutingOverride=_ParseAppEngineRoutingOverrideArgs(
            args, queue_type, messages, is_update))


def ParseCreateTaskArgs(args, task_type, messages,
                        release_track=base.ReleaseTrack.GA):
  """Parses task level args."""
  if release_track == base.ReleaseTrack.ALPHA:
    return messages.Task(
        scheduleTime=args.schedule_time,
        pullMessage=_ParsePullMessageArgs(args, task_type, messages),
        appEngineHttpRequest=_ParseAlphaAppEngineHttpRequestArgs(
            args, task_type, messages))
  else:
    return messages.Task(
        scheduleTime=args.schedule_time,
        appEngineHttpRequest=_ParseAppEngineHttpRequestArgs(args, task_type,
                                                            messages),
        httpRequest=_ParseHttpRequestArgs(args, task_type, messages))


def CheckUpdateArgsSpecified(args, queue_type,
                             release_track=base.ReleaseTrack.GA):
  """Verifies that args are valid for updating a queue."""
  updatable_config = QueueUpdatableConfiguration.FromQueueTypeAndReleaseTrack(
      queue_type, release_track)

  if _AnyArgsSpecified(args, updatable_config.AllConfigs(), clear_args=True):
    return
  raise NoFieldsSpecifiedError('Must specify at least one field to update.')


def GetSpecifiedFieldsMask(args, queue_type,
                           release_track=base.ReleaseTrack.GA):
  """Returns the mask fields to use with the given args."""
  updatable_config = QueueUpdatableConfiguration.FromQueueTypeAndReleaseTrack(
      queue_type, release_track)

  specified_args = _SpecifiedArgs(
      args, updatable_config.AllConfigs(), clear_args=True)

  args_to_mask = updatable_config.GetConfigToUpdateMaskMapping()

  return sorted(set([args_to_mask[arg] for arg in specified_args]))


def _SpecifiedArgs(specified_args_object, args_list, clear_args=False):
  """Returns the list of known arguments in the specified list."""
  clear_args_list = []
  if clear_args:
    clear_args_list = [_EquivalentClearArg(a) for a in args_list]
  return filter(specified_args_object.IsSpecified, args_list + clear_args_list)


def _AnyArgsSpecified(specified_args_object, args_list, clear_args=False):
  """Returns whether there are known arguments in the specified list."""
  return any(_SpecifiedArgs(specified_args_object, args_list, clear_args))


def _EquivalentClearArg(arg):
  return 'clear_{}'.format(arg)


def _ParseRetryConfigArgs(args, queue_type, messages, is_update,
                          is_alpha=False):
  """Parses the attributes of 'args' for Queue.retryConfig."""
  if (queue_type == constants.PULL_QUEUE and
      _AnyArgsSpecified(args, ['max_attempts', 'max_retry_duration'],
                        clear_args=is_update)):
    retry_config = messages.RetryConfig(
        maxRetryDuration=args.max_retry_duration)
    _AddMaxAttemptsFieldsFromArgs(args, retry_config, is_alpha)
    return retry_config

  if (queue_type == constants.PUSH_QUEUE and
      _AnyArgsSpecified(args, ['max_attempts', 'max_retry_duration',
                               'max_doublings', 'min_backoff', 'max_backoff'],
                        clear_args=is_update)):
    retry_config = messages.RetryConfig(
        maxRetryDuration=args.max_retry_duration,
        maxDoublings=args.max_doublings, minBackoff=args.min_backoff,
        maxBackoff=args.max_backoff)
    _AddMaxAttemptsFieldsFromArgs(args, retry_config, is_alpha)
    return retry_config


def _AddMaxAttemptsFieldsFromArgs(args, config_object, is_alpha=False):
  if args.IsSpecified('max_attempts'):
    # args.max_attempts is a BoundedInt and so None means unlimited
    if args.max_attempts is None:
      if is_alpha:
        config_object.unlimitedAttempts = True
      else:
        config_object.maxAttempts = -1
    else:
      config_object.maxAttempts = args.max_attempts


def _ParseAlphaRateLimitsArgs(args, queue_type, messages, is_update):
  """Parses the attributes of 'args' for Queue.rateLimits."""
  if (queue_type == constants.PUSH_QUEUE and
      _AnyArgsSpecified(args, ['max_tasks_dispatched_per_second',
                               'max_concurrent_tasks'],
                        clear_args=is_update)):
    return messages.RateLimits(
        maxTasksDispatchedPerSecond=args.max_tasks_dispatched_per_second,
        maxConcurrentTasks=args.max_concurrent_tasks)


def _ParseRateLimitsArgs(args, queue_type, messages, is_update):
  """Parses the attributes of 'args' for Queue.rateLimits."""
  if (queue_type == constants.PUSH_QUEUE and _AnyArgsSpecified(
      args, ['max_dispatches_per_second', 'max_concurrent_dispatches'],
      clear_args=is_update)):
    return messages.RateLimits(
        maxDispatchesPerSecond=args.max_dispatches_per_second,
        maxConcurrentDispatches=args.max_concurrent_dispatches)


def _ParseStackdriverLoggingConfigArgs(args, queue_type, messages, is_update):
  """Parses the attributes of 'args' for Queue.stackdriverLoggingConfig."""
  if (queue_type == constants.PUSH_QUEUE and _AnyArgsSpecified(
      args, ['log_sampling_ratio'], clear_args=is_update)):
    return messages.StackdriverLoggingConfig(
        samplingRatio=args.log_sampling_ratio)


def _ParsePullTargetArgs(unused_args, queue_type, messages, is_update):
  """Parses the attributes of 'args' for Queue.pullTarget."""
  if queue_type == constants.PULL_QUEUE and not is_update:
    return messages.PullTarget()


def _ParseAppEngineHttpTargetArgs(args, queue_type, messages, is_update):
  """Parses the attributes of 'args' for Queue.appEngineHttpTarget."""
  if queue_type == constants.PUSH_QUEUE:
    routing_override = _ParseAppEngineRoutingOverrideArgs(args, queue_type,
                                                          messages, is_update)
    return messages.AppEngineHttpTarget(
        appEngineRoutingOverride=routing_override)


def _ParseAppEngineHttpQueueArgs(args, queue_type, messages, is_update):
  """Parses the attributes of 'args' for Queue.appEngineHttpQueue."""
  if queue_type == constants.PUSH_QUEUE:
    routing_override = _ParseAppEngineRoutingOverrideArgs(args, queue_type,
                                                          messages, is_update)
    return messages.AppEngineHttpQueue(
        appEngineRoutingOverride=routing_override)


def _ParseAppEngineRoutingOverrideArgs(args, queue_type, messages, is_update):
  """Parses the attributes of 'args' for AppEngineRouting."""
  if queue_type == constants.PUSH_QUEUE:
    if args.IsSpecified('routing_override'):
      return messages.AppEngineRouting(**args.routing_override)
    elif is_update and args.IsSpecified('clear_routing_override'):
      return messages.AppEngineRouting()
    return None


def _ParsePullMessageArgs(args, task_type, messages):
  if task_type == constants.PULL_TASK:
    return messages.PullMessage(payload=_ParsePayloadArgs(args), tag=args.tag)


def _ParseAlphaAppEngineHttpRequestArgs(args, task_type, messages):
  """Parses the attributes of 'args' for Task.appEngineHttpRequest."""
  if task_type == constants.APP_ENGINE_TASK:
    routing = (
        messages.AppEngineRouting(**args.routing) if args.routing else None)
    http_method = (messages.AppEngineHttpRequest.HttpMethodValueValuesEnum(
        args.method.upper()) if args.IsSpecified('method') else None)
    return messages.AppEngineHttpRequest(
        appEngineRouting=routing, httpMethod=http_method,
        payload=_ParsePayloadArgs(args), relativeUrl=args.url,
        headers=_ParseHeaderArg(args,
                                messages.AppEngineHttpRequest.HeadersValue))


def _ParsePayloadArgs(args):
  if args.IsSpecified('payload_file'):
    payload = console_io.ReadFromFileOrStdin(args.payload_file, binary=False)
  elif args.IsSpecified('payload_content'):
    payload = args.payload_content
  else:
    return None
  return http_encoding.Encode(payload)


def _ParseAppEngineHttpRequestArgs(args, task_type, messages):
  """Parses the attributes of 'args' for Task.appEngineHttpRequest."""
  if task_type == constants.APP_ENGINE_TASK:
    routing = (
        messages.AppEngineRouting(**args.routing) if args.routing else None)
    http_method = (messages.AppEngineHttpRequest.HttpMethodValueValuesEnum(
        args.method.upper()) if args.IsSpecified('method') else None)
    return messages.AppEngineHttpRequest(
        appEngineRouting=routing, httpMethod=http_method,
        body=_ParseBodyArgs(args), relativeUri=args.relative_uri,
        headers=_ParseHeaderArg(args,
                                messages.AppEngineHttpRequest.HeadersValue))


def _ParseHttpRequestArgs(args, task_type, messages):
  """Parses the attributes of 'args' for Task.httpRequest."""
  if task_type == constants.HTTP_TASK:
    http_method = (messages.HttpRequest.HttpMethodValueValuesEnum(
        args.method.upper()) if args.IsSpecified('method') else None)
    return messages.HttpRequest(
        headers=_ParseHeaderArg(args, messages.HttpRequest.HeadersValue),
        httpMethod=http_method, body=_ParseBodyArgs(args), url=args.url,
        oauthToken=_ParseOAuthArgs(args, messages),
        oidcToken=_ParseOidcArgs(args, messages))


def _ParseBodyArgs(args):
  if args.IsSpecified('body_file'):
    body = console_io.ReadFromFileOrStdin(args.body_file, binary=False)
  elif args.IsSpecified('body_content'):
    body = args.body_content
  else:
    return None
  return http_encoding.Encode(body)


def _ParseOAuthArgs(args, messages):
  if args.IsSpecified('oauth_service_account_email'):
    return messages.OAuthToken(
        serviceAccountEmail=args.oauth_service_account_email,
        scope=args.oauth_token_scope)
  else:
    return None


def _ParseOidcArgs(args, messages):
  if args.IsSpecified('oidc_service_account_email'):
    return messages.OidcToken(
        serviceAccountEmail=args.oidc_service_account_email,
        audience=args.oidc_token_audience)
  else:
    return None


def _ParseHeaderArg(args, headers_value):
  if args.header:
    headers_dict = {k: v for k, v in map(_SplitHeaderArgValue, args.header)}
    return encoding.DictToAdditionalPropertyMessage(headers_dict, headers_value)


def _SplitHeaderArgValue(header_arg_value):
  key, value = header_arg_value.split(':', 1)
  return key, value.lstrip()


def FormatLeaseDuration(lease_duration):
  return '{}s'.format(lease_duration)


def ParseTasksLeaseFilterFlags(args):
  if args.oldest_tag:
    return 'tag_function=oldest_tag()'
  if args.IsSpecified('tag'):
    return 'tag="{}"'.format(args.tag)


def QueuesUriFunc(queue):
  return resources.REGISTRY.Parse(
      queue.name,
      params={'projectsId': _PROJECT},
      collection=constants.QUEUES_COLLECTION).SelfLink()


def TasksUriFunc(task):
  return resources.REGISTRY.Parse(
      task.name,
      params={'projectsId': _PROJECT},
      collection=constants.TASKS_COLLECTION).SelfLink()


def LocationsUriFunc(task):
  return resources.REGISTRY.Parse(
      task.name,
      params={'projectsId': _PROJECT},
      collection=constants.LOCATIONS_COLLECTION).SelfLink()
