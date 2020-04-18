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
"""Build and deploy to Google Kubernetes Engine command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os.path
import uuid

from apitools.base.py import encoding
from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.api_lib.cloudbuild import logs as cb_logs
from googlecloudsdk.api_lib.cloudbuild import snapshot
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exceptions
from googlecloudsdk.command_lib.builds import staging_bucket_util
from googlecloudsdk.command_lib.builds.deploy import build_util
from googlecloudsdk.command_lib.builds.deploy import git
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


class FailedDeployException(core_exceptions.Error):
  """Exception for builds that did not succeed."""

  def __init__(self, build):
    super(FailedDeployException, self).__init__(
        'failed to build or deploy: build {id} completed with status "{status}"'
        .format(id=build.id, status=build.status))


class DeployGKE(base.Command):
  """Build and deploy to a target Google Kubernetes Engine cluster."""

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
    """
    source = parser.add_mutually_exclusive_group()
    source.add_argument(
        'source',
        nargs='?',
        default='.',  # By default, the current directory is used.
        help='Location of the source and configs to build and deploy. '
        'The location can be a directory on a local disk or a '
        'gzipped archive file (.tar.gz) in Google Cloud Storage.')
    source.add_argument(
        '--no-source',
        action='store_true',
        help='Specify that no source should be uploaded with this build.')

    docker = parser.add_mutually_exclusive_group(
        help="""
        Image to use to build and/or deploy.

        To build an image with a default tag, omit these flags. The resulting
        tag will be in the format 'gcr.io/[PROJECT_ID]/[IMAGE]/[TAG], where
        [PROJECT_ID] is your project ID, [IMAGE] is the value provided by
        `--app-name`, if provided, else it is the name of the provided source
        directory, and [TAG] is the value provided by `--app-version`, if
        provided, else it is the commit SHA of your provided source.

        """)
    docker.add_argument(
        '--tag',
        help="""
        Tag to use with a 'docker build' image creation. Cloud Build runs a
        remote 'docker build -t $TAG .' command, where $TAG is the tag provided
        by this flag. The tag must be in the gcr.io/* or *.gcr.io/* namespaces.
        If you specify a tag in this command, your source must include a
        Dockerfile. For instructions on building using a Dockerfile see
        https://cloud.google.com/cloud-build/docs/quickstart-docker.
        """)
    docker.add_argument(
        '--image',
        help='Existing container image to deploy. If set, Cloud Build deploys '
        'the container image to the target Kubernetes cluster. The image must '
        'be in the gcr.io/* or *.gcr.io/* namespaces.')

    parser.add_argument(
        '--gcs-staging-dir',
        help="""
        Path to the Google Cloud Storage subdirectory into which to copy the
        source and configs (suggested base and expanded Kubernetes YAML files)
        that are used to stage and deploy your app. If the bucket in this path
        doesn't exist, Cloud Build creates it.

        If this field is not set, the source and configs are written to
        ```gs://[PROJECT_ID]_cloudbuild/deploy```, where source is written to
        the 'source' sub-directory and configs are written to the 'config'
        sub-directory.
        """)
    parser.add_argument(
        '--app-name',
        help='If specified, the following label is added to the Kubernetes '
        "manifests: 'app.kubernetes.io/name: APP_NAME'. Defaults to the "
        'container image name provided by `--image` or `--tag` without the tag, '
        "e.g. 'my-app' for 'gcr.io/my-project/my-app:1.0.0'.")
    parser.add_argument(
        '--app-version',
        help='If specified, the following label is added to the Kubernetes '
        "manifests: 'app.kubernetes.io/version: APP_VERSION'. Defaults to the "
        'container image tag provided by `--image` or `--tag`. If no image tag '
        'is provided and `SOURCE` is a valid git repository, defaults to the '
        'short revision hash of the HEAD commit.')
    parser.add_argument(
        '--cluster',
        help='Name of the target cluster to deploy to.',
        required=True)
    parser.add_argument(
        '--location',
        help='Region or zone of the target cluster to deploy to.',
        required=True)
    parser.add_argument(
        '--namespace',
        help='Namespace of the target cluster to deploy to. If this field is '
        "not set, the 'default' namespace is used.")
    parser.add_argument(
        '--config',
        help="""
        Path to the Kubernetes YAML, or directory containing multiple
        Kubernetes YAML files, used to deploy the container image. The path is
        relative to the repository root provided by [SOURCE]. The files must
        reference the provided container image or tag.

        If this field is not set, a default Deployment config and Horizontal
        Pod Autoscaler config are used to deploy the image.
        """)
    parser.add_argument(
        '--timeout',
        help='Maximum time a build is run before it times out. For example, '
        '"2h15m5s" is 2 hours, 15 minutes, and 5 seconds. If you '
        'do not specify a unit, seconds is assumed. Overrides the default '
        'builds/timeout property value for this command invocation.',
        action=actions.StoreProperty(properties.VALUES.builds.timeout),
    )
    parser.add_argument(
        '--expose',
        type=int,
        help='Port that the deployed application listens on. If set, a '
        "Kubernetes Service of type 'LoadBalancer' is created with a "
        'single TCP port mapping that exposes this port.')
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.

    Raises:
      FailedDeployException: If the build is completed and not 'SUCCESS'.
    """

    if not args.source and not args.no_source:
      raise c_exceptions.InvalidArgumentException(
          '--no-source', 'To omit source, use the --no-source flag.')

    if args.no_source:
      if args.tag:
        raise c_exceptions.RequiredArgumentException(
            'SOURCE',
            'Source is required to build container image.'
        )
      if args.config:
        raise c_exceptions.RequiredArgumentException(
            'SOURCE',
            'Source is required when specifying --config because it is a '
            'relative path in the source directory.')

    do_build_and_push = args.image is None
    if not do_build_and_push and not args.config:
      args.no_source = True

    image = self._DetermineImageFromArgs(args)

    # Determine app_name
    if args.app_name:
      app_name = args.app_name
    else:
      app_name = self._ImageName(image)

    # Determine app_version
    app_version = None
    image_has_tag = '@' not in image and ':' in image
    if args.app_version:
      app_version = args.app_version
    elif image_has_tag:
      app_version = image.split(':')[-1]  # Set version to tag
    elif args.source:
      if git.IsGithubRepository(
          args.source) and not git.HasPendingChanges(args.source):
        commit_sha = git.GetGitHeadRevision(args.source)
        if commit_sha:
          app_version = commit_sha

    # Validate expose
    if args.expose and args.expose < 0:
      raise c_exceptions.InvalidArgumentException('--expose',
                                                  'port number is invalid')

    # Determine gcs_staging_dir_bucket and gcs_staging_dir_object
    if args.gcs_staging_dir is None:
      gcs_staging_dir_bucket = staging_bucket_util.GetDefaultStagingBucket()
      gcs_staging_dir_object = 'deploy'
    else:
      try:
        gcs_staging_dir_ref = resources.REGISTRY.Parse(
            args.gcs_staging_dir, collection='storage.objects')
        gcs_staging_dir_object = gcs_staging_dir_ref.object
      except resources.WrongResourceCollectionException:
        gcs_staging_dir_ref = resources.REGISTRY.Parse(
            args.gcs_staging_dir, collection='storage.buckets')
        gcs_staging_dir_object = None
      gcs_staging_dir_bucket = gcs_staging_dir_ref.bucket

    gcs_client = storage_api.StorageClient()
    gcs_client.CreateBucketIfNotExists(gcs_staging_dir_bucket)

    # If we are using a default bucket check that it is owned by user project
    # (b/33046325)
    if (args.gcs_staging_dir is None
        and not staging_bucket_util.BucketIsInProject(
            gcs_client, gcs_staging_dir_bucket)):
      raise c_exceptions.RequiredArgumentException(
          '--gcs-staging-dir',
          'A bucket with name {} already exists and is owned by '
          'another project. Specify a bucket using '
          '--gcs-staging-dir.'.format(gcs_staging_dir_bucket))

    if gcs_staging_dir_object:
      gcs_config_staging_path = '{}/{}/config'.format(
          gcs_staging_dir_bucket, gcs_staging_dir_object)
    else:
      gcs_config_staging_path = gcs_staging_dir_bucket

    if not args.no_source:
      staged_source = self._StageSource(args.source, gcs_staging_dir_bucket,
                                        gcs_staging_dir_object)
    else:
      staged_source = None

    messages = cloudbuild_util.GetMessagesModule()
    build_config = build_util.CreateBuild(
        messages,
        build_timeout=properties.VALUES.builds.timeout.Get(),
        build_and_push=do_build_and_push,
        staged_source=staged_source,
        image=image,
        dockerfile_path='Dockerfile',
        app_name=app_name,
        app_version=app_version,
        config_path=args.config,
        namespace=args.namespace,
        expose_port=args.expose,
        gcs_config_staging_path=gcs_config_staging_path,
        cluster=args.cluster,
        location=args.location,
        build_tags=([] if not args.app_name else [args.app_name]))

    client = cloudbuild_util.GetClientInstance()
    self._SubmitBuild(
        client, messages, build_config, gcs_config_staging_path,
        args.config is None, args.async_)

  def _DetermineImageFromArgs(self, args):
    """Gets the image to use for the build, given the user args.

    Args:
      args: argsparse object from the DeployGKE command.

    Returns:
      Full image string representation.
    """
    if args.tag:
      if (properties.VALUES.builds.check_tag.GetBool() and
          'gcr.io/' not in args.tag):
        raise c_exceptions.InvalidArgumentException(
            '--tag',
            'Tag value must be in the gcr.io/* or *.gcr.io/* namespace.')
      return args.tag

    elif args.image:
      if (properties.VALUES.builds.check_tag.GetBool() and
          'gcr.io/' not in args.image):
        raise c_exceptions.InvalidArgumentException(
            '--image',
            'Image value must be in the gcr.io/* or *.gcr.io/* namespace.')
      return args.image

    else:  # Default tag
      if args.app_name:
        default_name = args.app_name
      elif os.path.isdir(args.source):  # I.e., the source is not a tarball
        default_name = os.path.basename(os.path.abspath(args.source))
      else:
        raise c_exceptions.OneOfArgumentsRequiredException(
            ['--app-name', '--tag'],
            'Cannot resolve default container image. Provide an app name with '
            '--app-name to use as the container image, or provide a full '
            'tag using --tag.')

      if args.app_version:
        default_tag = args.app_version
      elif git.IsGithubRepository(
          args.source) and not git.HasPendingChanges(args.source):
        default_tag = git.GetGitHeadRevision(args.source)
        if not default_tag:
          raise c_exceptions.OneOfArgumentsRequiredException(
              ['--app-version', '--tag'],
              'Cannot resolve default container tag using the Git commit SHA. '
              'Provide an app version with --app-version to use as the '
              'container tag, or provide a full tag using --tag.')
      else:
        raise c_exceptions.OneOfArgumentsRequiredException(
            ['--app-version', '--tag'],
            'Cannot resolve default container tag. '
            'Provide an app version with --app-version to use as the '
            'container tag, or provide a full tag using --tag.')

      return 'gcr.io/$PROJECT_ID/{name}:{tag}'.format(
          name=default_name, tag=default_tag)

  def _ImageName(self, image):
    """Given a full image string, return just the name of the image.

    Args:
      image: Full image string, represented in one of the following ways:
        - <protocol>/<name> (e.g., gcr.io/my-image)
        - <protocol>/<name>:<tag> (e.g., gcr.io/my-image:my-tag)
        - <protocol>/<name>@<digest> (e.g., gcr.io/my-image@sha256:asdfasdf)

    Returns:
      The image, minus the protocol, tag, and/or digest.
    """

    image_without_protocol = image.split('/')[-1]
    if '@' in image_without_protocol:
      return image_without_protocol.split('@')[0]
    elif ':' in image:
      return image_without_protocol.split(':')[0]
    else:
      return image_without_protocol

  def _StageSource(self, source, gcs_staging_dir_bucket,
                   gcs_staging_dir_object):
    """Stages source onto the provided bucket and returns its reference.

    Args:
      source: Path to source repo as a directory on a local disk or a
        gzipped archive file (.tar.gz) in Google Cloud Storage.
      gcs_staging_dir_bucket: Bucket name of staging directory.
      gcs_staging_dir_object: Bucket object of staging directory.

    Returns:
      Reference to the staged source, which has bucket, name, and generation
        fields.
    """

    suffix = '.tgz'
    if source.startswith('gs://') or os.path.isfile(source):
      _, suffix = os.path.splitext(source)

    source_object = 'source/{stamp}-{uuid}{suffix}'.format(
        stamp=times.GetTimeStampFromDateTime(times.Now()),
        uuid=uuid.uuid4().hex,
        suffix=suffix,
    )

    if gcs_staging_dir_object:
      source_object = gcs_staging_dir_object + '/' + source_object

    gcs_source_staging = resources.REGISTRY.Create(
        collection='storage.objects',
        bucket=gcs_staging_dir_bucket,
        object=source_object)

    gcs_client = storage_api.StorageClient()
    if source.startswith('gs://'):
      gcs_source = resources.REGISTRY.Parse(
          source, collection='storage.objects')
      staged_source = gcs_client.Rewrite(gcs_source, gcs_source_staging)
    else:
      if not os.path.exists(source):
        raise c_exceptions.BadFileException(
            'could not find source [{src}]'.format(src=source))
      elif os.path.isdir(source):
        source_snapshot = snapshot.Snapshot(source)
        size_str = resource_transform.TransformSize(
            source_snapshot.uncompressed_size)
        log.status.Print(
            'Creating temporary tarball archive of {num_files} file(s)'
            ' totalling {size} before compression.'.format(
                num_files=len(source_snapshot.files), size=size_str))
        staged_source = source_snapshot.CopyTarballToGCS(
            gcs_client, gcs_source_staging)
      elif os.path.isfile(source):
        unused_root, ext = os.path.splitext(source)
        if ext not in _ALLOWED_SOURCE_EXT:
          raise c_exceptions.BadFileException(
              'Local file [{src}] is none of '.format(src=source) +
              ', '.join(_ALLOWED_SOURCE_EXT))
        log.status.Print('Uploading local file [{src}] to '
                         '[gs://{bucket}/{object}].'.format(
                             src=source,
                             bucket=gcs_source_staging.bucket,
                             object=gcs_source_staging.object,
                         ))
        staged_source = gcs_client.CopyFileToGCS(source,
                                                 gcs_source_staging)

    return staged_source

  def _SubmitBuild(
      self, client, messages, build_config, gcs_config_staging_path,
      suggest_configs, async_):
    """Submits the build.

    Args:
      client: Client used to make calls to Cloud Build API.
      messages: Cloud Build messages module. This is the value returned from
        cloudbuild_util.GetMessagesModule().
      build_config: Build to submit.
      gcs_config_staging_path: A path to a GCS subdirectory where deployed
        configs will be saved to. This value will be printed to the user.
      suggest_configs: If True, suggest YAML configs for the user to add to
        their repo.
      async_: If true, exit immediately after submitting Build, rather than
        waiting for it to complete or fail.

    Raises:
      FailedDeployException: If the build is completed and not 'SUCCESS'.
    """
    project = properties.VALUES.core.project.Get(required=True)
    op = client.projects_builds.Create(
        messages.CloudbuildProjectsBuildsCreateRequest(
            build=build_config, projectId=project))
    log.debug('submitting build: ' + six.text_type(build_config))

    json = encoding.MessageToJson(op.metadata)
    build = encoding.JsonToMessage(messages.BuildOperationMetadata, json).build

    build_ref = resources.REGISTRY.Create(
        collection='cloudbuild.projects.builds',
        projectId=build.projectId,
        id=build.id)

    log.status.Print('Starting Cloud Build to build and deploy to the target '
                     'Google Kubernetes Engine cluster...\n')

    log.CreatedResource(build_ref)
    if build.logUrl:
      log.status.Print(
          'Logs are available at [{log_url}].'.format(log_url=build.logUrl))
    else:
      log.status.Print('Logs are available in the Cloud Console.')

    suggested_configs_path = build_util.SuggestedConfigsPath(
        gcs_config_staging_path, build.id)
    expanded_configs_path = build_util.ExpandedConfigsPath(
        gcs_config_staging_path, build.id)

    if async_:
      log.status.Print(
          '\nIf successful, you can find the configuration files of the deployed '
          'Kubernetes objects stored at gs://{expanded} or by visiting '
          'https://console.cloud.google.com/storage/browser/{expanded}/.'

          .format(expanded=expanded_configs_path))
      if suggest_configs:
        log.status.Print(
            '\nYou will also be able to find the suggested base Kubernetes '
            'configuration files at gs://{suggested} or by visiting '
            'https://console.cloud.google.com/storage/browser/{suggested}/.'
            .format(suggested=suggested_configs_path))

      # Return here, otherwise, logs are streamed from GCS.
      return

    mash_handler = execution.MashHandler(
        execution.GetCancelBuildHandler(client, messages, build_ref))

    with execution_utils.CtrlCSection(mash_handler):
      build = cb_logs.CloudBuildClient(client, messages).Stream(build_ref)

    if build.status == messages.Build.StatusValueValuesEnum.TIMEOUT:
      log.status.Print(
          'Your build and deploy timed out. Use the [--timeout=DURATION] flag '
          'to change the timeout threshold.')

    if build.status != messages.Build.StatusValueValuesEnum.SUCCESS:
      if build_util.SaveConfigsBuildStepIsSuccessful(messages, build):
        log.status.Print(
            'You can find the configuration files for this attempt at gs://{}.'
            .format(expanded_configs_path)
        )
      raise FailedDeployException(build)

    log.status.Print(
        'Successfully deployed to your Google Kubernetes Engine cluster.\n\n'
        'You can find the configuration files of the deployed Kubernetes '
        'objects stored at gs://{expanded} or by visiting '
        'https://console.cloud.google.com/storage/browser/{expanded}/.'
        .format(expanded=expanded_configs_path))
    if suggest_configs:
      log.status.Print(
          '\nYou can also find suggested base Kubernetes configuration files at '
          'gs://{suggested} or by visiting '
          'https://console.cloud.google.com/storage/browser/{suggested}/.'
          .format(suggested=suggested_configs_path))

