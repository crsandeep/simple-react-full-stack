# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Command group for Artifact Registry container images."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


class Images(base.Group):
  """Manage Artifact Registry container images.

  To list images under the current project, repository, and location:

      $ {command} list

  To list images under repository `my-repo`, project `my-project`, in
  `us-central1`:

      $ {command} list us-central1-docker.pkg.dev/my-project/my-repo

  To list images with tags, under repository `my-repo`, project `my-project`
  across all locations:

      $ {command} list docker.pkg.dev/my-project/my-repo --include-tags

  To list all images under image `busy-box`, in repository `my-repo`, project
  `my-project` across all locations:

      $ {command} list docker.pkg.dev/my-project/my-repo/busy-box

  To delete image `busy-box` in `us-west1` and all of its digests and tags:

      $ {command} delete
      us-west1-docker.pkg.dev/my-project/my-repository/busy-box

  To delete image digest `abcxyz` under image `busy-box`:

      $ {command} delete
      us-west1-docker.pkg.dev/my-project/my-repository/busy-box@sha256:abcxyz

  To delete image digest `abcxyz` under image `busy-box` while there're some
  other tags associate with the digest:

      $ {command} delete
      us-west1-docker.pkg.dev/my-project/my-repository/busy-box@sha256:abcxyz
      --delete-tags

  To delete an image digest and its only tag `my-tag` under image `busy-box`:

      $ {command} delete
      us-west1-docker.pkg.dev/my-project/my-repository/busy-box:my-tag
  """
