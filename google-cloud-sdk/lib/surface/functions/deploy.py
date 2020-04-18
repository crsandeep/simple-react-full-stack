# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Creates or updates a Google Cloud Function."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding

from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.api_lib.functions import env_vars as env_vars_api_util
from googlecloudsdk.api_lib.functions import util as api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.functions import flags
from googlecloudsdk.command_lib.functions.deploy import env_vars_util
from googlecloudsdk.command_lib.functions.deploy import labels_util
from googlecloudsdk.command_lib.functions.deploy import source_util
from googlecloudsdk.command_lib.functions.deploy import trigger_util
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.args import labels_util as args_labels_util
from googlecloudsdk.command_lib.util.args import map_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io

from six.moves import urllib


def _ApplyEnvVarsArgsToFunction(function, args):
  updated_fields = []
  old_env_vars = env_vars_api_util.GetFunctionEnvVarsAsDict(function)
  env_var_flags = map_util.GetMapFlagsFromArgs('env-vars', args)
  new_env_vars = map_util.ApplyMapFlags(old_env_vars, **env_var_flags)
  if old_env_vars != new_env_vars:
    function.environmentVariables = env_vars_api_util.DictToEnvVarsProperty(
        new_env_vars)
    updated_fields.append('environmentVariables')
  return updated_fields


def _CreateBindPolicyCommand(function_name, region):
  template = ('gcloud alpha functions add-iam-policy-binding %s %s'
              '--member=allUsers --role=roles/cloudfunctions.invoker')
  region_flag = '--region=%s ' % region if region else ''
  return template % (function_name, region_flag)


def _CreateStackdriverURLforBuildLogs(build_id, project_id):
  query_param = ('resource.type=build\nresource.labels.build_id=%s\n'
                 'logName=projects/%s/logs/cloudbuild' % (build_id, project_id))
  return ('https://console.cloud.google.com/logs/viewer?'
          'project=%s&advancedFilter=%s' %
          (project_id, urllib.parse.quote(query_param, safe='')))  # pylint: disable=redundant-keyword-arg


def _GetProject(args):
  return args.project or properties.VALUES.core.project.Get(required=True)


def _Run(args,
         track=None,
         enable_runtime=True,
         enable_build_worker_pool=False):
  """Run a function deployment with the given args."""
  # Check for labels that start with `deployment`, which is not allowed.
  labels_util.CheckNoDeploymentLabels('--remove-labels', args.remove_labels)
  labels_util.CheckNoDeploymentLabels('--update-labels', args.update_labels)

  # Check that exactly one trigger type is specified properly.
  trigger_util.ValidateTriggerArgs(args.trigger_event, args.trigger_resource,
                                   args.IsSpecified('retry'),
                                   args.IsSpecified('trigger_http'))
  trigger_params = trigger_util.GetTriggerEventParams(args.trigger_http,
                                                      args.trigger_bucket,
                                                      args.trigger_topic,
                                                      args.trigger_event,
                                                      args.trigger_resource)

  function_ref = args.CONCEPTS.name.Parse()
  function_url = function_ref.RelativeName()

  messages = api_util.GetApiMessagesModule(track)

  # Get an existing function or create a new one.
  function = api_util.GetFunction(function_url)
  is_new_function = function is None
  had_vpc_connector = bool(
      function.vpcConnector) if not is_new_function else False
  if is_new_function:
    trigger_util.CheckTriggerSpecified(args)
    function = messages.CloudFunction()
    function.name = function_url
  elif trigger_params:
    # If the new deployment would implicitly change the trigger_event type
    # raise error
    trigger_util.CheckLegacyTriggerUpdate(function.eventTrigger,
                                          trigger_params['trigger_event'])

  # Keep track of which fields are updated in the case of patching.
  updated_fields = []

  # Populate function properties based on args.
  if args.entry_point:
    function.entryPoint = args.entry_point
    updated_fields.append('entryPoint')
  if args.timeout:
    function.timeout = '{}s'.format(args.timeout)
    updated_fields.append('timeout')
  if args.memory:
    function.availableMemoryMb = utils.BytesToMb(args.memory)
    updated_fields.append('availableMemoryMb')
  if args.service_account:
    function.serviceAccountEmail = args.service_account
    updated_fields.append('serviceAccountEmail')
  if (args.IsSpecified('max_instances') or
      args.IsSpecified('clear_max_instances')):
    max_instances = 0 if args.clear_max_instances else args.max_instances
    function.maxInstances = max_instances
    updated_fields.append('maxInstances')
  if enable_runtime:
    if args.IsSpecified('runtime'):
      function.runtime = args.runtime
      updated_fields.append('runtime')
      if args.runtime in ['nodejs6']:
        log.warning(
            'The Node.js 6 runtime is deprecated on Cloud Functions. '
            'Please migrate to Node.js 8 (--runtime=nodejs8) or Node.js 10 '
            '(--runtime=nodejs10). '
            'See https://cloud.google.com/functions/docs/migrating/nodejs-runtimes'
        )
    elif is_new_function:
      raise exceptions.RequiredArgumentException(
          'runtime', 'Flag `--runtime` is required for new functions.')
  if args.vpc_connector or args.clear_vpc_connector:
    function.vpcConnector = ('' if args.clear_vpc_connector else
                             args.vpc_connector)
    updated_fields.append('vpcConnector')
  if args.IsSpecified('egress_settings'):
    will_have_vpc_connector = ((had_vpc_connector and
                                not args.clear_vpc_connector) or
                               args.vpc_connector)
    if not will_have_vpc_connector:
      raise exceptions.RequiredArgumentException(
          'vpc-connector', 'Flag `--vpc-connector` is '
          'required for setting `egress-settings`.')
    egress_settings_enum = arg_utils.ChoiceEnumMapper(
        arg_name='egress_settings',
        message_enum=function.VpcConnectorEgressSettingsValueValuesEnum,
        custom_mappings=flags.EGRESS_SETTINGS_MAPPING).GetEnumForChoice(
            args.egress_settings)
    function.vpcConnectorEgressSettings = egress_settings_enum
    updated_fields.append('vpcConnectorEgressSettings')
  if args.IsSpecified('ingress_settings'):
    ingress_settings_enum = arg_utils.ChoiceEnumMapper(
        arg_name='ingress_settings',
        message_enum=function.IngressSettingsValueValuesEnum,
        custom_mappings=flags.INGRESS_SETTINGS_MAPPING).GetEnumForChoice(
            args.ingress_settings)
    function.ingressSettings = ingress_settings_enum
    updated_fields.append('ingressSettings')
  if enable_build_worker_pool:
    if args.build_worker_pool or args.clear_build_worker_pool:
      function.buildWorkerPool = ('' if args.clear_build_worker_pool else
                                  args.build_worker_pool)
      updated_fields.append('buildWorkerPool')
  # Populate trigger properties of function based on trigger args.
  if args.trigger_http:
    function.httpsTrigger = messages.HttpsTrigger()
    function.eventTrigger = None
    updated_fields.extend(['eventTrigger', 'httpsTrigger'])
  if trigger_params:
    function.eventTrigger = trigger_util.CreateEventTrigger(**trigger_params)
    function.httpsTrigger = None
    updated_fields.extend(['eventTrigger', 'httpsTrigger'])
  if args.IsSpecified('retry'):
    updated_fields.append('eventTrigger.failurePolicy')
    if args.retry:
      function.eventTrigger.failurePolicy = messages.FailurePolicy()
      function.eventTrigger.failurePolicy.retry = messages.Retry()
    else:
      function.eventTrigger.failurePolicy = None
  elif function.eventTrigger:
    function.eventTrigger.failurePolicy = None

  # Populate source properties of function based on source args.
  # Only Add source to function if its explicitly provided, a new function,
  # using a stage bucket or deploy of an existing function that previously
  # used local source.
  if (args.source or args.stage_bucket or is_new_function or
      function.sourceUploadUrl):
    updated_fields.extend(
        source_util.SetFunctionSourceProps(function, function_ref, args.source,
                                           args.stage_bucket, args.ignore_file))

  # Apply label args to function
  if labels_util.SetFunctionLabels(function, args.update_labels,
                                   args.remove_labels, args.clear_labels):
    updated_fields.append('labels')

  # Apply environment variables args to function
  updated_fields.extend(_ApplyEnvVarsArgsToFunction(function, args))

  ensure_all_users_invoke = flags.ShouldEnsureAllUsersInvoke(args)
  deny_all_users_invoke = flags.ShouldDenyAllUsersInvoke(args)

  if is_new_function:
    if (not ensure_all_users_invoke and not deny_all_users_invoke and
        api_util.CanAddFunctionIamPolicyBinding(_GetProject(args))):
      ensure_all_users_invoke = console_io.PromptContinue(
          prompt_string=(
              'Allow unauthenticated invocations of new function [{}]?'.format(
                  args.NAME)),
          default=False)

    op = api_util.CreateFunction(function, function_ref.Parent().RelativeName())
    if (not ensure_all_users_invoke and not deny_all_users_invoke):
      template = ('Function created with limited-access IAM policy. '
                  'To enable unauthorized access consider "%s"')
      log.warning(template % _CreateBindPolicyCommand(args.NAME, args.region))
      deny_all_users_invoke = True

  elif updated_fields:
    op = api_util.PatchFunction(function, updated_fields)

  else:
    op = None  # Nothing to wait for
    if not ensure_all_users_invoke and not deny_all_users_invoke:
      log.status.Print('Nothing to update.')
      return

  stop_trying_perm_set = [False]

  # The server asyncrhonously sets allUsers invoker permissions some time after
  # we create the function. That means, to remove it, we need do so after the
  # server adds it. We can remove this mess after the default changes.
  # TODO(b/139026575): Remove the "remove" path, only bother adding. Remove the
  # logic from the polling loop. Remove the ability to add logic like this to
  # the polling loop.
  def TryToSetInvokerPermission():
    """Try to make the invoker permission be what we said it should.

    This is for executing in the polling loop, and will stop trying as soon as
    it succeeds at making a change.
    """
    if stop_trying_perm_set[0]:
      return
    try:
      if ensure_all_users_invoke:
        api_util.AddFunctionIamPolicyBinding(function.name)
        stop_trying_perm_set[0] = True
      elif deny_all_users_invoke:
        stop_trying_perm_set[0] = (
            api_util.RemoveFunctionIamPolicyBindingIfFound(function.name))
    except exceptions.HttpException:
      stop_trying_perm_set[0] = True
      log.warning('Setting IAM policy failed, try "%s"' %
                  _CreateBindPolicyCommand(args.NAME, args.region))

  log_stackdriver_url = [True]

  def TryToLogStackdriverURL(op):
    """Logs stackdriver URL.

    This is for executing in the polling loop, and will stop trying as soon as
    it succeeds at making a change.

    Args:
      op: the operation
    """
    if log_stackdriver_url[0] and op.metadata:
      metadata = encoding.PyValueToMessage(
          messages.OperationMetadataV1, encoding.MessageToPyValue(op.metadata))
      if metadata.buildId:
        sd_info_template = '\nFor Cloud Build Stackdriver Logs, visit: %s'
        log.status.Print(sd_info_template %
                         _CreateStackdriverURLforBuildLogs(metadata.buildId,
                                                           _GetProject(args)))
        log_stackdriver_url[0] = False

  if op:
    api_util.WaitForFunctionUpdateOperation(
        op, try_set_invoker=TryToSetInvokerPermission,
        on_every_poll=[TryToLogStackdriverURL])
  return api_util.GetFunction(function.name)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Deploy(base.Command):
  """Create or update a Google Cloud Function."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddMaxInstancesFlag(parser)
    flags.AddFunctionResourceArg(parser, 'to deploy')
    # Add args for function properties
    flags.AddFunctionMemoryFlag(parser)
    flags.AddFunctionTimeoutFlag(parser)
    flags.AddFunctionRetryFlag(parser)
    args_labels_util.AddUpdateLabelsFlags(
        parser,
        extra_update_message=labels_util.NO_LABELS_STARTING_WITH_DEPLOY_MESSAGE,
        extra_remove_message=labels_util.NO_LABELS_STARTING_WITH_DEPLOY_MESSAGE)

    flags.AddServiceAccountFlag(parser)
    flags.AddAllowUnauthenticatedFlag(parser)

    # Add args for specifying the function source code
    flags.AddSourceFlag(parser)
    flags.AddStageBucketFlag(parser)
    flags.AddEntryPointFlag(parser)

    # Add args for specifying the function trigger
    flags.AddTriggerFlagGroup(parser)

    flags.AddRuntimeFlag(parser)

    # Add args for specifying environment variables
    env_vars_util.AddUpdateEnvVarsFlags(parser)

    # Add args for specifying ignore files to upload source
    flags.AddIgnoreFileFlag(parser)

    flags.AddVPCConnectorMutexGroup(parser)
    flags.AddEgressSettingsFlag(parser)
    flags.AddIngressSettingsFlag(parser)

  def Run(self, args):
    return _Run(args, track=self.ReleaseTrack())


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DeployBeta(base.Command):
  """Create or update a Google Cloud Function."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    Deploy.Args(parser)

  def Run(self, args):
    return _Run(args, track=self.ReleaseTrack())


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DeployAlpha(base.Command):
  """Create or update a Google Cloud Function."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    Deploy.Args(parser)
    flags.AddBuildWorkerPoolMutexGroup(parser)

  def Run(self, args):
    return _Run(
        args,
        track=self.ReleaseTrack(),
        enable_build_worker_pool=True)
