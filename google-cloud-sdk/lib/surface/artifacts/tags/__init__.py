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
  """Manage Artifact Registry tags.

  ## EXAMPLES

  To create tag with the name `my-tag` for version `1.0.0` of package `my-pkg`
  in the current project with `artifacts/repository` and `artifacts/location`
  properties are set, run:

    $ {command} create my-tag --package=my-pkg --version=1.0.0

  To list all tags under package `my-pkg`, run:

    $ {command} list --package=my-pkg

  To update tag `my-tag` from a different version to version `1.0.0` of package
  `my-pkg`, run:

    $ {command} update my-tag --version=1.0.0 --package=my-pkg

  To delete tag `my-tag` of package `my-pkg`, run:

    $ {command} delete my-tag --package=my-pkg
  """
