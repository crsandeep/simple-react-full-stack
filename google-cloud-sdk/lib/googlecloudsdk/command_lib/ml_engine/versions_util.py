# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Utilities for ml versions commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ml_engine import versions_api
from googlecloudsdk.command_lib.ml_engine import models_util
from googlecloudsdk.command_lib.ml_engine import uploads
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.util.args import repeated
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io


class InvalidArgumentCombinationError(exceptions.Error):
  """Indicates that a given combination of arguments was invalid."""
  pass


def ParseCreateLabels(client, args):
  return labels_util.ParseCreateArgs(args, client.version_class.LabelsValue)


def ParseUpdateLabels(client, get_result, args):
  return labels_util.ProcessUpdateArgsLazy(
      args, client.version_class.LabelsValue, get_result.GetAttrThunk('labels'))


def ParseVersion(model, version):
  """Parses a model/version ID into a version resource object."""
  return resources.REGISTRY.Parse(
      version,
      params={
          'projectsId': properties.VALUES.core.project.GetOrFail,
          'modelsId': model
      },
      collection='ml.projects.models.versions')


def WaitForOpMaybe(operations_client, op, asyncronous=False, message=None):
  """Waits for an operation if asyncronous flag is on.

  Args:
    operations_client: api_lib.ml_engine.operations.OperationsClient, the client
      via which to poll
    op: Cloud ML Engine operation, the operation to poll
    asyncronous: bool, whether to wait for the operation or return immediately
    message: str, the message to display while waiting for the operation

  Returns:
    The result of the operation if asyncronous is true, or the Operation message
        otherwise
  """
  if asyncronous:
    return op
  return operations_client.WaitForOperation(op, message=message).response


def Create(versions_client, operations_client, version_id,
           model=None, origin=None, staging_bucket=None, runtime_version=None,
           config_file=None, asyncronous=None, labels=None, machine_type=None,
           description=None, framework=None, python_version=None,
           prediction_class=None, package_uris=None, accelerator_config=None,
           service_account=None, explanation_method=None,
           num_integral_steps=None, num_paths=None):
  """Create a version, optionally waiting for creation to finish."""
  if origin:
    try:
      origin = uploads.UploadDirectoryIfNecessary(origin, staging_bucket)
    except uploads.MissingStagingBucketException:
      raise InvalidArgumentCombinationError(
          'If --origin is provided as a local path, --staging-bucket must be '
          'given as well.')
  if explanation_method is not None:
    log.status.Print(
        'Explanations reflect patterns in your model, but don\'t necessarily '
        'reveal fundamental relationships about your data population. See '
        'https://cloud.google.com/ml-engine/docs/ai-explanations/limitations '
        'for more information.')

  model_ref = models_util.ParseModel(model)
  version = versions_client.BuildVersion(version_id,
                                         path=config_file,
                                         deployment_uri=origin,
                                         runtime_version=runtime_version,
                                         labels=labels,
                                         description=description,
                                         machine_type=machine_type,
                                         framework=framework,
                                         python_version=python_version,
                                         package_uris=package_uris,
                                         prediction_class=prediction_class,
                                         accelerator_config=accelerator_config,
                                         service_account=service_account,
                                         explanation_method=explanation_method,
                                         num_integral_steps=num_integral_steps,
                                         num_paths=num_paths)
  if not version.deploymentUri:
    raise InvalidArgumentCombinationError(
        'Either `--origin` must be provided or `deploymentUri` must be '
        'provided in the file given by `--config`.')
  op = versions_client.Create(model_ref, version)
  return WaitForOpMaybe(
      operations_client, op, asyncronous=asyncronous,
      message='Creating version (this might take a few minutes)...')


def Delete(versions_client, operations_client, version, model=None):
  version_ref = ParseVersion(model, version)
  console_io.PromptContinue(
      'This will delete version [{}]...'.format(version_ref.versionsId),
      cancel_on_no=True)
  op = versions_client.Delete(version_ref)
  return WaitForOpMaybe(
      operations_client, op, asyncronous=False,
      message='Deleting version [{}]...'.format(version_ref.versionsId))


def Describe(versions_client, version, model=None):
  version_ref = ParseVersion(model, version)
  return versions_client.Get(version_ref)


def List(versions_client, model=None):
  model_ref = models_util.ParseModel(model)
  return versions_client.List(model_ref)


def Update(versions_client, operations_client, version_ref, args):
  """Update the given version."""
  get_result = repeated.CachedResult.FromFunc(
      versions_client.Get, version_ref)
  labels_update = ParseUpdateLabels(versions_client, get_result, args)
  all_args = ['update_labels', 'clear_labels', 'remove_labels', 'description']

  try:
    op = versions_client.Patch(version_ref, labels_update, args.description)
  except versions_api.NoFieldsSpecifiedError:
    if not any(args.IsSpecified(arg) for arg in all_args):
      raise
    log.status.Print('No update to perform.')
    return None
  else:
    return operations_client.WaitForOperation(
        op, message='Updating version [{}]'.format(version_ref.Name())).response


def SetDefault(versions_client, version, model=None):
  version_ref = ParseVersion(model, version)
  return versions_client.SetDefault(version_ref)


def ValidateFrameworkAndMachineTypeGa(framework, machine_type):
  frameworks_enum = (
      versions_api.GetMessagesModule().GoogleCloudMlV1Version
      .FrameworkValueValuesEnum)
  if (framework != frameworks_enum.TENSORFLOW and
      not machine_type.startswith('ml')):
    raise InvalidArgumentCombinationError(
        'Machine type {0} is currently only supported with tensorflow.'.format(
            machine_type))
