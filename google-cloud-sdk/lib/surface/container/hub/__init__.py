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
"""Command group for GKE Hub."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Hub(base.Group):
  """Centrally manage features and services on all your Kubernetes clusters with Hub.

  The command group to register GKE or other Kubernetes clusters running in a
  variety of environments, including Google cloud, on premises in customer
  datacenters, or other third party clouds with Hub. Hub provides a centralized
  control-plane to managed features and services on all registered clusters.

  A registered cluster is always associated with a Membership, a resource
  within Hub.

  ## EXAMPLES

  Manage memberships of all your GKE and other Kubernetes clusters with Hub:

    $ {command} memberships --help

  Manage features on all memberships:

    $ {command} features --help
  """
