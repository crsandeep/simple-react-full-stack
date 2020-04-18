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
"""Command group for GKE Hub memberships."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


DETAILED_HELP = {
    'brief': 'Manage Google Kubernetes Hub memberships.',
    'DESCRIPTION': """Manage Google Kubernetes Hub memberships.""",
    'EXAMPLES': """
    Create a membership:

      $ gcloud container memberships create a-membership
          --description="Description of a-membership."

    Check the status of a membership:

      $ gcloud container memberships describe a-membership

    List the memberships in a project:

      $ gcloud container memberships list

    Delete a membership:

      $ gcloud container memberships delete a-membership

    Register a cluster referenced from the default kubeconfig file, installing the
    Connect agent:

        $ {command} register my-cluster \
            --context=my-cluster-context \
            --service-account-key-file=/tmp/keyfile.json

    Upgrade the Connect agent in a cluster:

        $ {command} register my-cluster \
            --context=my-cluster-context \
            --service-account-key-file=/tmp/keyfile.json

    Register a cluster and output a manifest that can be used to install the
    Connect agent:

        $ {command} register my-cluster \
            --context=my-cluster-context \
            --manifest-output-file=/tmp/manifest.yaml \
            --service-account-key-file=/tmp/keyfile.json
    """
}


@base.Deprecate(
    is_removed=False,
    warning=(
        'This command group is deprecated. '
        'Please use `gcloud container hub memberships` command group instead.'),
    error=(
        'This command group has been removed. '
        'Please use `gcloud container hub memberships` command group instead.'))
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Memberships(base.Group):
  """Manage Google Kubernetes Hub memberships."""
  detailed_help = DETAILED_HELP
