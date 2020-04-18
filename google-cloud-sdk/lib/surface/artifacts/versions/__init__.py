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
"""Command group for Artifact Registry versions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


class Versions(base.Group):
  """Manage Artifact Registry package versions.

  ## EXAMPLES

  To list all versions for a package when the `artifacts/repository` and
  `artifacts/location` properties are set to a repository in the current
  project, run:

    $ {command} list --package=my-pkg

  To delete version `1.0.0` under package `my-pkg`, run:

      $ {command} delete 1.0.0 --package=my-pkg

  To delete version `1.0.0` under package `my-pkg` with its tags, run:

      $ {command} delete 1.0.0 --package=my-pkg --delete-tags
  """
