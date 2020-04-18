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
"""Command group for Artifact Registry repositories."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


class Repositories(base.Group):
  """Manage Artifact Registry repositories.

  ## EXAMPLES

  To create a repository with the name `my-repo`, run:

    $ {command} create my-repo

  To delete a repository with the name `my-repo`, run:

    $ {command} delete my-repo

  To list all Artifact Registry repositories, run:

    $ {command} list

  To set an IAM policy for repository `my-repo`, run:

    $ {command} set-iam-policy my-repo policy.json

  To get an IAM policy for repository `my-repo`, run:

    $ {command} get-iam-policy my-repo

  To add an IAM policy binding for the role of 'roles/editor' for the user
  'test-user@gmail.com' on  repository `my-repo`, run:

    $ {command} add-iam-policy-binding my-repo
    --member='user:test-user@gmail.com' --role='roles/editor'

  To remove an IAM policy binding for the role of 'roles/editor' for the user
  'test-user@gmail.com' on repository `my-repo`, run:

    $ {command} remove-iam-policy-binding my-repo
    --member='user:test-user@gmail.com' --role='roles/editor'
  """
