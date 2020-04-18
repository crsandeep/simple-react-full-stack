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
"""Create GitHub trigger command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.api_lib.cloudbuild import trigger_config as trigger_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


class CreateGitHub(base.CreateCommand):
  """Create a build trigger for a GitHub repository."""

  detailed_help = {
      'EXAMPLES':
          """\
            To create a push trigger for all branches:

              $ {command} --repo-owner="GoogleCloudPlatform" --repo-name="cloud-builders" --branch-pattern=".*" --build-config="cloudbuild.yaml"

            To create a pull request trigger for master:

              $ {command} --repo-owner="GoogleCloudPlatform" --repo-name="cloud-builders" --pull-request-pattern="^master$" --build-config="cloudbuild.yaml"
          """,
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
    """

    parser.display_info.AddFormat("""
          table(
            name,
            createTime.date('%Y-%m-%dT%H:%M:%S%Oz', undefined='-'),
            status
          )
        """)

    # Allow trigger config to be specified on the command line or file
    trigger_config = parser.add_mutually_exclusive_group(required=True)
    trigger_config.add_argument(
        '--trigger-config',
        help=('Path to a YAML/JSON file for Build Trigger config. '
              'See https://cloud.google.com/cloud-build/docs/api/reference'
              '/rest/v1/projects.triggers#BuildTrigger'),
        metavar='PATH',
    )

    # Trigger configuration
    flag_config = trigger_config.add_argument_group(
        help='Flag based trigger configuration')
    flag_config.add_argument('--description', help='Build trigger description.')
    flag_config.add_argument(
        '--repo-owner', help='Owner of the GitHub Repository.', required=True)

    flag_config.add_argument(
        '--repo-name', help='Name of the GitHub Repository.', required=True)
    ref_config = flag_config.add_mutually_exclusive_group(required=True)
    trigger_utils.AddBranchPattern(ref_config)
    trigger_utils.AddTagPattern(ref_config)
    pr_config = ref_config.add_argument_group(help='Pull Request settings')
    pr_config.add_argument(
        '--pull-request-pattern',
        metavar='REGEX',
        help="""\
A regular expression specifying which base git branch to match for
pull request events.

This pattern is used as a regex search for the base branch (the branch you are
trying to merge into) for pull request updates.
For example, --pull-request-pattern=foo will match "foo", "foobar", and "barfoo".

The syntax of the regular expressions accepted is the syntax accepted by
RE2 and described at https://github.com/google/re2/wiki/Syntax.
""")
    pr_config.add_argument(
        '--comment-control',
        help='Require a repository collaborator owner to comment \'/gcbrun\' on a pull request before running the build.',
        action='store_true')

    trigger_utils.AddBuildConfigArgs(flag_config)

  def ParseTriggerFromFlags(self, args):
    project = properties.VALUES.core.project.Get(required=True)
    messages = cloudbuild_util.GetMessagesModule()
    trigger = messages.BuildTrigger()
    trigger.description = args.description
    # GitHub config
    gh = messages.GitHubEventsConfig(owner=args.repo_owner, name=args.repo_name)

    if args.comment_control and not args.pull_request_pattern:
      raise c_exceptions.RequiredArgumentException(
          '--comment-control',
          '--comment-control must be specified with --pull-request-pattern')
    if args.pull_request_pattern:
      gh.pullRequest = messages.PullRequestFilter(
          branch=args.pull_request_pattern)
      if args.comment_control:
        gh.pullRequest.commentControl = messages.PullRequestFilter.CommentControlValueValuesEnum.COMMENTS_ENABLED
    else:
      # Push event
      gh.push = messages.PushFilter(
          branch=args.branch_pattern, tag=args.tag_pattern)
    trigger.github = gh

    # Build Config
    if args.build_config:
      trigger.filename = args.build_config
      trigger.substitutions = cloudbuild_util.EncodeTriggerSubstitutions(
          args.substitutions, messages)
    if args.dockerfile:
      image = args.dockerfile_image if args.dockerfile_image else 'gcr.io/%s/github.com/%s/%s:$COMMIT_SHA' % (
          project, args.repo_owner, args.repo_name)
      trigger.build = messages.Build(steps=[
          messages.BuildStep(
              name='gcr.io/cloud-builders/docker',
              dir=args.dockerfile_dir,
              args=['build', '-t', image, '-f', args.dockerfile, '.'],
          )
      ])

    # Include/Exclude files
    if args.included_files:
      trigger.includedFiles = args.included_files
    if args.ignored_files:
      trigger.ignoredFiles = args.ignored_files

    return trigger

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """

    client = cloudbuild_util.GetClientInstance()
    messages = cloudbuild_util.GetMessagesModule()

    trigger = messages.BuildTrigger()
    if args.trigger_config:
      trigger = cloudbuild_util.LoadMessageFromPath(
          path=args.trigger_config,
          msg_type=messages.BuildTrigger,
          msg_friendly_name='build trigger config',
          skip_camel_case=['substitutions'])
    else:
      trigger = self.ParseTriggerFromFlags(args)

    # Send the Create request
    project = properties.VALUES.core.project.Get(required=True)
    created_trigger = client.projects_triggers.Create(
        messages.CloudbuildProjectsTriggersCreateRequest(
            buildTrigger=trigger, projectId=project))

    trigger_resource = resources.REGISTRY.Parse(
        None,
        collection='cloudbuild.projects.triggers',
        api_version='v1',
        params={
            'projectId': project,
            'triggerId': created_trigger.id,
        })
    log.CreatedResource(trigger_resource)

    return created_trigger
