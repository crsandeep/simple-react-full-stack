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
"""Submit build command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.builds import flags
from googlecloudsdk.command_lib.builds import submit_util


def _CommonArgs(parser):
  """Register flags for this command.

  Args:
    parser: An argparse.ArgumentParser-like object. It is mocked out in order to
      capture some information, but behaves like an ArgumentParser.
  """
  source = parser.add_mutually_exclusive_group()
  source.add_argument(
      'source',
      nargs='?',
      default='.',  # By default, the current directory is used.
      help='The location of the source to build. The location can be a '
      'directory on a local disk or a gzipped archive file (.tar.gz) in '
      'Google Cloud Storage. If the source is a local directory, this '
      'command skips the files specified in the `--ignore-file`. If '
      '`--ignore-file` is not specified, use`.gcloudignore` file. If a '
      '`.gitignore` file is present in the local source directory, gcloud '
      'will use a Git-compatible `.gcloudignore` file that respects your '
      '.gitignored files. The global `.gitignore` is not respected. For more '
      'information on `.gcloudignore`, see `gcloud topic gcloudignore`.',
  )
  source.add_argument(
      '--no-source',
      action='store_true',
      help='Specify that no source should be uploaded with this build.')

  flags.AddGcsSourceStagingDirFlag(parser)
  flags.AddGcsLogDirFlag(parser)
  flags.AddTimeoutFlag(parser)

  flags.AddMachineTypeFlag(parser)
  flags.AddDiskSizeFlag(parser)
  flags.AddSubstitutionsFlag(parser)

  flags.AddNoCacheFlag(parser)
  flags.AddAsyncFlag(parser)
  parser.display_info.AddFormat("""
        table(
          id,
          createTime.date('%Y-%m-%dT%H:%M:%S%Oz', undefined='-'),
          duration(start=startTime,end=finishTime,precision=0,calendar=false,undefined="  -").slice(2:).join(""):label=DURATION,
          build_source(undefined="-"):label=SOURCE,
          build_images(undefined="-"):label=IMAGES,
          status
        )
      """)
  # Do not try to create a URI to update the cache.
  parser.display_info.AddCacheUpdater(None)

  flags.AddIgnoreFileFlag(parser)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Submit(base.CreateCommand):
  """Submit a build using Google Cloud Build.

  Submit a build using Google Cloud Build.

  ## NOTES

  You can also run a build locally using the
  separate component: `gcloud components install cloud-build-local`.
  """

  detailed_help = {
      'DESCRIPTION':
          """\
          {description}

          When the `builds/use_kaniko` property is `True`, builds submitted with
          `--tag` will use Kaniko
          (https://github.com/GoogleContainerTools/kaniko) to execute builds.
          Kaniko executes directives in a Dockerfile, with remote layer caching
          for faster builds. By default, Kaniko will cache layers for 6 hours.
          To override this, set the `builds/kaniko_cache_ttl` property.
      """,
      'EXAMPLES': ("""
      To submit a build with source located at storage URL `gs://bucket/object.zip`:

         $ {command}  `gs://bucket/object.zip` --tag=gcr.io/my-project/image

      To submit a build with source located at storage URL `gs://bucket/object.zip`
      using config file `config.yaml`:

        $ {command} `gs://bucket/object.zip` --tag=gcr.io/my-project/image --config=config.yaml

      To submit a build with local source `source.tgz` asynchronously:

        $ {command} `source.tgz` --tag=gcr.io/my-project/image --async
      """)
  }

  @staticmethod
  def Args(parser):
    _CommonArgs(parser)
    flags.AddConfigFlags(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.

    Raises:
      FailedBuildException: If the build is completed and not 'SUCCESS'.
    """

    messages = cloudbuild_util.GetMessagesModule()

    # Create the build request.
    build_config = submit_util.CreateBuildConfig(
        args.tag, args.no_cache, messages, args.substitutions, args.config,
        args.IsSpecified('source'), args.no_source, args.source,
        args.gcs_source_staging_dir, args.ignore_file, args.gcs_log_dir,
        args.machine_type, args.disk_size)

    # Start the build.
    build, _ = submit_util.Build(messages, args.async_, build_config)
    return build


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class SubmitBeta(Submit):
  """Submit a build using Google Cloud Build.

  Submit a build using Google Cloud Build.

  ## NOTES

  You can also run a build locally using the
  separate component: `gcloud components install cloud-build-local`.
  """


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class SubmitAlpha(SubmitBeta):
  """Submit a build using Google Cloud Build.

  Submit a build using Google Cloud Build.

  ## NOTES

  You can also run a build locally using the
  separate component: `gcloud components install cloud-build-local`.
  """

  @staticmethod
  def Args(parser):
    _CommonArgs(parser)
    flags.AddConfigFlagsAlpha(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.

    Raises:
      FailedBuildException: If the build is completed and not 'SUCCESS'.
    """

    messages = cloudbuild_util.GetMessagesModule()

    # Create the build request.
    build_config = submit_util.CreateBuildConfigAlpha(
        args.tag, args.no_cache, messages, args.substitutions, args.config,
        args.IsSpecified('source'), args.no_source, args.source,
        args.gcs_source_staging_dir, args.ignore_file, args.gcs_log_dir,
        args.machine_type, args.disk_size, args.pack)

    # Start the build.
    build, _ = submit_util.Build(messages, args.async_, build_config)
    return build
