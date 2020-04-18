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
"""The register-cluster command for registering external clusters with the Hub."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.util import exceptions as core_api_exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.hub import agent_util as agent_util
from googlecloudsdk.command_lib.container.hub import api_util as api_util
from googlecloudsdk.command_lib.container.hub import exclusivity_util as exclusivity_util
from googlecloudsdk.command_lib.container.hub import kube_util as kube_util
from googlecloudsdk.command_lib.container.hub import util as hub_util
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import files


SERVICE_ACCOUNT_KEY_FILE_FLAG = '--service-account-key-file'
DOCKER_CREDENTIAL_FILE_FLAG = '--docker-credential-file'


class Register(base.CreateCommand):
  r"""Registers a cluster with Google Cloud Platform.

  This command registers a cluster referenced from a kubeconfig file with Google
  Cloud Platform. It also installs the Connect agent into this cluster, or
  updates the Connect agent in a previously-registered cluster.

  ## EXAMPLES

  Register a cluster referenced from the default kubeconfig file, installing the
  Connect agent:

      $ {command} my-cluster \
          --context=my-cluster-context \
          --service-account-key-file=/tmp/keyfile.json

  Upgrade the Connect agent in a cluster:

      $ {command} my-cluster \
          --context=my-cluster-context \
          --service-account-key-file=/tmp/keyfile.json

  Register a cluster and output a manifest that can be used to install the
  Connect agent:

      $ {command} my-cluster \
          --context=my-cluster-context \
          --manifest-output-file=/tmp/manifest.yaml \
          --service-account-key-file=/tmp/keyfile.json
  Register a cluster with a specific version of GKE Connect:

      $ {command} my-cluster \
          --context=my-cluster-context \
          --service-account-key-file=/tmp/keyfile.json \
          --version=gkeconnect_20190802_02_00
  """

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        'CLUSTER_NAME',
        type=str,
        help='The name of the cluster being registered.',
    )
    hub_util.AddCommonArgs(parser)
    parser.add_argument(
        '--manifest-output-file',
        type=str,
        help=textwrap.dedent("""\
            The full path of the file into which the Connect agent installation
            manifest should be stored. If this option is provided, then the
            manifest will be written to this file and will not be deployed into
            the cluster by gcloud, and it will need to be deployed manually.
          """),
    )
    parser.add_argument(
        SERVICE_ACCOUNT_KEY_FILE_FLAG,
        required=True,
        type=str,
        help='The JSON file of a Google Cloud service account private key.',
    )
    parser.add_argument(
        '--proxy',
        type=str,
        help=textwrap.dedent("""\
            The proxy address in the format of http[s]://{hostname}.
            The proxy must support the HTTP CONNECT method in order for this
            connection to succeed.
          """),
    )
    parser.add_argument(
        '--version',
        type=str,
        help=textwrap.dedent("""\
        The version of the connect agent to install/upgrade if not using the
        latest connect version.
          """),
    )
    parser.add_argument(
        DOCKER_CREDENTIAL_FILE_FLAG,
        type=str,
        hidden=True,
        help=textwrap.dedent("""\
            The credentials to be used if a private registry is provided and
            auth is required. The contents of the file will be stored into a
            Secret and referenced from the imagePullSecrets of the Connect
            agent workload.
          """),
    )
    parser.add_argument(
        '--docker-registry',
        type=str,
        hidden=True,
        help=textwrap.dedent("""\
            The registry to pull GKE Connect agent image if not using
            gcr.io/gkeconnect.
          """),
    )

  def Run(self, args):
    project = arg_utils.GetFromNamespace(args, '--project', use_defaults=True)
    # TODO(b/145953996): api_utils map release_track to an api_version.
    # All old commands needs to use 'v1beta1' irrespective of the release track,
    # till they are removed (already deprecation policy applied).
    self.release_track = base.ReleaseTrack.BETA
    # This incidentally verifies that the kubeconfig and context args are valid.
    kube_client = kube_util.OldKubernetesClient(args)
    uuid = kube_util.GetClusterUUID(kube_client)

    self._VerifyClusterExclusivity(kube_client, project, args.context, uuid)

    # Read the service account files provided in the arguments early, in order
    # to catch invalid files before performing mutating operations.
    try:
      service_account_key_data = hub_util.Base64EncodedFileContents(
          args.service_account_key_file)
    except files.Error as e:
      raise exceptions.Error('Could not process {}: {}'.format(
          SERVICE_ACCOUNT_KEY_FILE_FLAG, e))

    docker_credential_data = None
    if args.docker_credential_file:
      try:
        docker_credential_data = hub_util.Base64EncodedFileContents(
            args.docker_credential_file)
      except files.Error as e:
        raise exceptions.Error('Could not process {}: {}'.format(
            DOCKER_CREDENTIAL_FILE_FLAG, e))

    gke_cluster_self_link = api_util.GKEClusterSelfLink(kube_client)

    # The full resource name of the membership for this registration flow.
    name = 'projects/{}/locations/global/memberships/{}'.format(project, uuid)
    # Attempt to create a membership.
    already_exists = False
    try:
      exclusivity_util.ApplyMembershipResources(kube_client, project)
      obj = api_util.CreateMembership(project, uuid, args.CLUSTER_NAME,
                                      gke_cluster_self_link, uuid,
                                      self.release_track)
    except apitools_exceptions.HttpConflictError as e:
      # If the error is not due to the object already existing, re-raise.
      error = core_api_exceptions.HttpErrorPayload(e)
      if error.status_description != 'ALREADY_EXISTS':
        raise

      # The membership already exists. Check to see if it has the same
      # description (i.e., user-visible cluster name).
      #
      # This intentionally does not verify that the gke_cluster_self_link is
      # equivalent: this check is meant to prevent the user from updating the
      # Connect agent in a cluster that is different from the one that they
      # expect, and is not required for the proper functioning of the agent or
      # the Hub.
      obj = api_util.GetMembership(name, self.release_track)
      if obj.description != args.CLUSTER_NAME:
        # A membership exists, but does not have the same description. This is
        # possible if two different users attempt to register the same
        # cluster, or if the user is upgrading and has passed a different
        # cluster name. Treat this as an error: even in the upgrade case,
        # this is useful to prevent the user from upgrading the wrong cluster.
        raise exceptions.Error(
            'There is an existing membership, [{}], that conflicts with [{}]. '
            'Please delete it before continuing:\n\n'
            '  gcloud {}container memberships delete {}'.format(
                obj.description, args.CLUSTER_NAME,
                hub_util.ReleaseTrackCommandPrefix(self.ReleaseTrack()), name))

      # The membership exists and has the same description.
      already_exists = True
      console_io.PromptContinue(
          message='A membership for [{}] already exists. Continuing will '
          'reinstall the Connect agent deployment to use a new image (if one '
          'is available).'.format(args.CLUSTER_NAME),
          cancel_on_no=True)

    # A membership exists. Attempt to update the existing agent deployment, or
    # install a new agent if necessary.
    if already_exists:
      obj = api_util.GetMembership(name, self.release_track)
      agent_util.DeployConnectAgent(kube_client, args, service_account_key_data,
                                    docker_credential_data, name,
                                    self.release_track)
      return obj

    # No membership exists. Attempt to create a new one, and install a new
    # agent.
    try:
      agent_util.DeployConnectAgent(kube_client, args, service_account_key_data,
                                    docker_credential_data, name,
                                    self.release_track)
    except:
      api_util.DeleteMembership(name, self.release_track)
      exclusivity_util.DeleteMembershipResources(kube_client)
      raise
    return obj

  def _VerifyClusterExclusivity(self, kube_client, project, context, uuid):
    """Verifies that the cluster can be registered to the project.

    The ensures cluster exclusivity constraints are not violated as well as
    ensuring the user is authorized to register the cluster to the project.

    Args:
      kube_client: A KubernetesClient
      project: A project ID the user is attempting to register the cluster with.
      context: The kubernetes cluster context.
      uuid: The UUID of the kubernetes cluster.

    Raises:
      exceptions.Error: If exclusivity constraints are violated or the user is
        not authorized to register to the cluster.
    """
    authorized_projects = hub_util.UserAccessibleProjectIDSet()
    registered_project = exclusivity_util.GetMembershipCROwnerID(kube_client)

    if registered_project:
      if registered_project not in authorized_projects:
        raise exceptions.Error(
            'The cluster is already registered to [{}], which you are not '
            'authorized to access.'.format(registered_project))
      elif registered_project != project:
        raise exceptions.Error(
            'This cluster is already registered to [{}]. '
            'Please unregister this cluster before continuing:\n\n'
            '  gcloud {}container hub unregister-cluster --project {} --context {}'
            .format(registered_project,
                    hub_util.ReleaseTrackCommandPrefix(self.release_track),
                    registered_project, context))

    if project not in authorized_projects:
      raise exceptions.Error(
          'The project you are attempting to register with [{}] either '
          'doesn\'t exist or you are not authorized to access it.'.format(
              project))

    try:
      registered_membership_project = api_util.ProjectForClusterUUID(
          uuid, [project, registered_project], self.release_track)
    except apitools_exceptions.HttpNotFoundError as e:
      raise exceptions.Error(
          'Could not access Memberships API. Is your project whitelisted for '
          'API access? Underlying error: {}'.format(e))

    if registered_membership_project and registered_membership_project != project:
      raise exceptions.Error(
          'This cluster is already registered to [{}]. '
          'Please unregister this cluster before continuing:\n\n'
          '  gcloud {}container hub unregister-cluster --project {} --context {}'
          .format(registered_membership_project,
                  hub_util.ReleaseTrackCommandPrefix(self.release_track),
                  registered_membership_project, context))
