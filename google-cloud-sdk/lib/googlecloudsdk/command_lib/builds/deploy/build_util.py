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
"""Support library to generate Build and BuildTrigger configs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import times

import six

_VERSION = '$COMMIT_SHA'

_DEFAULT_TAGS = [
    'gcp-cloud-build-deploy',
    'gcp-cloud-build-deploy-gcloud'
]
_DEFAULT_PR_PREVIEW_TAGS = [
    'gcp-cloud-build-deploy-gcloud',
    'gcp-cloud-build-deploy-pr-preview',
]
_DEFAULT_CLEAN_PREVIEW_TAGS = [
    'gcp-cloud-build-deploy-gcloud',
    'gcp-cloud-build-deploy-clean-preview',
]

_GKE_DEPLOY_PROD = 'gcr.io/cloud-builders/gke-deploy'

_SUGGESTED_CONFIGS_PATH = '{0}/{1}/suggested'
_EXPANDED_CONFIGS_PATH = '{0}/{1}/expanded'

# Build substitution variables
_DOCKERFILE_PATH_SUB_VAR = '_DOCKERFILE_PATH'
_APP_NAME_SUB_VAR = '_APP_NAME'
_K8S_YAML_PATH_SUB_VAR = '_K8S_YAML_PATH'
_EXPOSE_PORT_SUB_VAR = '_EXPOSE_PORT'
_GKE_CLUSTER_SUB_VAR = '_GKE_CLUSTER'
_GKE_LOCATION_SUB_VAR = '_GKE_LOCATION'
_OUTPUT_BUCKET_PATH_SUB_VAR = '_OUTPUT_BUCKET_PATH'
_K8S_ANNOTATIONS_SUB_VAR = '_K8S_ANNOTATIONS'
_K8S_NAMESPACE_SUB_VAR = '_K8S_NAMESPACE'
_PREVIEW_EXPIRY_SUB_VAR = '_PREVIEW_EXPIRY'

_EXPANDED_CONFIGS_PATH_DYNAMIC = _EXPANDED_CONFIGS_PATH.format(
    '$' + _OUTPUT_BUCKET_PATH_SUB_VAR, '$BUILD_ID')
_SUGGESTED_CONFIGS_PATH_DYNAMIC = _SUGGESTED_CONFIGS_PATH.format(
    '$' + _OUTPUT_BUCKET_PATH_SUB_VAR, '$BUILD_ID')

_SAVE_CONFIGS_SCRIPT = '''
set -e

if [[ "${output_bucket_path}" ]]; then
  gsutil -m cp output/expanded/* gs://{expanded}
  echo "Copied expanded configs to gs://{expanded}"
  echo "View expanded configs at https://console.cloud.google.com/storage/browser/{expanded}/"
  if [[ ! "${k8s_yaml_path}" ]]; then
    gsutil -m cp output/suggested/* gs://{suggested}
    echo "Copied suggested base configs to gs://{suggested}"
    echo "View suggested base configs at https://console.cloud.google.com/storage/browser/{suggested}/"
  fi
fi
'''.format(
    output_bucket_path=_OUTPUT_BUCKET_PATH_SUB_VAR,
    expanded=_EXPANDED_CONFIGS_PATH_DYNAMIC,
    k8s_yaml_path=_K8S_YAML_PATH_SUB_VAR,
    suggested=_SUGGESTED_CONFIGS_PATH_DYNAMIC,
)

_PREPARE_PREVIEW_DEPLOY_SCRIPT = '''
set -e

REPO_NAME_FIXED=$$(echo $REPO_NAME | tr "[:upper:]" "[:lower:]")
NAMESPACE=preview-$$REPO_NAME_FIXED-$_PR_NUMBER

# Save generated preview namespace to a file for use in other steps
echo $$NAMESPACE > preview-namespace.txt

gcloud container clusters get-credentials ${cluster} --zone=${location}

# Fail if namespace exists but isn't for this repo name
NAMESPACE_REF=$$(kubectl get namespace $$NAMESPACE --ignore-not-found)
if [[ $$NAMESPACE_REF ]]; then
  EXPECTED_REPO_NAME=$$(kubectl get namespace $$NAMESPACE -o=jsonpath="{{.metadata.annotations.preview/repo-name}}")
  if [[ $$EXPECTED_REPO_NAME != $REPO_NAME ]]; then
    echo "Namespace already exists but preview/repo-name annotation does not match: $$EXPECTED_REPO_NAME"
    exit 1
  fi
fi

/gke-deploy prepare \\
  --filename=${k8s_yaml_path} \\
  --image={image} \\
  --app=${app_name} \\
  --version=$COMMIT_SHA \\
  --namespace=$$NAMESPACE \\
  --output=output \\
  --annotation=gcb-build-id=$BUILD_ID,${k8s_annotations} \\
  --expose=${expose_port}
'''

_APPLY_PREVIEW_DEPLOY_SCRIPT = '''
set -e

NAMESPACE=$$(cat preview-namespace.txt)

/gke-deploy apply \\
  --filename=output/expanded \\
  --namespace=$$NAMESPACE \\
  --cluster=${cluster} \\
  --location=${location} \\
  --timeout=24h
'''.format(
    cluster=_GKE_CLUSTER_SUB_VAR,
    location=_GKE_LOCATION_SUB_VAR,
)

# This should be done in a separate step because the date command in
# _APPLY_PREVIEW_DEPLOY_SCRIPT is busybox date, which can't increment days.
_ANNOTATE_PREVIEW_NAMESPACE_SCRIPT = '''
set -e

NAMESPACE=$$(cat preview-namespace.txt)
gcloud container clusters get-credentials ${cluster} --zone=${location}
EXPIRY_EPOCH=$$(date -d "+${preview_expiry} days" "+%s")
kubectl annotate namespace $$NAMESPACE preview/repo-name=$REPO_NAME preview/expiry=$$EXPIRY_EPOCH --overwrite
'''.format(
    cluster=_GKE_CLUSTER_SUB_VAR,
    location=_GKE_LOCATION_SUB_VAR,
    preview_expiry=_PREVIEW_EXPIRY_SUB_VAR,
)

_CLEANUP_PREVIEW_SCRIPT = '''
set -e

gcloud container clusters get-credentials ${cluster} --zone=${location} --project=$PROJECT_ID

IFS=
NAMESPACES="$$(kubectl get namespace -o=jsonpath="{{range .items[?(@.metadata.annotations.preview/repo-name==\\"$REPO_NAME\\")]}}{{.metadata.name}},{{.metadata.annotations.preview/expiry}}{{\\"\\n\\"}}{{end}}")"

if [[ -z $$NAMESPACES ]]; then
  echo "No preview environments found"
  exit
fi

while read -r i; do
  NAMESPACE=$$(echo $$i | cut -d"," -f1)
  EXPIRY=$$(echo $$i | cut -d"," -f2)

  if [[ $$(date "+%s") -ge $$EXPIRY ]]; then
    echo "Deleting expired preview environment in namespace $$NAMESPACE"
    kubectl delete namespace $$NAMESPACE
  else
    echo "Preview environment in namespace $$NAMESPACE expires on $$(date --date="@$$EXPIRY" -u)"
  fi
done <<< $$NAMESPACES
'''.format(
    cluster=_GKE_CLUSTER_SUB_VAR,
    location=_GKE_LOCATION_SUB_VAR,
)

# Build step IDs
_BUILD_BUILD_STEP_ID = 'Build'
_PUSH_BUILD_STEP_ID = 'Push'
_PREPARE_DEPLOY_BUILD_STEP_ID = 'Prepare deploy'
_SAVE_CONFIGS_BUILD_STEP_ID = 'Save generated Kubernetes configs'
_APPLY_DEPLOY_BUILD_STEP_ID = 'Apply deploy'
_ANNOTATE_PREVIEW_NAMESPACE_BUILD_STEP_ID = 'Annotate preview namespace'
_CLEANUP_PREVIEW_BUILD_STEP_ID = 'Delete expired preview environments'


def SuggestedConfigsPath(gcs_config_staging_path, build_id):
  """Gets the formatted suggested configs path, without the 'gs://' prefix.

  Args:
    gcs_config_staging_path: The path to a GCS subdirectory where the configs
      are saved to.
    build_id: The build_id of the build that creates and saves the configs.

  Returns:
    Formatted suggested configs path as a string.
  """
  return _SUGGESTED_CONFIGS_PATH.format(
      gcs_config_staging_path, build_id)


def ExpandedConfigsPath(gcs_config_staging_path, build_id):
  """Gets the formatted expanded configs path, without the 'gs://' prefix.

  Args:
    gcs_config_staging_path: The path to a GCS subdirectory where the configs
      are saved to.
    build_id: The build_id of the build that creates and saves the configs.

  Returns:
    Formatted expanded configs path as a string.
  """
  return _EXPANDED_CONFIGS_PATH.format(
      gcs_config_staging_path, build_id)


def SaveConfigsBuildStepIsSuccessful(messages, build):
  """Returns True if the step with _SAVE_CONFIGS_BUILD_STEP_ID id is successful.

  Args:
    messages: Cloud Build messages module. This is the value returned from
      cloudbuild_util.GetMessagesModule().
    build: The build that contains the step to check.

  Returns:
    True if the step is successful, else false.
  """
  save_configs_build_step = next((
      x for x in build.steps if x.id == _SAVE_CONFIGS_BUILD_STEP_ID
  ), None)

  status = save_configs_build_step.status
  return status == messages.BuildStep.StatusValueValuesEnum.SUCCESS


def CreateBuild(
    messages, build_timeout, build_and_push, staged_source,
    image, dockerfile_path, app_name, app_version, config_path, namespace,
    expose_port, gcs_config_staging_path, cluster, location, build_tags
):
  """Creates the Cloud Build config to run.

  Args:
    messages: Cloud Build messages module. This is the value returned from
      cloudbuild_util.GetMessagesModule().
    build_timeout: An optional maximum time a build is run before it times out.
      For example, "2h15m5s" is 2 hours, 15 minutes, and 5 seconds. If you do
      not specify a unit, seconds is assumed. If this value is None, a timeout
      is not set.
    build_and_push: If True, the created build will have Build and Push steps.
    staged_source: An optional GCS object for a staged source repository. The
      object must have bucket, name, and generation fields. If this value is
      None, the created build will not have a source.
    image: The image that will be deployed and optionally built beforehand. The
      image can include a tag or digest.
    dockerfile_path: An optional path to the source repository's Dockerfile,
      relative to the source repository's root directory. If this value is not
      provided, 'Dockerfile' is used.
    app_name: An optional app name that is set to a substitution variable.
      If this value is None, the substitution variable is set to '' to indicate
      its absence.
    app_version: A app version that is set to the deployed application's
      version. If this value is None, the version will be set to '' to indicate
      its absence.
    config_path: An optional path to the source repository's Kubernetes configs,
      relative to the source repository's root directory that is set to a
      substitution variable. If this value is None, the substitution variable is
      set to '' to indicate its absence.
    namespace: An optional Kubernetes namespace of the cluster to deploy to that
      is set to a substitution variable. If this value is None, the substitution
      variable is set to 'default'.
    expose_port: An optional port that the deployed application listens to that
      is set to a substitution variable. If this value is None, the substitution
      variable is set to 0 to indicate its absence.
    gcs_config_staging_path: An optional path to a GCS subdirectory to copy
      application configs that is set to a substitution variable. If this value
      is None, the substitution variable is set to '' to indicate its absence.
    cluster: The name of the target cluster to deploy to.
    location: The zone/region of the target cluster to deploy to.
    build_tags: Tags to append to build tags in addition to default tags.

  Returns:
    messages.Build, the Cloud Build config.
  """

  build = messages.Build()

  if build_timeout is not None:
    try:
      # A bare number is interpreted as seconds.
      build_timeout_secs = int(build_timeout)
    except ValueError:
      build_timeout_duration = times.ParseDuration(build_timeout)
      build_timeout_secs = int(build_timeout_duration.total_seconds)
    build.timeout = six.text_type(build_timeout_secs) + 's'

  if staged_source:
    build.source = messages.Source(
        storageSource=messages.StorageSource(
            bucket=staged_source.bucket,
            object=staged_source.name,
            generation=staged_source.generation
        )
    )

  if config_path is None:
    config_path = ''

  if not expose_port:
    expose_port = '0'
  else:
    expose_port = six.text_type(expose_port)
  if app_version is None:
    app_version = ''

  build.steps = []

  if build_and_push:
    build.steps.append(_BuildBuildStep(messages, image))
    build.steps.append(_PushBuildStep(messages, image))

  build.steps.append(messages.BuildStep(
      id=_PREPARE_DEPLOY_BUILD_STEP_ID,
      name=_GKE_DEPLOY_PROD,
      args=[
          'prepare',
          '--filename=${}'.format(_K8S_YAML_PATH_SUB_VAR),
          '--image={}'.format(image),
          '--app=${}'.format(_APP_NAME_SUB_VAR),
          '--version={}'.format(app_version),
          '--namespace=${}'.format(_K8S_NAMESPACE_SUB_VAR),
          '--output=output',
          '--annotation=gcb-build-id=$BUILD_ID,${}'.format(
              _K8S_ANNOTATIONS_SUB_VAR),  # You cannot embed a substitution
          # variable in another, so gcb-build-id=$BUILD_ID must be hard-coded.
          '--expose=${}'.format(_EXPOSE_PORT_SUB_VAR),
          '--create-application-cr',
          '--links="Build details=https://console.cloud.google.com/cloud-build/builds/$BUILD_ID?project=$PROJECT_ID"',
      ],
  ))
  build.steps.append(_SaveConfigsBuildStep(messages))
  build.steps.append(messages.BuildStep(
      id=_APPLY_DEPLOY_BUILD_STEP_ID,
      name=_GKE_DEPLOY_PROD,
      args=[
          'apply',
          '--filename=output/expanded',
          '--namespace=${}'.format(_K8S_NAMESPACE_SUB_VAR),
          '--cluster=${}'.format(_GKE_CLUSTER_SUB_VAR),
          '--location=${}'.format(_GKE_LOCATION_SUB_VAR),
          '--timeout=24h'  # Set this to max value allowed for a build so that
          # this step never times out. We prefer the timeout given to the build
          # to take precedence.
      ],
  ))

  substitutions = _BaseBuildSubstitutionsDict(dockerfile_path, app_name,
                                              config_path, expose_port, cluster,
                                              location, gcs_config_staging_path)
  if namespace is None:
    namespace = 'default'
  substitutions[_K8S_NAMESPACE_SUB_VAR] = namespace

  build.substitutions = cloudbuild_util.EncodeSubstitutions(
      substitutions, messages)

  build.tags = _DEFAULT_TAGS[:]
  if build_tags:
    for tag in build_tags:
      build.tags.append(tag)

  build.options = messages.BuildOptions()
  build.options.substitutionOption = messages.BuildOptions.SubstitutionOptionValueValuesEnum.ALLOW_LOOSE

  if build_and_push:
    build.images = [image]

  build.artifacts = messages.Artifacts(
      objects=messages.ArtifactObjects(
          location='gs://' + _EXPANDED_CONFIGS_PATH_DYNAMIC,
          paths=['output/expanded/*']
      )
  )

  return build


def CreateGitPushBuildTrigger(
    messages, name, description, build_timeout,
    csr_repo_name, github_repo_owner, github_repo_name,
    branch_pattern, tag_pattern,
    image, dockerfile_path, app_name, config_path, namespace,
    expose_port, gcs_config_staging_path, cluster, location, build_tags,
    build_trigger_tags
):
  """Creates the Cloud BuildTrigger config that deploys an application when triggered by a git push.

  Args:
    messages: Cloud Build messages module. This is the value returned from
      cloudbuild_util.GetMessagesModule().
    name: Trigger name, which must be unique amongst all triggers in a project.
    description: Trigger description.
    build_timeout: An optional maximum time a triggered build is run before it
      times out. For example, "2h15m5s" is 2 hours, 15 minutes, and 5 seconds.
      If you do not specify a unit, seconds is assumed. If this value is None, a
      timeout is not set.
    csr_repo_name: An optional CSR repo name to be used in the trigger's
      triggerTemplate field. If this field is provided, github_repo_owner and
      github_repo_name should not be provided. Either csr_repo_name or both
      github_repo_owner and github_repo_name must be provided.
    github_repo_owner: An optional GitHub repo owner to be used in the trigger's
      github field. If this field is provided, github_repo_name must be provided
      and csr_repo_name should not be provided. Either csr_repo_name or both
      github_repo_owner and github_repo_name must be provided.
    github_repo_name: An optional GitHub repo name to be used in the trigger's
      github field. If this field is provided, github_repo_owner must be
      provided and csr_repo_name should not be provided. Either csr_repo_name or
      both github_repo_owner and github_repo_name must be provided.
    branch_pattern: An optional regex value to be used to trigger. If this value
      if provided, tag_pattern should not be provided. branch_pattern or
      tag_pattern must be provided.
    tag_pattern: An optional regex value to be used to trigger. If this value
      if provided, branch_pattern should not be provided. branch_pattern or
      tag_pattern must be provided.
    image: The image that will be built and deployed. The image can include a
      tag or digest.
    dockerfile_path: An optional path to the source repository's Dockerfile,
      relative to the source repository's root directory that is set to a
      substitution variable. If this value is not provided, 'Dockerfile' is
      used.
    app_name: An optional app name that is set to a substitution variable.
      If this value is None, the substitution variable is set to '' to indicate
      its absence.
    config_path: An optional path to the source repository's Kubernetes configs,
      relative to the source repository's root directory that is set to a
      substitution variable. If this value is None, the substitution variable is
      set to '' to indicate its absence.
    namespace: An optional Kubernetes namespace of the cluster to deploy to that
      is set to a substitution variable. If this value is None, the substitution
      variable is set to 'default'.
    expose_port: An optional port that the deployed application listens to that
      is set to a substitution variable. If this value is None, the substitution
      variable is set to 0 to indicate its absence.
    gcs_config_staging_path: An optional path to a GCS subdirectory to copy
      application configs that is set to a substitution variable. If this value
      is None, the substitution variable is set to '' to indicate its absence.
    cluster: The name of the target cluster to deploy to that is set to a
      substitution variable.
    location: The zone/region of the target cluster to deploy to that is set to
      a substitution variable.
    build_tags: Tags to append to build tags in addition to default tags.
    build_trigger_tags: Tags to append to build trigger tags in addition to
      default tags.

  Returns:
    messages.BuildTrigger, the Cloud BuildTrigger config.
  """

  substitutions = _BaseBuildSubstitutionsDict(dockerfile_path, app_name,
                                              config_path, expose_port, cluster,
                                              location, gcs_config_staging_path)
  if namespace is None:
    namespace = 'default'
  substitutions[_K8S_NAMESPACE_SUB_VAR] = namespace

  build_trigger = messages.BuildTrigger(
      name=name,
      description=description,
      build=CreateBuild(messages, build_timeout, True, None, image,
                        dockerfile_path, app_name, _VERSION, config_path,
                        namespace, expose_port, gcs_config_staging_path,
                        cluster, location, build_tags),
      substitutions=cloudbuild_util.EncodeTriggerSubstitutions(
          substitutions,
          messages))

  if csr_repo_name:
    build_trigger.triggerTemplate = messages.RepoSource(
        projectId=properties.VALUES.core.project.Get(required=True),
        repoName=csr_repo_name,
        branchName=branch_pattern,
        tagName=tag_pattern
    )
  elif github_repo_owner and github_repo_name:
    build_trigger.github = messages.GitHubEventsConfig(
        owner=github_repo_owner,
        name=github_repo_name,
        push=messages.PushFilter(
            branch=branch_pattern,
            tag=tag_pattern
        )
    )

  build_trigger.tags = _DEFAULT_TAGS[:]
  if build_trigger_tags:
    for tag in build_trigger_tags:
      build_trigger.tags.append(tag)

  return build_trigger


def CreatePRPreviewBuildTrigger(
    messages, name, description, build_timeout,
    github_repo_owner, github_repo_name,
    pr_pattern, preview_expiry_days, comment_control,
    image, dockerfile_path, app_name, config_path, expose_port,
    gcs_config_staging_path, cluster, location, build_tags,
    build_trigger_tags
):
  """Creates the Cloud BuildTrigger config that deploys an application when triggered by a PR create/update.

  Args:
    messages: Cloud Build messages module. This is the value returned from
      cloudbuild_util.GetMessagesModule().
    name: Trigger name, which must be unique amongst all triggers in a project.
    description: Trigger description.
    build_timeout: An optional maximum time a triggered build is run before it
      times out. For example, "2h15m5s" is 2 hours, 15 minutes, and 5 seconds.
      If you do not specify a unit, seconds is assumed. If this value is None, a
      timeout is not set.
    github_repo_owner: A GitHub repo owner to be used in the trigger's github
      field.
    github_repo_name: A GitHub repo name to be used in the trigger's github
      field.
    pr_pattern: A regex value that is the base branch that the PR is targeting,
      which triggers the creation of the PR preview deployment.
    preview_expiry_days: How long a deployed preview application can exist
      before it is expired, in days, that is set to a substitution variable.
    comment_control: Whether or not a user must comment /gcbrun to trigger
      the deployment build.
    image: The image that will be built and deployed. The image can include a
      tag or digest.
    dockerfile_path: An optional path to the source repository's Dockerfile,
      relative to the source repository's root directory that is set to a
      substitution variable. If this value is not provided, 'Dockerfile' is
      used.
    app_name: An optional app name that is set to a substitution variable.
      If this value is None, the substitution variable is set to '' to indicate
      its absence.
    config_path: An optional path to the source repository's Kubernetes configs,
      relative to the source repository's root directory that is set to a
      substitution variable. If this value is None, the substitution variable is
      set to '' to indicate its absence.
    expose_port: An optional port that the deployed application listens to that
      is set to a substitution variable. If this value is None, the substitution
      variable is set to 0 to indicate its absence.
    gcs_config_staging_path: An optional path to a GCS subdirectory to copy
      application configs that is set to a substitution variable. If this value
      is None, the substitution variable is set to '' to indicate its absence.
    cluster: The name of the target cluster to deploy to that is set to a
      substitution variable.
    location: The zone/region of the target cluster to deploy to that is set to
      a substitution variable.
    build_tags: Tags to append to build tags in addition to default tags.
    build_trigger_tags: Tags to append to build trigger tags in addition to
      default tags.

  Returns:
    messages.BuildTrigger, the Cloud BuildTrigger config.
  """

  substitutions = _BaseBuildSubstitutionsDict(dockerfile_path, app_name,
                                              config_path, expose_port, cluster,
                                              location, gcs_config_staging_path)
  substitutions[_PREVIEW_EXPIRY_SUB_VAR] = six.text_type(preview_expiry_days)

  build = messages.Build(
      steps=[
          _BuildBuildStep(messages, image),
          _PushBuildStep(messages, image),
          messages.BuildStep(
              id=_PREPARE_DEPLOY_BUILD_STEP_ID,
              name=_GKE_DEPLOY_PROD,
              entrypoint='sh',
              args=[
                  '-c',
                  _PREPARE_PREVIEW_DEPLOY_SCRIPT.format(
                      image=image,
                      cluster=_GKE_CLUSTER_SUB_VAR,
                      location=_GKE_LOCATION_SUB_VAR,
                      k8s_yaml_path=_K8S_YAML_PATH_SUB_VAR,
                      app_name=_APP_NAME_SUB_VAR,
                      k8s_annotations=_K8S_ANNOTATIONS_SUB_VAR,
                      expose_port=_EXPOSE_PORT_SUB_VAR,
                  )
              ]
          ),
          _SaveConfigsBuildStep(messages),
          messages.BuildStep(
              id=_APPLY_DEPLOY_BUILD_STEP_ID,
              name=_GKE_DEPLOY_PROD,
              entrypoint='sh',
              args=[
                  '-c',
                  _APPLY_PREVIEW_DEPLOY_SCRIPT
              ]
          ),
          messages.BuildStep(
              id=_ANNOTATE_PREVIEW_NAMESPACE_BUILD_STEP_ID,
              name='gcr.io/cloud-builders/kubectl',
              entrypoint='sh',
              args=[
                  '-c',
                  _ANNOTATE_PREVIEW_NAMESPACE_SCRIPT
              ]
          )
      ],
      substitutions=cloudbuild_util.EncodeSubstitutions(
          substitutions, messages),
      options=messages.BuildOptions(
          substitutionOption=messages.BuildOptions
          .SubstitutionOptionValueValuesEnum.ALLOW_LOOSE
      ),
      images=[image],
      artifacts=messages.Artifacts(
          objects=messages.ArtifactObjects(
              location='gs://' + _EXPANDED_CONFIGS_PATH_DYNAMIC,
              paths=['output/expanded/*']
          )
      )
  )

  if build_timeout is not None:
    try:
      # A bare number is interpreted as seconds.
      build_timeout_secs = int(build_timeout)
    except ValueError:
      build_timeout_duration = times.ParseDuration(build_timeout)
      build_timeout_secs = int(build_timeout_duration.total_seconds)
    build.timeout = six.text_type(build_timeout_secs) + 's'

  build.tags = _DEFAULT_PR_PREVIEW_TAGS[:]
  if build_tags:
    for tag in build_tags:
      build.tags.append(tag)

  github_config = messages.GitHubEventsConfig(
      owner=github_repo_owner,
      name=github_repo_name,
      pullRequest=messages.PullRequestFilter(
          branch=pr_pattern
      )
  )

  if comment_control:
    github_config.pullRequest.commentControl = messages.PullRequestFilter.CommentControlValueValuesEnum.COMMENTS_ENABLED

  build_trigger = messages.BuildTrigger(
      name=name,
      description=description,
      build=build,
      github=github_config,
      substitutions=cloudbuild_util.EncodeTriggerSubstitutions(
          substitutions, messages)
  )

  build_trigger.tags = _DEFAULT_PR_PREVIEW_TAGS[:]
  if build_trigger_tags:
    for tag in build_trigger_tags:
      build_trigger.tags.append(tag)

  return build_trigger


def CreateCleanPreviewBuildTrigger(messages, name, description,
                                   github_repo_owner, github_repo_name,
                                   cluster, location, build_tags,
                                   build_trigger_tags):
  """Creates the Cloud BuildTrigger config that deletes expired preview deployments.

  Args:
    messages: Cloud Build messages module. This is the value returned from
      cloudbuild_util.GetMessagesModule().
    name: Trigger name, which must be unique amongst all triggers in a project.
    description: Trigger description.
    github_repo_owner: A GitHub repo owner to be used in the trigger's github
      field.
    github_repo_name: A GitHub repo name to be used in the trigger's github
      field.
    cluster: The name of the target cluster to check for expired deployments
      that is set to a substitution variable.
    location: The zone/region of the target cluster to check for the expired
      deployments that is set to a substitution variable.
    build_tags: Tags to append to build tags in addition to default tags.
    build_trigger_tags: Tags to append to build trigger tags in addition to
      default tags.

  Returns:
    messages.BuildTrigger, the Cloud BuildTrigger config.
  """

  substitutions = {
      _GKE_CLUSTER_SUB_VAR: cluster,
      _GKE_LOCATION_SUB_VAR: location,
  }

  build_trigger = messages.BuildTrigger(
      name=name,
      description=description,
      github=messages.GitHubEventsConfig(
          owner=github_repo_owner,
          name=github_repo_name,
          push=messages.PushFilter(
              branch='$manual-only^',
          )
      ),
      build=messages.Build(
          steps=[
              messages.BuildStep(
                  id=_CLEANUP_PREVIEW_BUILD_STEP_ID,
                  name='gcr.io/cloud-builders/kubectl',
                  entrypoint='bash',
                  args=[
                      '-c',
                      _CLEANUP_PREVIEW_SCRIPT
                  ]
              )
          ],
          substitutions=cloudbuild_util.EncodeSubstitutions(
              substitutions, messages),
          timeout='600s'
      ),
      substitutions=cloudbuild_util.EncodeTriggerSubstitutions(
          substitutions, messages)
  )

  build_trigger.build.tags = _DEFAULT_CLEAN_PREVIEW_TAGS[:]
  if build_tags:
    for tag in build_tags:
      build_trigger.build.tags.append(tag)

  build_trigger.tags = _DEFAULT_CLEAN_PREVIEW_TAGS[:]
  if build_trigger_tags:
    for tag in build_trigger_tags:
      build_trigger.tags.append(tag)

  return build_trigger


def AddAnnotationToPrepareDeployStep(build_trigger, key, value):
  """Adds an additional annotation key value pair to the Prepare Deploy step, through the substitution variable.

  Args:
    build_trigger: BuildTrigger config to modify.
    key: Annotation key.
    value: Annotation value.
  """

  # BuildTrigger
  annotations_substitution = next((
      x for x in build_trigger.substitutions.additionalProperties
      if x.key == _K8S_ANNOTATIONS_SUB_VAR
  ), None)
  annotations_substitution.value = '{},{}={}'.format(
      annotations_substitution.value, key, value)

  # BuildTrigger.Build
  annotations_substitution = next((
      x for x in build_trigger.build.substitutions.additionalProperties
      if x.key == _K8S_ANNOTATIONS_SUB_VAR
  ), None)
  annotations_substitution.value = '{},{}={}'.format(
      annotations_substitution.value, key, value)


def _BaseBuildSubstitutionsDict(dockerfile_path, app_name, config_path,
                                expose_port, cluster, location,
                                gcs_config_staging_path):
  """Creates a base dict of substitutions for a Build or BuildTrigger to encode.

  The returned dict contains shared substitutions of Builds and BuildTriggers
  that this library creates.

  Args:
    dockerfile_path: Value for _DOCKERFILE_PATH_SUB_VAR substitution variable.
    app_name: Value for _APP_NAME_SUB_VAR substitution variable.
    config_path: Value for _K8S_YAML_PATH_SUB_VAR substitution variable.
    expose_port: Value for _EXPOSE_PORT_SUB_VAR substitution variable.
    cluster: Value for _GKE_CLUSTER_SUB_VAR substitution variable.
    location: Value for _GKE_LOCATION_SUB_VAR substitution variable.
    gcs_config_staging_path: Value for _OUTPUT_BUCKET_PATH_SUB_VAR substitution
      variable.

  Returns:
    Dict of substitutions mapped to values.
  """
  if not dockerfile_path:
    dockerfile_path = 'Dockerfile'

  if config_path is None:
    config_path = ''

  if not expose_port:
    expose_port = '0'
  else:
    expose_port = six.text_type(expose_port)

  return {
      _DOCKERFILE_PATH_SUB_VAR: dockerfile_path,
      _APP_NAME_SUB_VAR: app_name,
      _K8S_YAML_PATH_SUB_VAR: config_path,
      _EXPOSE_PORT_SUB_VAR: expose_port,
      _GKE_CLUSTER_SUB_VAR: cluster,
      _GKE_LOCATION_SUB_VAR: location,
      _OUTPUT_BUCKET_PATH_SUB_VAR: gcs_config_staging_path,
      _K8S_ANNOTATIONS_SUB_VAR: '',
  }


def _BuildBuildStep(messages, image):
  return messages.BuildStep(
      id=_BUILD_BUILD_STEP_ID,
      name='gcr.io/cloud-builders/docker',
      args=[
          'build',
          '--network',
          'cloudbuild',
          '--no-cache',
          '-t',
          image,
          '-f',
          '${}'.format(_DOCKERFILE_PATH_SUB_VAR),
          '.'
      ]
  )


def _PushBuildStep(messages, image):
  return messages.BuildStep(
      id=_PUSH_BUILD_STEP_ID,
      name='gcr.io/cloud-builders/docker',
      args=[
          'push',
          image,
      ]
  )


def _SaveConfigsBuildStep(messages):
  return messages.BuildStep(
      id=_SAVE_CONFIGS_BUILD_STEP_ID,
      name='gcr.io/cloud-builders/gsutil',
      entrypoint='bash',
      args=[
          '-c',
          _SAVE_CONFIGS_SCRIPT
      ]
  )
