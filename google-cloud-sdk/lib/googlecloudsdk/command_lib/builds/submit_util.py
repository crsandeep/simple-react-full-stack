# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Support library to handle the build submit."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os.path
import uuid

from apitools.base.py import encoding
from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.api_lib.cloudbuild import config
from googlecloudsdk.api_lib.cloudbuild import logs as cb_logs
from googlecloudsdk.api_lib.cloudbuild import snapshot
from googlecloudsdk.api_lib.compute import utils as compute_utils
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.calliope import exceptions as c_exceptions
from googlecloudsdk.command_lib.builds import flags
from googlecloudsdk.command_lib.builds import staging_bucket_util
from googlecloudsdk.command_lib.cloudbuild import execution
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.resource import resource_transform
from googlecloudsdk.core.util import times
import six

_ALLOWED_SOURCE_EXT = ['.zip', '.tgz', '.gz']

_DEFAULT_BUILDPACK_BUILDER = 'gcr.io/buildpacks/builder'

_SUPPORTED_REGISTRIES = ['gcr.io', 'pkg.dev']


class FailedBuildException(core_exceptions.Error):
  """Exception for builds that did not succeed."""

  def __init__(self, build):
    super(FailedBuildException,
          self).__init__('build {id} completed with status "{status}"'.format(
              id=build.id, status=build.status))


def _GetBuildTimeout():
  """Get the build timeout."""
  build_timeout = properties.VALUES.builds.timeout.Get()
  if build_timeout is not None:
    try:
      # A bare number is interpreted as seconds.
      build_timeout_secs = int(build_timeout)
    except ValueError:
      build_timeout_duration = times.ParseDuration(build_timeout)
      build_timeout_secs = int(build_timeout_duration.total_seconds)
    timeout_str = six.text_type(build_timeout_secs) + 's'
  else:
    timeout_str = None

  return timeout_str


def _SetBuildSteps(tag, no_cache, messages, substitutions, arg_config,
                   timeout_str):
  """Set build steps."""
  if tag is not None:
    if (properties.VALUES.builds.check_tag.GetBool() and
        not any(reg in tag for reg in _SUPPORTED_REGISTRIES)):
      raise c_exceptions.InvalidArgumentException(
          '--tag', 'Tag value must be in the gcr.io/*, *.gcr.io/*, '
                   'or *.pkg.dev/* namespace.')
    if properties.VALUES.builds.use_kaniko.GetBool():
      if no_cache:
        ttl = '0h'
      else:
        ttl = '{}h'.format(properties.VALUES.builds.kaniko_cache_ttl.Get())
      build_config = messages.Build(
          steps=[
              messages.BuildStep(
                  name=properties.VALUES.builds.kaniko_image.Get(),
                  args=[
                      '--destination',
                      tag,
                      '--cache',
                      '--cache-ttl',
                      ttl,
                      '--cache-dir',
                      '',
                  ],
              ),
          ],
          timeout=timeout_str,
          substitutions=cloudbuild_util.EncodeSubstitutions(
              substitutions, messages))
    else:
      if no_cache:
        raise c_exceptions.InvalidArgumentException(
            'no-cache',
            'Cannot specify --no-cache if builds/use_kaniko property is '
            'False')
      build_config = messages.Build(
          images=[tag],
          steps=[
              messages.BuildStep(
                  name='gcr.io/cloud-builders/docker',
                  args=[
                      'build', '--network', 'cloudbuild', '--no-cache', '-t',
                      tag, '.'
                  ],
              ),
          ],
          timeout=timeout_str,
          substitutions=cloudbuild_util.EncodeSubstitutions(
              substitutions, messages))
  elif arg_config is not None:
    if no_cache:
      raise c_exceptions.ConflictingArgumentsException('--config', '--no-cache')
    if not arg_config:
      raise c_exceptions.InvalidArgumentException(
          '--config', 'Config file path must not be empty.')
    build_config = config.LoadCloudbuildConfigFromPath(
        arg_config, messages, params=substitutions)
  else:
    raise c_exceptions.OneOfArgumentsRequiredException(
        ['--tag', '--config'], 'Requires either a docker tag or a config file.')

  # If timeout was set by flag, overwrite the config file.
  if timeout_str:
    build_config.timeout = timeout_str

  return build_config


def _SetBuildStepsAlpha(tag, no_cache, messages, substitutions, arg_config,
                        timeout_str, buildpack):
  """Set build steps."""
  if tag is not None:
    if (properties.VALUES.builds.check_tag.GetBool() and
        not any(reg in tag for reg in _SUPPORTED_REGISTRIES)):
      raise c_exceptions.InvalidArgumentException(
          '--tag', 'Tag value must be in the gcr.io/*, *.gcr.io/*, '
          'or *.pkg.dev/* namespace.')
    if properties.VALUES.builds.use_kaniko.GetBool():
      if no_cache:
        ttl = '0h'
      else:
        ttl = '{}h'.format(properties.VALUES.builds.kaniko_cache_ttl.Get())
      build_config = messages.Build(
          steps=[
              messages.BuildStep(
                  name=properties.VALUES.builds.kaniko_image.Get(),
                  args=[
                      '--destination',
                      tag,
                      '--cache',
                      '--cache-ttl',
                      ttl,
                      '--cache-dir',
                      '',
                  ],
              ),
          ],
          timeout=timeout_str,
          substitutions=cloudbuild_util.EncodeSubstitutions(
              substitutions, messages))
    else:
      if no_cache:
        raise c_exceptions.InvalidArgumentException(
            'no-cache',
            'Cannot specify --no-cache if builds/use_kaniko property is '
            'False')
      build_config = messages.Build(
          images=[tag],
          steps=[
              messages.BuildStep(
                  name='gcr.io/cloud-builders/docker',
                  args=[
                      'build', '--network', 'cloudbuild', '--no-cache', '-t',
                      tag, '.'
                  ],
              ),
          ],
          timeout=timeout_str,
          substitutions=cloudbuild_util.EncodeSubstitutions(
              substitutions, messages))
  elif buildpack is not None:
    if not buildpack:
      raise c_exceptions.InvalidArgumentException(
          '--pack', 'Image value must not be empty.')
    if buildpack[0].get('builder') is None:
      builder = _DEFAULT_BUILDPACK_BUILDER
    else:
      builder = buildpack[0].get('builder')
    if buildpack[0].get('image') is None:
      raise c_exceptions.InvalidArgumentException(
          '--pack', 'Image value must not be empty.')
    image = buildpack[0].get('image')
    if (properties.VALUES.builds.check_tag.GetBool() and
        not any(reg in image for reg in _SUPPORTED_REGISTRIES)):
      raise c_exceptions.InvalidArgumentException(
          '--pack',
          'Image value must be in the gcr.io/*, *.gcr.io/*, or *.pkg.dev/* namespace.'
      )
    env = buildpack[0].get('env')
    pack_args = ['build', image, '--builder', builder]
    if env is not None:
      pack_args.append('--env')
      pack_args.append(env)
    build_config = messages.Build(
        images=[image],
        steps=[
            messages.BuildStep(
                name='gcr.io/k8s-skaffold/pack',
                entrypoint='pack',
                args=pack_args,
            ),
        ],
        timeout=timeout_str,
        substitutions=cloudbuild_util.EncodeSubstitutions(
            substitutions, messages))
  elif arg_config is not None:
    if no_cache:
      raise c_exceptions.ConflictingArgumentsException('--config', '--no-cache')
    if not arg_config:
      raise c_exceptions.InvalidArgumentException(
          '--config', 'Config file path must not be empty.')
    build_config = config.LoadCloudbuildConfigFromPath(
        arg_config, messages, params=substitutions)
  else:
    raise c_exceptions.OneOfArgumentsRequiredException(
        ['--tag', '--config', '--pack'],
        'Requires either a docker tag, a config file, or pack argument.')

  # If timeout was set by flag, overwrite the config file.
  if timeout_str:
    build_config.timeout = timeout_str

  return build_config


def _SetSource(build_config, messages, is_specified_source, no_source, source,
               gcs_source_staging_dir, ignore_file):
  """Set the source for the build config."""
  default_gcs_source = False
  default_bucket_name = None
  if gcs_source_staging_dir is None:
    default_gcs_source = True
    default_bucket_name = staging_bucket_util.GetDefaultStagingBucket()
    gcs_source_staging_dir = 'gs://{}/source'.format(default_bucket_name)
  gcs_client = storage_api.StorageClient()

  # --no-source overrides the default --source.
  if not is_specified_source and no_source:
    source = None

  gcs_source_staging = None
  if source:
    suffix = '.tgz'
    if source.startswith('gs://') or os.path.isfile(source):
      _, suffix = os.path.splitext(source)

    # Next, stage the source to Cloud Storage.
    staged_object = '{stamp}-{uuid}{suffix}'.format(
        stamp=times.GetTimeStampFromDateTime(times.Now()),
        uuid=uuid.uuid4().hex,
        suffix=suffix,
    )
    gcs_source_staging_dir = resources.REGISTRY.Parse(
        gcs_source_staging_dir, collection='storage.objects')

    # We create the bucket (if it does not exist) first. If we do an existence
    # check and then create the bucket ourselves, it would be possible for an
    # attacker to get lucky and beat us to creating the bucket. Block on this
    # creation to avoid this race condition.
    gcs_client.CreateBucketIfNotExists(gcs_source_staging_dir.bucket)

    # If no bucket is specified (for the source `default_gcs_source`), check
    # that the default bucket is also owned by the project (b/33046325).
    if default_gcs_source and not staging_bucket_util.BucketIsInProject(
        gcs_client, default_bucket_name):
      raise c_exceptions.RequiredArgumentException(
          'gcs-source-staging-dir',
          'A bucket with name {} already exists and is owned by '
          'another project. Specify a bucket using '
          '--gcs-source-staging-dir.'.format(default_bucket_name))

    if gcs_source_staging_dir.object:
      staged_object = gcs_source_staging_dir.object + '/' + staged_object
    gcs_source_staging = resources.REGISTRY.Create(
        collection='storage.objects',
        bucket=gcs_source_staging_dir.bucket,
        object=staged_object)

    if source.startswith('gs://'):
      gcs_source = resources.REGISTRY.Parse(
          source, collection='storage.objects')
      staged_source_obj = gcs_client.Rewrite(gcs_source, gcs_source_staging)
      build_config.source = messages.Source(
          storageSource=messages.StorageSource(
              bucket=staged_source_obj.bucket,
              object=staged_source_obj.name,
              generation=staged_source_obj.generation,
          ))
    else:
      if not os.path.exists(source):
        raise c_exceptions.BadFileException(
            'could not find source [{src}]'.format(src=source))
      if os.path.isdir(source):
        source_snapshot = snapshot.Snapshot(source, ignore_file=ignore_file)
        size_str = resource_transform.TransformSize(
            source_snapshot.uncompressed_size)
        log.status.Print(
            'Creating temporary tarball archive of {num_files} file(s)'
            ' totalling {size} before compression.'.format(
                num_files=len(source_snapshot.files), size=size_str))
        staged_source_obj = source_snapshot.CopyTarballToGCS(
            gcs_client, gcs_source_staging, ignore_file=ignore_file)
        build_config.source = messages.Source(
            storageSource=messages.StorageSource(
                bucket=staged_source_obj.bucket,
                object=staged_source_obj.name,
                generation=staged_source_obj.generation,
            ))
      elif os.path.isfile(source):
        unused_root, ext = os.path.splitext(source)
        if ext not in _ALLOWED_SOURCE_EXT:
          raise c_exceptions.BadFileException('Local file [{src}] is none of ' +
                                              ', '.join(_ALLOWED_SOURCE_EXT))
        log.status.Print('Uploading local file [{src}] to '
                         '[gs://{bucket}/{object}].'.format(
                             src=source,
                             bucket=gcs_source_staging.bucket,
                             object=gcs_source_staging.object,
                         ))
        staged_source_obj = gcs_client.CopyFileToGCS(source, gcs_source_staging)
        build_config.source = messages.Source(
            storageSource=messages.StorageSource(
                bucket=staged_source_obj.bucket,
                object=staged_source_obj.name,
                generation=staged_source_obj.generation,
            ))
  else:
    # No source
    if not no_source:
      raise c_exceptions.InvalidArgumentException(
          '--no-source', 'To omit source, use the --no-source flag.')

  return build_config


def _SetLogsBucket(build_config, arg_gcs_log_dir):
  """Set a Google Cloud Storage directory to hold build logs."""
  if arg_gcs_log_dir:
    gcs_log_dir = resources.REGISTRY.Parse(
        arg_gcs_log_dir, collection='storage.objects')
    build_config.logsBucket = ('gs://' + gcs_log_dir.bucket + '/' +
                               gcs_log_dir.object)

  return build_config


def _SetMachineType(build_config, messages, arg_machine_type):
  """Set the machine type used to run the build."""
  if arg_machine_type is not None:
    machine_type = flags.GetMachineType(arg_machine_type)
    if not build_config.options:
      build_config.options = messages.BuildOptions()
    build_config.options.machineType = machine_type

  return build_config


def _SetDiskSize(build_config, messages, arg_disk_size):
  """Set the disk size used to run the build."""
  if arg_disk_size is not None:
    disk_size = compute_utils.BytesToGb(arg_disk_size)
    if not build_config.options:
      build_config.options = messages.BuildOptions()
    build_config.options.diskSizeGb = int(disk_size)

  return build_config


def CreateBuildConfig(tag, no_cache, messages, substitutions, arg_config,
                      is_specified_source, no_source, source,
                      gcs_source_staging_dir, ignore_file, arg_gcs_log_dir,
                      arg_machine_type, arg_disk_size):
  """Returns a build config."""

  timeout_str = _GetBuildTimeout()
  build_config = _SetBuildSteps(tag, no_cache, messages, substitutions,
                                arg_config, timeout_str)
  build_config = _SetSource(build_config, messages, is_specified_source,
                            no_source, source, gcs_source_staging_dir,
                            ignore_file)
  build_config = _SetLogsBucket(build_config, arg_gcs_log_dir)
  build_config = _SetMachineType(build_config, messages, arg_machine_type)
  build_config = _SetDiskSize(build_config, messages, arg_disk_size)

  return build_config


def CreateBuildConfigAlpha(tag, no_cache, messages, substitutions, arg_config,
                           is_specified_source, no_source, source,
                           gcs_source_staging_dir, ignore_file, arg_gcs_log_dir,
                           arg_machine_type, arg_disk_size, buildpack):
  """Returns a build config."""
  timeout_str = _GetBuildTimeout()

  build_config = _SetBuildStepsAlpha(tag, no_cache, messages, substitutions,
                                     arg_config, timeout_str, buildpack)
  build_config = _SetSource(build_config, messages, is_specified_source,
                            no_source, source, gcs_source_staging_dir,
                            ignore_file)
  build_config = _SetLogsBucket(build_config, arg_gcs_log_dir)
  build_config = _SetMachineType(build_config, messages, arg_machine_type)
  build_config = _SetDiskSize(build_config, messages, arg_disk_size)

  return build_config


def Build(messages, async_, build_config, show_logs=False):
  """Starts the build."""
  log.debug('submitting build: ' + repr(build_config))
  client = cloudbuild_util.GetClientInstance()
  op = client.projects_builds.Create(
      messages.CloudbuildProjectsBuildsCreateRequest(
          build=build_config, projectId=properties.VALUES.core.project.Get()))
  json = encoding.MessageToJson(op.metadata)
  build = encoding.JsonToMessage(messages.BuildOperationMetadata, json).build

  build_ref = resources.REGISTRY.Create(
      collection='cloudbuild.projects.builds',
      projectId=build.projectId,
      id=build.id)

  if not show_logs:
    log.CreatedResource(build_ref)
    if build.logUrl:
      log.status.Print(
          'Logs are available at [{log_url}].'.format(log_url=build.logUrl))
    else:
      log.status.Print('Logs are available in the Cloud Console.')

  # If the command is run --async, we just print out a reference to the build.
  if async_:
    return build, op

  mash_handler = execution.MashHandler(
      execution.GetCancelBuildHandler(client, messages, build_ref))

  # Otherwise, logs are streamed from GCS.
  with execution_utils.CtrlCSection(mash_handler):
    build = cb_logs.CloudBuildClient(client, messages).Stream(build_ref)

  if build.status == messages.Build.StatusValueValuesEnum.TIMEOUT:
    log.status.Print(
        'Your build timed out. Use the [--timeout=DURATION] flag to change '
        'the timeout threshold.')

  if build.status != messages.Build.StatusValueValuesEnum.SUCCESS:
    raise FailedBuildException(build)

  return build, op
