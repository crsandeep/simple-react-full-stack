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
"""Create Cloud Source Repositories trigger command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.api_lib.cloudbuild import trigger_config as trigger_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.source import resource_args as repo_resource
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


class CreateCSR(base.CreateCommand):
  """Create a build trigger from a Cloud Source Repository."""

  detailed_help = {
      'EXAMPLES':
          """\
            To create a push trigger for all branches:

              $ {command} --repo="my-repo" --branch-pattern=".*" --build-config="cloudbuild.yaml"
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

    trigger_config = parser.add_mutually_exclusive_group(required=True)

    # Allow trigger config to be specified on the command line or by file.
    trigger_config.add_argument(
        '--trigger-config',
        metavar='PATH',
        help="""\
Path to a YAML or JSON file containing the trigger configuration.

For more details, see: https://cloud.google.com/cloud-build/docs/api/reference/rest/v1/projects.triggers
""")

    # Trigger configuration
    flag_config = trigger_config.add_argument_group(
        help='Flag based trigger configuration')
    flag_config.add_argument('--description', help='Build trigger description.')
    repo_spec = presentation_specs.ResourcePresentationSpec(
        '--repo',  # This defines how the "anchor" or leaf argument is named.
        repo_resource.GetRepoResourceSpec(),
        'Cloud Source Repository.',
        required=True,
        prefixes=False)
    concept_parsers.ConceptParser([repo_spec]).AddToParser(flag_config)
    ref_config = flag_config.add_mutually_exclusive_group(required=True)
    trigger_utils.AddBranchPattern(ref_config)
    trigger_utils.AddTagPattern(ref_config)

    trigger_utils.AddBuildConfigArgs(flag_config)

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
      repo_ref = args.CONCEPTS.repo.Parse()
      repo = repo_ref.reposId
      trigger = messages.BuildTrigger(
          description=args.description,
          triggerTemplate=messages.RepoSource(
              repoName=repo,
              branchName=args.branch_pattern,
              tagName=args.tag_pattern,
          ),
      )

      # Build Config
      if args.build_config:
        trigger.filename = args.build_config
        trigger.substitutions = cloudbuild_util.EncodeTriggerSubstitutions(
            args.substitutions, messages)
      if args.dockerfile:
        project = properties.VALUES.core.project.Get(required=True)
        image = args.dockerfile_image if args.dockerfile_image else 'gcr.io/%s/%s:$COMMIT_SHA' % (
            project, repo)
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
