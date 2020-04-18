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
"""Configure build and deploy to Google Kubernetes Engine command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from apitools.base.py.exceptions import HttpNotFoundError
from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.api_lib.source import sourcerepo
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exceptions
from googlecloudsdk.command_lib.builds import staging_bucket_util
from googlecloudsdk.command_lib.builds.deploy import build_util
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources

import six

_CLEAN_PREVIEW_SCHEDULE_HOUR = 12
_CLEAN_PREVIEW_SCHEDULE = '0 {} * * *'.format(_CLEAN_PREVIEW_SCHEDULE_HOUR)
_REPO_TYPE_CODES = {
    'github': 'ga',
    'bitbucket_mirrored': 'bm',
    'github_mirrored': 'gm',
    'csr': 'cs'
}


class SourceRepoNotConnectedException(c_exceptions.InvalidArgumentException):
  """Exception for when a third party CSR repo is not found.

  This should not be used for regular CSR repos since they are connected by
  default.
  """

  def __init__(self, parameter_name, message):
    super(SourceRepoNotConnectedException, self).__init__(
        parameter_name,
        '{message}\n\n'
        'Visit https://console.cloud.google.com/cloud-build/triggers/connect?project={project} '
        'to connect a repository to your project.'.format(
            message=message,
            project=properties.VALUES.core.project.Get(required=True),
        ))


class ConfigureGKEDeploy(base.Command):
  """Configure automated build and deployment to a target Google Kubernetes Engine cluster.

  Configure automated build and deployment from a repository. This can be
  triggered by a Git branch or tag push.
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
    """
    parser.add_argument(
        '--repo-type',
        help="""
        Type of repository.

        `--repo-owner` must be provided if one of the following choices is
        selected:

        `github` - A GitHub (Cloud Build GitHub App) repository connected to
        Cloud Build triggers. The deployed image will have the format
        'gcr.io/[PROJECT_ID]/github.com/[REPO_OWNER]/[REPO_NAME]:$COMMIT_SHA'.

        `bitbucket_mirrored` - A Bitbucket repository connected to Cloud Source
        Repositories. The deployed image will have the format
        'gcr.io/[PROJECT_ID]/bitbucket.org/[REPO_OWNER]/[REPO_NAME]:$COMMIT_SHA'.

        `github_mirrored` - A GitHub repository connected to Cloud Source
        Repositories. The deployed image will have the format
        'gcr.io/[PROJECT_ID]/github.com/[REPO_OWNER]/[REPO_NAME]:$COMMIT_SHA'.

        `--repo-owner` must not be provided if the following is selected:

        `csr` - A repository on Cloud Source Repositories. The deployed image
        will have the format 'gcr.io/[PROJECT_ID]/[REPO_NAME]:$COMMIT_SHA'.

        Connect repositories at
        https://console.cloud.google.com/cloud-build/triggers/connect.
        """,
        choices=['github', 'bitbucket_mirrored', 'github_mirrored', 'csr'],
        required=True)
    parser.add_argument(
        '--repo-name',
        help='Name of the repository.',
        required=True)
    parser.add_argument(
        '--repo-owner',
        help='Owner of the repository.')
    parser.add_argument(
        '--dockerfile',
        help="""
        Path to the Dockerfile to build from, relative to the repository.

        Defaults to './Dockerfile'.
        """)
    trigger_match = parser.add_mutually_exclusive_group(required=True)
    trigger_match.add_argument(
        '--branch-pattern',
        metavar='REGEX',
        help='''
        A regular expression specifying which Git branches to match.

        This pattern is used as a regex search for any incoming pushes. For
        example, --branch-pattern=foo will match "foo", "foobar", and "barfoo".
        Events on a branch that does not match will be ignored.

        The syntax of the regular expressions accepted is the syntax accepted by
        RE2 and described at https://github.com/google/re2/wiki/Syntax.
        ''')
    trigger_match.add_argument(
        '--tag-pattern',
        metavar='REGEX',
        help='''
        A regular expression specifying which Git tags to match.

        This pattern is used as a regex search for any incoming pushes. For
        example, --tag-pattern=foo will match "foo", "foobar", and "barfoo".
        Events on a tag that does not match will be ignored.

        The syntax of the regular expressions accepted is the syntax accepted by
        RE2 and described at https://github.com/google/re2/wiki/Syntax.
        ''')
    pr_preview = trigger_match.add_argument_group(
        help='Pull request preview deployment settings')
    pr_preview.add_argument(
        '--pull-request-preview',
        help='''
        Enables previewing your application for each pull request.

        This configures your application to deploy to a target cluster when
        a pull request is created or updated against a branch specified by the
        `--pull-request-pattern` argument. The application will be deployed
        to the namespace 'preview-[REPO_NAME]-[PR_NUMBER]'. This namespace will
        be deleted after a number of days specified by the `--preview-expiry`
        argument.

        The deployed preview application will still exist even after the pull
        request is merged or closed. The preview application will eventually get
        cleaned up by a Cloud Scheduler job after the namespace expires. You can
        also delete the namespace manually.
        ''',
        action='store_true',
        required=True
    )
    pr_preview.add_argument(
        '--preview-expiry',
        type=int,
        default=3,
        help='''
        Number of days before a pull request preview deployment's namespace is
        considered to be expired. An expired namespace will eventually be
        deleted. Defaults to 3 days.
        '''
    )
    pr_preview.add_argument(
        '--pull-request-pattern',
        metavar='REGEX',
        help="""
        A regular expression specifying which base Git branch to match for
        pull request events.

        This pattern is used as a regex search for the base branch (the branch
        you are trying to merge into) for pull request updates. For example,
        --pull-request-pattern=foo will match "foo", "foobar", and "barfoo".

        The syntax of the regular expressions accepted is the syntax accepted by
        RE2 and described at https://github.com/google/re2/wiki/Syntax.
        """,
        required=True
    )
    pr_preview.add_argument(
        '--comment-control',
        help="Require a repo collaborator to add '/gcbrun' as a comment in the "
        'pull request in order to run the build.',
        action='store_true'
    )
    parser.add_argument(
        '--gcs-config-staging-dir',
        help="""
        Path to the Google Cloud Storage subdirectory into which to copy the
        configs (suggested base and expanded Kubernetes YAML files) that are
        used to stage and deploy your app. If the bucket in this path doesn't
        exist, Cloud Build creates it.

        If this field is not set, the configs are written to
        ```gs://[PROJECT_ID]_cloudbuild/deploy/config```.
        """)
    parser.add_argument(
        '--app-name',
        help='If specified, the following label is added to the Kubernetes '
        "manifests: 'app.kubernetes.io/name: APP_NAME'. Defaults to the "
        'repository name provided by `--repo-name`.')
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
        relative to the repository root. The files must reference the provided
        container image or tag.

        If this field is not set, a default Deployment config and Horizontal
        Pod Autoscaler config are used to deploy the image.
        """)
    parser.add_argument(
        '--expose',
        type=int,
        help='Port that the deployed application listens on. If set, a '
        "Kubernetes Service of type 'LoadBalancer' is created with a "
        'single TCP port mapping that exposes this port.')
    parser.add_argument(
        '--timeout',
        help='Maximum time a build is run before it times out. For example, '
        '"2h15m5s" is two hours, fifteen minutes, and five seconds. If you '
        'do not specify a unit, seconds is assumed. Overrides the default '
        'builds/timeout property value for this command invocation.',
        action=actions.StoreProperty(properties.VALUES.builds.timeout))

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """

    if args.pull_request_preview:
      if args.repo_type != 'github':
        raise c_exceptions.InvalidArgumentException(
            '--repo-type',
            "Repo type must be 'github' to configure pull request previewing.")
      if args.namespace:
        raise c_exceptions.InvalidArgumentException(
            '--namespace',
            'Namespace must not be provided to configure pull request '
            'previewing. --namespace must only be provided when configuring '
            'automated deployments with the --branch-pattern or --tag-pattern '
            'flags.')
      if args.preview_expiry <= 0:
        raise c_exceptions.InvalidArgumentException(
            '--preview-expiry',
            'Preview expiry must be > 0.')

    # Determine image based on repo type
    image = None

    # Determine github app or csr
    github_repo_name = None
    github_repo_owner = None
    csr_repo_name = None

    project = properties.VALUES.core.project.Get(required=True)

    if args.repo_type == 'github':
      if not args.repo_owner:
        raise c_exceptions.RequiredArgumentException(
            '--repo-owner',
            'Repo owner is required for --repo-type=github.')
      image = 'gcr.io/{}/github.com/{}/{}:$COMMIT_SHA'.format(
          project, args.repo_owner, args.repo_name)
      github_repo_name = args.repo_name
      github_repo_owner = args.repo_owner
      # We do not have to verify that this repo exists because the request to
      # create the BuildTrigger will fail with the appropriate message asking
      # the user to connect their repo, if the repo is not found.

    elif args.repo_type == 'csr':
      if args.repo_owner:
        raise c_exceptions.InvalidArgumentException(
            '--repo-owner',
            'Repo owner must not be provided for --repo-type=csr.')
      image = 'gcr.io/{}/{}:$COMMIT_SHA'.format(project, args.repo_name)
      csr_repo_name = args.repo_name
      self._VerifyCSRRepoExists(csr_repo_name)

    elif args.repo_type == 'bitbucket_mirrored':
      if not args.repo_owner:
        raise c_exceptions.RequiredArgumentException(
            '--repo-owner',
            'Repo owner is required for --repo-type=bitbucket_mirrored.')
      image = 'gcr.io/{}/bitbucket.org/{}/{}:$COMMIT_SHA'.format(
          project, args.repo_owner, args.repo_name)
      csr_repo_name = 'bitbucket_{}_{}'.format(args.repo_owner, args.repo_name)
      self._VerifyBitbucketCSRRepoExists(
          csr_repo_name, args.repo_owner, args.repo_name)

    elif args.repo_type == 'github_mirrored':
      if not args.repo_owner:
        raise c_exceptions.RequiredArgumentException(
            '--repo-owner',
            'Repo owner is required for --repo-type=github_mirrored.')
      image = 'gcr.io/{}/github.com/{}/{}:$COMMIT_SHA'.format(
          project, args.repo_owner, args.repo_name)
      csr_repo_name = 'github_{}_{}'.format(args.repo_owner, args.repo_name)
      self._VerifyGitHubCSRRepoExists(
          csr_repo_name, args.repo_owner, args.repo_name)

    self._VerifyClusterExists(args.cluster, args.location)

    # Determine app_name
    if args.app_name:
      app_name = args.app_name
    else:
      app_name = args.repo_name

    # Determine gcs_config_staging_dir_bucket, gcs_config_staging_dir_object
    if args.gcs_config_staging_dir is None:
      gcs_config_staging_dir_bucket = \
        staging_bucket_util.GetDefaultStagingBucket()
      gcs_config_staging_dir_object = 'deploy/config'
    else:
      try:
        gcs_config_staging_dir_ref = resources.REGISTRY.Parse(
            args.gcs_config_staging_dir, collection='storage.objects')
        gcs_config_staging_dir_object = gcs_config_staging_dir_ref.object
      except resources.WrongResourceCollectionException:
        gcs_config_staging_dir_ref = resources.REGISTRY.Parse(
            args.gcs_config_staging_dir, collection='storage.buckets')
        gcs_config_staging_dir_object = None
      gcs_config_staging_dir_bucket = gcs_config_staging_dir_ref.bucket

    gcs_client = storage_api.StorageClient()
    gcs_client.CreateBucketIfNotExists(gcs_config_staging_dir_bucket)

    # If we are using a default bucket check that it is owned by user project
    # (b/33046325)
    if (args.gcs_config_staging_dir is None
        and not staging_bucket_util.BucketIsInProject(
            gcs_client, gcs_config_staging_dir_bucket)):
      raise c_exceptions.RequiredArgumentException(
          '--gcs-config-staging-dir',
          'A bucket with name {} already exists and is owned by '
          'another project. Specify a bucket using '
          '--gcs-config-staging-dir.'.format(gcs_config_staging_dir_bucket))

    if gcs_config_staging_dir_object:
      gcs_config_staging_path = '{}/{}'.format(
          gcs_config_staging_dir_bucket, gcs_config_staging_dir_object)
    else:
      gcs_config_staging_path = gcs_config_staging_dir_bucket

    if args.pull_request_preview:
      log.status.Print('Setting up previewing {} on pull requests.\n'.format(
          github_repo_name))
      self._ConfigurePRPreview(
          repo_owner=github_repo_owner,
          repo_name=github_repo_name,
          pull_request_pattern=args.pull_request_pattern,
          preview_expiry=args.preview_expiry,
          comment_control=args.comment_control,
          image=image,
          dockerfile_path=args.dockerfile,
          app_name=app_name,
          config_path=args.config,
          expose_port=args.expose,
          gcs_config_staging_path=gcs_config_staging_path,
          cluster=args.cluster,
          location=args.location)
    else:
      log.status.Print('Setting up automated deployments for {}.\n'.format(
          args.repo_name))
      self._ConfigureGitPushBuildTrigger(
          repo_type=args.repo_type,
          csr_repo_name=csr_repo_name,
          github_repo_owner=github_repo_owner,
          github_repo_name=github_repo_name,
          branch_pattern=args.branch_pattern,
          tag_pattern=args.tag_pattern,
          image=image,
          dockerfile_path=args.dockerfile,
          app_name=app_name,
          config_path=args.config,
          namespace=args.namespace,
          expose_port=args.expose,
          gcs_config_staging_path=gcs_config_staging_path,
          cluster=args.cluster,
          location=args.location)

  def _VerifyCSRRepoExists(self, csr_repo_name):
    try:
      csr_repo_ref = sourcerepo.ParseRepo(csr_repo_name)
      csr_repo = sourcerepo.Source().GetRepo(csr_repo_ref)
      if csr_repo.mirrorConfig:
        log.error("CSR repo '{}' has mirrorConfig.url of {}", csr_repo_name,
                  csr_repo.mirrorConfig.url)
        raise c_exceptions.InvalidArgumentException(
            '--repo-type',
            "Repo '{}' is found but is connected to {}. Specify the correct "
            'value for --repo-type, along with appropriate values for '
            '--repo-owner and --repo-name.'
            .format(csr_repo_name, csr_repo.mirrorConfig.url)
        )
    except HttpNotFoundError:
      raise c_exceptions.InvalidArgumentException(
          '--repo-name',
          "Repo '{}' is not found on CSR.".format(csr_repo_name))

  def _VerifyBitbucketCSRRepoExists(self, csr_repo_name, bitbucket_repo_owner,
                                    bitbucket_repo_name):
    try:
      csr_repo_ref = sourcerepo.ParseRepo(csr_repo_name)
      csr_repo = sourcerepo.Source().GetRepo(csr_repo_ref)
      if not csr_repo.mirrorConfig:
        raise c_exceptions.InvalidArgumentException(
            '--repo-type',
            "Repo '{}/{}' is found but the resolved repo name '{}' is a "
            'regular CSR repo. Reference it with --repo-type=csr and '
            '--repo-name={}.'
            .format(bitbucket_repo_owner, bitbucket_repo_name, csr_repo_name,
                    csr_repo_name))
      if (csr_repo.mirrorConfig and
          not csr_repo.mirrorConfig.url.startswith('https://bitbucket.org/')):
        log.error("CSR repo '{}' has mirrorConfig.url of {}", csr_repo_name,
                  csr_repo.mirrorConfig.url)
        raise c_exceptions.InvalidArgumentException(
            '--repo-type',
            "Repo '{}/{}' is found but the resolved repo name '{}' is not "
            'connected to a Bitbucket repo. Specify the correct value for '
            '--repo-type.'
            .format(bitbucket_repo_owner, bitbucket_repo_name, csr_repo_name))
    except HttpNotFoundError:
      raise SourceRepoNotConnectedException(
          '--repo-name',
          "Bitbucket repo '{}/{}' is not connected to CSR.".format(
              bitbucket_repo_owner, bitbucket_repo_name))

  def _VerifyGitHubCSRRepoExists(self, csr_repo_name, github_repo_owner,
                                 github_repo_name):
    try:
      csr_repo_ref = sourcerepo.ParseRepo(csr_repo_name)
      csr_repo = sourcerepo.Source().GetRepo(csr_repo_ref)
      if not csr_repo.mirrorConfig:
        raise c_exceptions.InvalidArgumentException(
            '--repo-type',
            "Repo '{}/{}' is found but the resolved repo name '{}' is a "
            'regular CSR repo. Reference it with --repo-type=csr and '
            '--repo-name={}.'
            .format(github_repo_owner, github_repo_name, csr_repo_name,
                    csr_repo_name))
      if (csr_repo.mirrorConfig and
          not csr_repo.mirrorConfig.url.startswith('https://github.com/')):
        log.error("CSR repo '{}' has mirrorConfig.url of {}", csr_repo_name,
                  csr_repo.mirrorConfig.url)
        raise c_exceptions.InvalidArgumentException(
            '--repo-type',
            "Repo '{}/{}' is found but the resolved repo name '{}' is not "
            'connected to a GitHub repo. Specify the correct value for '
            '--repo-type.'
            .format(github_repo_owner, github_repo_name, csr_repo_name))
    except HttpNotFoundError:
      raise SourceRepoNotConnectedException(
          '--repo-name',
          "GitHub repo '{}/{}' is not connected to CSR.".format(
              github_repo_owner, github_repo_name))

  def _VerifyClusterExists(self, cluster, location):
    client = apis.GetClientInstance('container', 'v1')
    messages = apis.GetMessagesModule('container', 'v1')
    project = properties.VALUES.core.project.Get(required=True)
    try:
      cluster_res = client.projects_locations_clusters.Get(
          messages.ContainerProjectsLocationsClustersGetRequest(
              name='projects/{project}/locations/{location}/clusters/{cluster}'
              .format(
                  project=project,
                  location=location,
                  cluster=cluster
              )))
    except HttpNotFoundError:
      raise c_exceptions.InvalidArgumentException(
          '--cluster',
          "No cluster '{cluster}' in location '{location}' in project {project}.\n\n"
          'Visit https://console.cloud.google.com/kubernetes/list?project={project} '
          'to create a cluster.'.format(
              cluster=cluster,
              location=location,
              project=project
          ))
    if cluster_res.status != messages.Cluster.StatusValueValuesEnum.RUNNING:
      raise core_exceptions.Error(
          'Cluster was found but status is not RUNNING. Status is {}.'
          .format(cluster_res.status))

  def _GetTriggerIfExists(self, client, messages, project, trigger_name):
    """Returns a BuildTrigger if one with the given name exists in a project.

    Args:
      client: Client used to make calls to Cloud Build API.
      messages: Cloud Build messages module. This is the value returned from
        cloudbuild_util.GetMessagesModule().
      project: Project of BuildTrigger to check existence.
      trigger_name: Name of BuildTrigger to check existence.

    Returns:
      A BuildTrigger with the given trigger_name if it exists, else None.
    """
    try:
      return client.projects_triggers.Get(
          messages.CloudbuildProjectsTriggersGetRequest(
              projectId=project,
              triggerId=trigger_name))  # Undocumented, but this field can be ID
                                       # or name.
    except HttpNotFoundError:
      return None

  def _UpsertBuildTrigger(self, build_trigger, add_gcb_trigger_id):
    """Creates a BuildTrigger using the CloudBuild API if it doesn't exist, else updates it.

    A BuildTrigger "exists" if one with the same name already exists in the
    project.

    Args:
      build_trigger: Config of BuildTrigger to create.
      add_gcb_trigger_id: If True, adds the gcb-trigger-id=<trigger-id>
        annotation to the deployed Kubernetes objects. The annotation must be
        added to an existing trigger because the trigger-id is only known after
        the trigger is created.

    Returns:
      The upserted trigger.
    """
    client = cloudbuild_util.GetClientInstance()
    messages = cloudbuild_util.GetMessagesModule()
    project = properties.VALUES.core.project.Get(required=True)

    # Check if trigger with this name already exists.
    existing = self._GetTriggerIfExists(
        client, messages, project, build_trigger.name)
    if existing:
      trigger_id = existing.id

      if add_gcb_trigger_id:
        # Use the existing trigger's id to patch the trigger object we created
        # to add gcb-trigger-id=<trigger-id> annotation for its deployed
        # resources.
        build_util.AddAnnotationToPrepareDeployStep(
            build_trigger, 'gcb-trigger-id', trigger_id)

      upserted_build_trigger = client.projects_triggers.Patch(
          messages.CloudbuildProjectsTriggersPatchRequest(
              buildTrigger=build_trigger,
              projectId=project,
              triggerId=trigger_id
          )
      )
      log.debug('updated existing BuildTrigger: '
                + six.text_type(upserted_build_trigger))

    else:
      upserted_build_trigger = client.projects_triggers.Create(
          messages.CloudbuildProjectsTriggersCreateRequest(
              buildTrigger=build_trigger, projectId=project))
      log.debug('created BuildTrigger: '
                + six.text_type(upserted_build_trigger))

      trigger_id = upserted_build_trigger.id
      if add_gcb_trigger_id:
        # Since <trigger-id> is only known after a BuildTrigger is created, we
        # must patch the newly created trigger to add
        # gcb-trigger-id=<trigger-id> annotation for its deployed resources.
        build_util.AddAnnotationToPrepareDeployStep(
            upserted_build_trigger, 'gcb-trigger-id', trigger_id)
        upserted_build_trigger = client.projects_triggers.Patch(
            messages.CloudbuildProjectsTriggersPatchRequest(
                buildTrigger=upserted_build_trigger,
                projectId=project,
                triggerId=trigger_id
            )
        )
        log.debug('updated BuildTrigger with gcb-trigger-id annotation: '
                  + six.text_type(upserted_build_trigger))

    # Log trigger full name
    build_trigger_ref = resources.REGISTRY.Parse(
        None,
        collection='cloudbuild.projects.triggers',
        api_version='v1',
        params={
            'projectId': project,
            'triggerId': trigger_id,
        })

    if existing:
      log.UpdatedResource(build_trigger_ref)
    else:
      log.CreatedResource(build_trigger_ref)

    return upserted_build_trigger

  def _ConfigureGitPushBuildTrigger(
      self, repo_type, csr_repo_name, github_repo_owner, github_repo_name,
      branch_pattern, tag_pattern, image, dockerfile_path, app_name,
      config_path, namespace, expose_port, gcs_config_staging_path, cluster,
      location):

    # Generate deterministic trigger name
    if csr_repo_name:
      full_repo_name = csr_repo_name
    else:
      full_repo_name = github_repo_owner + '-' + github_repo_name

    name = self._FixBuildTriggerName(self._GenerateResourceName(
        function_code='gp',  # Git Push
        repo_type=repo_type,
        full_repo_name=full_repo_name,
        branch_pattern=branch_pattern,
        tag_pattern=tag_pattern))

    if branch_pattern:
      description = 'Build and deploy on push to "{}"'.format(branch_pattern)
    elif tag_pattern:
      description = 'Build and deploy on "{}" tag'.format(tag_pattern)

    build_trigger = build_util.CreateGitPushBuildTrigger(
        cloudbuild_util.GetMessagesModule(),
        name=name,
        description=description,
        build_timeout=properties.VALUES.builds.timeout.Get(),
        csr_repo_name=csr_repo_name,
        github_repo_owner=github_repo_owner,
        github_repo_name=github_repo_name,
        branch_pattern=branch_pattern,
        tag_pattern=tag_pattern,
        image=image,
        dockerfile_path=dockerfile_path,
        app_name=app_name,
        config_path=config_path,
        namespace=namespace,
        expose_port=expose_port,
        gcs_config_staging_path=gcs_config_staging_path,
        cluster=cluster,
        location=location,
        build_tags=[app_name],
        build_trigger_tags=[app_name],
    )

    log.status.Print('Upserting Cloud Build trigger to build and deploy your '
                     'application.')
    upserted_trigger = self._UpsertBuildTrigger(build_trigger, True)
    project = properties.VALUES.core.project.Get(required=True)

    log.status.Print(
        '\nSuccessfully created the Cloud Build trigger to build and deploy '
        'your application.\n\n'
        'Visit https://console.cloud.google.com/cloud-build/triggers/edit/{trigger_id}?project={project} '
        'to view the trigger.\n\n'
        'You can visit https://console.cloud.google.com/cloud-build/triggers?project={project} '
        'to view all Cloud Build triggers.'.format(
            trigger_id=upserted_trigger.id, project=project)
    )

  def _ConfigurePRPreview(
      self, repo_owner, repo_name, pull_request_pattern, preview_expiry,
      comment_control, image, dockerfile_path, app_name, config_path,
      expose_port, gcs_config_staging_path, cluster, location):
    """Configures previewing the application for each pull request.

    PR previewing is only supported for GitHub repos.

    This creates three resources:
    * A BuildTrigger that builds, publishes, and deploys the application to
      namespace 'preview-[REPO_NAME]-[PR_NUMBER]. The deployed namespace has an
      expiry time, which indicates when it is considered to be expired.
    * A BuildTrigger that cleans up expired namespaces of this application.
    * A CloudScheduler Job that executes the BuildTrigger every day. This is
      needed because BuildTriggers can't run on a Cron by themselves.

    Args:
      repo_owner: Owner of repo to be deployed.
      repo_name: Name of repo to be deployed.
      pull_request_pattern: Regex value of branch to trigger on.
      preview_expiry: How long, in days, a preview namespace can exist before it
        is expired.
      comment_control: Whether or not a user must comment /gcbrun to trigger
        the deployment build.
      image: The image that will be built and deployed. The image can include a
        tag or digest.
      dockerfile_path: Path to the source repository's Dockerfile, relative to
        the source repository's root directory.
      app_name: Application name, which is set as a label to deployed objects.
      config_path: Path to the source repository's Kubernetes configs, relative
        to the source repository's root directory.
      expose_port: Port that the deployed application listens on.
      gcs_config_staging_path: Path to a GCS subdirectory to copy application
        configs to.
      cluster: Name of target cluster to deploy to.
      location: Zone/region of target cluster to deploy to.
    """
    # Attempt to get scheduler location before creating any resources so we can
    # fail early if we fail to get the location due to the user's App Engine
    # app not existing, since the scheduler job must be in the same region:
    # https://cloud.google.com/scheduler/docs/
    scheduler_location = self._GetSchedulerJobLocation()

    pr_preview_trigger = self._ConfigurePRPreviewBuildTrigger(
        repo_owner=repo_owner,
        repo_name=repo_name,
        pull_request_pattern=pull_request_pattern,
        preview_expiry=preview_expiry,
        comment_control=comment_control,
        image=image,
        dockerfile_path=dockerfile_path,
        app_name=app_name,
        config_path=config_path,
        expose_port=expose_port,
        gcs_config_staging_path=gcs_config_staging_path,
        cluster=cluster,
        location=location
    )
    clean_preview_trigger = self._ConfigureCleanPreviewBuildTrigger(
        repo_owner=repo_owner,
        repo_name=repo_name,
        pull_request_pattern=pull_request_pattern,
        cluster=cluster,
        location=location,
        app_name=app_name
    )
    # TODO(b/141294571): Once cron triggers feature is done, use cron trigger
    #   instead of Scheduler job.
    clean_preview_job = self._ConfigureCleanPreviewSchedulerJob(
        repo_owner=repo_owner,
        repo_name=repo_name,
        pull_request_pattern=pull_request_pattern,
        clean_preview_trigger_id=clean_preview_trigger.id,
        scheduler_location=scheduler_location)

    # We add scheduler job location and name as tags to the clean preview
    # trigger to track it as created by us.
    job_location = clean_preview_job.name.split('/')[-3]
    job_id = clean_preview_job.name.split('/')[-1]
    self._UpdateBuildTriggerWithSchedulerJobTags(
        clean_preview_trigger, job_location, job_id)

    log.status.Print(
        '\nSuccessfully created resources for previewing pull requests of your '
        'application.\n\n'
        'Visit https://console.cloud.google.com/cloud-build/triggers/edit/{pr_preview_trigger_id}?project={project} '
        'to view the Cloud Build trigger that deploys your application on pull '
        'request open/update.\n\n'
        'Visit https://console.cloud.google.com/cloud-build/triggers/edit/{clean_preview_trigger_id}?project={project} '
        'to view the Cloud Build trigger that cleans up expired preview '
        'deployments.\n\n'
        'Visit https://console.cloud.google.com/cloudscheduler/jobs/edit/{location}/{job}?project={project} '
        'to view the Cloud Scheduler job that periodically executes the '
        'trigger to clean up expired preview deployments.\n\n'
        'WARNING: The deletion of expired preview deployments requires a Cloud '
        'Scheduler job that runs a Cloud Build trigger every day. Pause '
        "this job if you don't want to it to run anymore."
        .format(
            pr_preview_trigger_id=pr_preview_trigger.id,
            clean_preview_trigger_id=clean_preview_trigger.id,
            project=properties.VALUES.core.project.Get(required=True),
            location=job_location,
            job=job_id
        )
    )

  def _UpdateBuildTriggerWithSchedulerJobTags(
      self, build_trigger, job_location, job_id):
    job_location_tag = 'cloudscheduler-job-location_' + job_location
    job_id_tag = 'cloudscheduler-job-id_' + job_id

    build_trigger_tags = [x for x in build_trigger.tags
                          if not x.startswith('cloudscheduler-job-')]
    build_trigger_tags.append(job_location_tag)
    build_trigger_tags.append(job_id_tag)
    build_trigger.tags = build_trigger_tags

    build_tags = [x for x in build_trigger.build.tags
                  if not x.startswith('cloudscheduler-job-')]
    build_tags.append(job_location_tag)
    build_tags.append(job_id_tag)
    build_trigger.build.tags = build_tags

    client = cloudbuild_util.GetClientInstance()
    messages = cloudbuild_util.GetMessagesModule()
    project = properties.VALUES.core.project.Get(required=True)

    updated_trigger = client.projects_triggers.Patch(
        messages.CloudbuildProjectsTriggersPatchRequest(
            buildTrigger=build_trigger,
            projectId=project,
            triggerId=build_trigger.id
        )
    )

    log.debug('added job id to trigger: ' + six.text_type(updated_trigger))

  def _GenerateResourceName(
      self, function_code, repo_type, full_repo_name,
      branch_pattern=None, tag_pattern=None):
    """Generate a short, deterministic resource name based on parameters that should be unique.

    Args:
      function_code: A two-character code describing what function the resource
        has.
      repo_type: A two-character code describing the repo type.
      full_repo_name: Deterministicly generated repo name, including owner
        available.
      branch_pattern: Branch pattern to match. Only one of branch_pattern or
        tag_pattern should be provided. They can also both be omitted.
      tag_pattern: Tag pattern to match. Only one of branch_pattern or
        tag_pattern should be provided. They can also both be omitted.

    Returns:
      Deterministicly generated resource name.
    """

    repo_type_code = _REPO_TYPE_CODES[repo_type]
    if branch_pattern:
      return '{}{}b-{}-{}'.format(
          function_code, repo_type_code, full_repo_name, branch_pattern)
    elif tag_pattern:
      return '{}{}t-{}-{}'.format(
          function_code, repo_type_code, full_repo_name, tag_pattern)
    else:
      return '{}{}b-{}'.format(
          function_code, repo_type_code, full_repo_name)

  def _ConfigurePRPreviewBuildTrigger(
      self, repo_owner, repo_name, pull_request_pattern, preview_expiry,
      comment_control, image, dockerfile_path, app_name, config_path,
      expose_port, gcs_config_staging_path, cluster, location):

    # Generate deterministic trigger name
    name = self._FixBuildTriggerName(self._GenerateResourceName(
        function_code='pp',  # Pr Preview
        repo_type='github',  # Only supports github for now.
        full_repo_name=repo_owner + '-' + repo_name))
    description = \
      'Build and deploy on PR create/update against "{}"'.format(
          pull_request_pattern)

    build_trigger = build_util.CreatePRPreviewBuildTrigger(
        messages=cloudbuild_util.GetMessagesModule(),
        name=name,
        description=description,
        build_timeout=properties.VALUES.builds.timeout.Get(),
        github_repo_owner=repo_owner,
        github_repo_name=repo_name,
        pr_pattern=pull_request_pattern,
        preview_expiry_days=preview_expiry,
        comment_control=comment_control,
        image=image,
        dockerfile_path=dockerfile_path,
        app_name=app_name,
        config_path=config_path,
        expose_port=expose_port,
        gcs_config_staging_path=gcs_config_staging_path,
        cluster=cluster,
        location=location,
        build_tags=[app_name],
        build_trigger_tags=[app_name]
    )

    log.status.Print('Upserting Cloud Build trigger to build and deploy your '
                     'application on PR open/update for previewing.')
    return self._UpsertBuildTrigger(build_trigger, True)

  def _ConfigureCleanPreviewBuildTrigger(
      self, repo_name, repo_owner, pull_request_pattern, cluster, location,
      app_name):

    # Generate deterministic trigger name
    name = self._FixBuildTriggerName(self._GenerateResourceName(
        function_code='cp',  # Clean Preview
        repo_type='github',  # Only supports github for now.
        full_repo_name=repo_owner + '-' + repo_name))
    description = \
        'Clean expired preview deployments for PRs against "{}"'.format(
            pull_request_pattern)

    build_trigger = build_util.CreateCleanPreviewBuildTrigger(
        messages=cloudbuild_util.GetMessagesModule(),
        name=name,
        description=description,
        github_repo_owner=repo_owner,
        github_repo_name=repo_name,
        cluster=cluster,
        location=location,
        build_tags=[app_name],
        build_trigger_tags=[app_name]
    )

    log.status.Print('Upserting Cloud Build trigger to clean expired preview '
                     'deployments of your application.')
    return self._UpsertBuildTrigger(build_trigger, False)

  def _GetSchedulerJobLocation(self):
    messages = apis.GetMessagesModule('cloudscheduler', 'v1')
    client = apis.GetClientInstance('cloudscheduler', 'v1')
    project = properties.VALUES.core.project.Get(required=True)

    try:
      locations_res = client.projects_locations.List(
          messages.CloudschedulerProjectsLocationsListRequest(
              name='projects/' + project))
    except HttpNotFoundError:
      raise core_exceptions.Error(
          'You must create an App Engine application in your project to use '
          'Cloud Scheduler. Visit '
          'https://console.developers.google.com/appengine?project={} to '
          'add an App Engine application.'.format(project))

    return locations_res.locations[0].labels.additionalProperties[0].value

  def _ConfigureCleanPreviewSchedulerJob(
      self, repo_owner, repo_name, pull_request_pattern,
      clean_preview_trigger_id, scheduler_location):

    log.status.Print('Upserting Cloud Scheduler to run Cloud Build trigger to '
                     'clean expired preview deployments of your application.')

    messages = apis.GetMessagesModule('cloudscheduler', 'v1')
    client = apis.GetClientInstance('cloudscheduler', 'v1')
    project = properties.VALUES.core.project.Get(required=True)
    service_account_email = project + '@appspot.gserviceaccount.com'

    # Generate deterministic scheduler job name (id)
    job_id = self._FixSchedulerName(self._GenerateResourceName(
        function_code='cp',  # Clean Preview
        repo_type='github',  # Only supports github for now.
        full_repo_name=repo_owner + '-' + repo_name))

    name = 'projects/{}/locations/{}/jobs/{}'.format(
        project, scheduler_location, job_id)

    job = messages.Job(
        name=name,
        description='Every day, run trigger to clean expired preview '
                    'deployments for PRs against "{}" in {}/{}'.format(
                        pull_request_pattern, repo_owner, repo_name),
        schedule=_CLEAN_PREVIEW_SCHEDULE,
        timeZone='UTC',
        httpTarget=messages.HttpTarget(
            uri='https://cloudbuild.googleapis.com/v1/projects/{}/triggers/{}:run'
            .format(project, clean_preview_trigger_id),
            httpMethod=messages.HttpTarget.HttpMethodValueValuesEnum.POST,
            body=bytes(
                # We don't actually use the branchName value but it has to be
                # set to an existing branch, so set it to master.
                '{{"projectId":"{}","repoName":"{}","branchName":"master"}}'
                .format(project, repo_name)
                .encode('utf-8')),
            oauthToken=messages.OAuthToken(
                serviceAccountEmail=service_account_email
            )
        )
    )

    existing = None
    try:
      existing = client.projects_locations_jobs.Get(
          messages.CloudschedulerProjectsLocationsJobsGetRequest(name=name))

      upserted_job = client.projects_locations_jobs.Patch(
          messages.CloudschedulerProjectsLocationsJobsPatchRequest(
              name=name,
              job=job))
      log.debug('updated existing CloudScheduler job: '
                + six.text_type(upserted_job))

    except HttpNotFoundError:
      upserted_job = client.projects_locations_jobs.Create(
          messages.CloudschedulerProjectsLocationsJobsCreateRequest(
              parent='projects/{}/locations/{}'.format(
                  project, scheduler_location),
              job=job))
      log.debug('created CloudScheduler job: ' + six.text_type(upserted_job))

    job_id = upserted_job.name.split('/')[-1]
    job_ref = resources.REGISTRY.Parse(
        None,
        collection='cloudscheduler.projects.locations.jobs',
        api_version='v1',
        params={
            'projectsId': project,
            'locationsId': scheduler_location,
            'jobsId': job_id,
        })

    if existing:
      log.UpdatedResource(job_ref)
    else:
      log.CreatedResource(job_ref)

    return upserted_job

  def _FixBuildTriggerName(self, name):
    """Fixes a BuildTrigger name to match the allowed format.

    Args:
      name: Name must start with an alpha-numberic character, since this method
        will not check that condition.

    Returns:
      Fixed name.
    """
    # Name pattern must match
    # ^[a-zA-Z0-9]$|^[a-zA-Z0-9][a-zA-Z0-9-]{0,62}[a-zA-Z0-9]$, where the max
    # length is 64 characters.
    if len(name) > 64:
      name = name[:64]
    name = re.sub('[^a-zA-Z0-9-]', '-', name)
    if name.endswith('-'):  # Cannot trail in a '-' character.
      name = name[:-1] + '0'
    # Assume the name starts with alpha-numeric character, so we will not check.

    return name

  def _FixSchedulerName(self, name):
    """Fixes a Scheduler Job's name to match the allowed format.

    Args:
      name: Name to fix.

    Returns:
      Fixed name.
    """
    # Name pattern must match "[a-zA-Z\d_-]{1,500}".
    if len(name) > 500:
      name = name[:500]
    name = re.sub('[^a-zA-Z0-9_-]', '-', name)

    return name
