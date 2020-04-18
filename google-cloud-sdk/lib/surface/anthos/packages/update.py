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
"""Update a local package with changes from a remote source repo."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.anthos import anthoscli_backend
from googlecloudsdk.command_lib.anthos import flags
from googlecloudsdk.core import log


_LOCAL_DIR_HELP = ('The local package directory to update. Can optionally '
                   'include a git reference  (GIT_REF) to a tag, branch or '
                   'commit hash to update to. '
                   'Defaults to last fetched git-ref.')
_LOCAL_DIR_META = 'LOCAL_DIR[@GIT_REF]'


class Update(base.BinaryBackedCommand):
  """Update a local package with changes from a remote source repo."""
  detailed_help = {
      'EXAMPLES': """
      To update local package `~/my-package-dir`:

        $ {command} ~/my-package-dir

      To update my-package-dir/ to match the v1.3 tag at git URL
      https://github.com/my-other-account/foo.git:

        $ {command} my-package-dir@v1.3 --repo-uri https://github.com/my-other-account/foo.git

      To update by applying a git patch:

        $ git add my-package-dir/
        $ git commit -m "package updates"
        $ {command} my-package-dir/@master --strategy alpha-git-patch
      """,
  }

  @staticmethod
  def Args(parser):
    flags.GetLocalDirFlag(help_override=_LOCAL_DIR_HELP,
                          metavar=_LOCAL_DIR_META).AddToParser(parser)
    flags.GetRepoURIFlag(positional=False, required=False, metavar='REPO_URI',
                         help_override='git repo url for updating contents. '
                                       'Defaults to the url the package was '
                                       'fetched from.').AddToParser(parser)
    flags.GetStrategyFlag().AddToParser(parser)
    flags.GetDryRunFlag().AddToParser(parser)

  def Run(self, args):
    is_verbose = args.verbosity == 'debug'
    command_executor = anthoscli_backend.AnthosCliWrapper()
    log.status.Print('Syncing dir [{}]'.format(args.LOCAL_DIR))
    # kpt update requires relative path
    work_dir, at_symbol, git_ref = args.LOCAL_DIR.partition('@')
    pkg_dir = at_symbol.join(['.', git_ref]) if git_ref else '.'
    response = command_executor(command='update',
                                local_dir=pkg_dir,
                                repo_uri=args.REPO_URI,
                                strategy=args.strategy,
                                dry_run=args.dry_run,
                                verbose=is_verbose,
                                show_exec_error=args.show_exec_error,
                                env=anthoscli_backend.GetEnvArgsForCommand(),
                                execution_dir=work_dir)
    return self._DefaultOperationResponseHandler(response)
