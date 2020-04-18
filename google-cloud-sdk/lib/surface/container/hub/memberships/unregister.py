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
"""The unregister-cluster command for removing clusters from the Hub."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import textwrap

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.hub import agent_util
from googlecloudsdk.command_lib.container.hub import api_util
from googlecloudsdk.command_lib.container.hub import exclusivity_util
from googlecloudsdk.command_lib.container.hub import kube_util
from googlecloudsdk.command_lib.container.hub import util as hub_util
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log


class Unregister(base.DeleteCommand):
  r"""Unregister a cluster from Hub.

  This command unregisters a cluster with the Hub by:

    1. Deleting the Hub Membership resource for this cluster (a.k.a
       `{parent_command} delete`).
    2. Removing the corresponding in-cluster Kubernetes Resources that make the
       cluster exclusive to one Hub (a.k.a `kubectl delete memberships
       membership`).
    3. Uninstalling the Connect Agent from this cluster (a.k.a
       `kubectl delete on the gke-connect namespace`).

  The unregister command makes additional internal checks to ensure that all
  three steps can be safely done to properly clean-up in-Hub and in-cluster
  resources.

  To register a non-GKE cluster use --context flag (with an optional
  --kubeconfig flag).

  To register a GKE cluster use --gke-cluster or --gke-uri flag (no --kubeconfig
  flag is required).

  To only delete the Hub membership resource, consider using the command:
  `{parent_command} delete`. This command is intended to delete stale Hub
  Membership resources as doing so on a fully registered cluster will skip some
  of the steps above and orphan in-cluster resources and agent connections to
  Google.

  ## EXAMPLES

    Unregister a non-GKE cluster referenced from a specific kubeconfig file:

      $ {command} my-cluster \
        --context=my-cluster-context \
        --kubeconfig=/home/user/custom_kubeconfig

    Unregister a non-GKE cluster referenced from the default kubeconfig file:

      $ {command} my-cluster --context=my-cluster-context

    Unregister a GKE cluster referenced from a GKE URI:

      $ {command} my-cluster \
        --gke-uri=my-cluster-gke-uri

    Unregister a GKE cluster referenced from a GKE Cluster location and name:

      $ {command} my-cluster \
        --gke-cluster=my-cluster-region-or-zone/my-cluster

  """

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        'CLUSTER_NAME',
        type=str,
        help=textwrap.dedent("""\
            The membership name that corresponds to the cluster being
            unregistered. To get list of all the memberships on the Hub,
            consider using the command: `{parent_command} list`.
         """),
    )
    hub_util.AddUnRegisterCommonArgs(parser)

    if cls.ReleaseTrack() is base.ReleaseTrack.ALPHA:
      workload_identity = parser.add_group(
          help='Workload Identity', hidden=True)
      workload_identity.add_argument(
          '--manage-workload-identity-bucket',
          hidden=True,
          action='store_true',
          help=textwrap.dedent("""\
            Set this option if --manage-workload-identity-bucket was set when
            the cluster was initially registered with Hub. Setting this option
            will cause the bucket to be deleted.
            Requires gcloud alpha.
            """),
      )

  def Run(self, args):
    project = arg_utils.GetFromNamespace(args, '--project', use_defaults=True)
    kube_client = kube_util.KubernetesClient(args)
    kube_client.CheckClusterAdminPermissions()
    kube_util.ValidateClusterIdentifierFlags(kube_client, args)
    membership_id = args.CLUSTER_NAME

    # Delete membership from Hub API.
    try:
      name = 'projects/{}/locations/global/memberships/{}'.format(
          project, membership_id)
      api_util.DeleteMembership(name, self.ReleaseTrack())
    except apitools_exceptions.HttpUnauthorizedError as e:
      raise exceptions.Error(
          'You are not authorized to unregister clusters from project [{}]. '
          'Underlying error: {}'.format(project, e))
    except apitools_exceptions.HttpNotFoundError as e:
      log.status.Print(
          'Membership [{}] for the cluster [{}] was not found on the Hub. '
          'It may already have been deleted, or it may never have existed.'
          .format(name, args.CLUSTER_NAME))

    # enable_workload_identity and manage_workload_identity_bucket are only
    # properties if we are on the alpha track
    if (self.ReleaseTrack() is base.ReleaseTrack.ALPHA and
        args.manage_workload_identity_bucket):
      # The issuer URL from the cluster indicates which bucket to delete.
      # --manage-workload-identity-bucket always uses the cluster's
      # built-in endpoints.
      openid_config_json = None
      try:
        openid_config_json = kube_client.GetOpenIDConfiguration()
      except exceptions.Error as e:
        log.status.Print(
            'Cannot get the issuer URL that identifies the bucket associated '
            'with this membership. Please double check that it is possible to '
            'access the /.well-known/openid-configuration endpoint on the '
            'cluster: {}'.format(e))

      if openid_config_json:
        issuer_url = json.loads(openid_config_json).get('issuer')
        if not issuer_url:
          log.status.Print(
              'Cannot get the issuer URL that identifies the bucket associated '
              'with this membership. The OpenID Config from '
              '/.well-known/openid-configuration is missing the issuer field: '
              '{}'.format(openid_config_json))

        try:
          api_util.DeleteWorkloadIdentityBucket(issuer_url)
        except exceptions.Error as e:
          log.status.Print(
              'Failed to delete bucket for issuer {}: {}'.format(issuer_url, e))

    # Get namespace for the connect resource label.
    selector = '{}={}'.format(agent_util.CONNECT_RESOURCE_LABEL, project)
    namespaces = kube_client.NamespacesWithLabelSelector(selector)
    if not namespaces:
      log.status.Print('There\'s no namespace for the label [{}]. '
                       'If [gke-connect] is labeled with another project, '
                       'You\'ll have to manually delete the namespace. '
                       'You can find all namespaces by running:\n'
                       '  `kubectl get ns -l {}`'.format(
                           agent_util.CONNECT_RESOURCE_LABEL,
                           agent_util.CONNECT_RESOURCE_LABEL))

    # Delete in-cluster membership resources.
    try:
      exclusivity_util.DeleteMembershipResources(kube_client)
    except exceptions.Error as e:
      log.status.Print(
          '{} error in deleting in-cluster membership resources. '
          'You can manually delete these membership related '
          'resources from your cluster by running the command:\n'
          '  `kubectl delete memberships membership`.\nBy doing so, '
          'the cluster will lose its association to the Hub in '
          'project [{}] and can be registered into a different '
          'project. '.format(e, project))

    # Delete the connect agent.
    agent_util.DeleteConnectNamespace(kube_client, args)
