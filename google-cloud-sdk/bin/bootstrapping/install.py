#!/usr/bin/env python
#
# Copyright 2013 Google Inc. All Rights Reserved.
#

"""Do initial setup for the Cloud SDK."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import bootstrapping

# pylint:disable=g-bad-import-order
import argparse
import os
import sys

from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import config
from googlecloudsdk.core import platforms_install
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.updater import update_manager
from googlecloudsdk.core.util import encoding
from googlecloudsdk import gcloud_main

# pylint:disable=superfluous-parens

_CLI = gcloud_main.CreateCLI([])


def ParseArgs():
  """Parse args for the installer, so interactive prompts can be avoided."""

  def Bool(s):
    return s.lower() in ['true', '1']

  parser = argparse.ArgumentParser()

  parser.add_argument('--usage-reporting',
                      default=None, type=Bool,
                      help='(true/false) Disable anonymous usage reporting.')
  parser.add_argument('--rc-path',
                      help=('Profile to update with PATH and completion. If'
                            ' given without --command-completion or'
                            ' --path-update in "quiet" mode, a line will be'
                            ' added to this profile for both command completion'
                            ' and path updating.'))
  parser.add_argument('--command-completion', '--bash-completion',
                      default=None, type=Bool,
                      help=('(true/false) Add a line for command completion in'
                            ' the profile. In "quiet" mode, if True and you do'
                            ' not provide--rc-path, the default profile'
                            ' will be updated.'))
  parser.add_argument('--path-update',
                      default=None, type=Bool,
                      help=('(true/false) Add a line for path updating in the'
                            ' profile. In "quiet" mode, if True and you do not'
                            ' provide --rc-path, the default profile will be'
                            ' updated.'))
  parser.add_argument('--disable-installation-options', action='store_true',
                      help='DEPRECATED.  This flag is no longer used.')
  parser.add_argument('--override-components', nargs='*',
                      help='Override the components that would be installed by '
                      'default and install these instead.')
  parser.add_argument('--additional-components', nargs='+',
                      help='Additional components to install by default.  These'
                      ' components will either be added to the default install '
                      'list, or to the override-components (if provided).')
  # Must have a None default so properties are not always overridden when the
  # arg is not provided.
  parser.add_argument('--quiet', '-q', default=None,
                      action=actions.StoreConstProperty(
                          properties.VALUES.core.disable_prompts, True),
                      help='Disable all interactive prompts. If input is '
                      'required, defaults will be used or an error will be '
                      'raised')

  return parser.parse_args(bootstrapping.GetDecodedArgv()[1:])


def Prompts(usage_reporting):
  """Display prompts to opt out of usage reporting.

  Args:
    usage_reporting: bool, If True, enable usage reporting. If None, check
    the environmental variable. If None, check if its alternate release channel.
    If not, ask.
  """

  if usage_reporting is None:

    if encoding.GetEncodedValue(
        os.environ, 'CLOUDSDK_CORE_DISABLE_USAGE_REPORTING') is not None:
      usage_reporting = not encoding.GetEncodedValue(
          os.environ, 'CLOUDSDK_CORE_DISABLE_USAGE_REPORTING')
    else:
      if config.InstallationConfig.Load().IsAlternateReleaseChannel():
        usage_reporting = True
        print("""
    Usage reporting is always on for alternate release channels.
    """)
      else:
        print("""
To help improve the quality of this product, we collect anonymized usage data
and anonymized stacktraces when crashes are encountered; additional information
is available at <https://cloud.google.com/sdk/usage-statistics>. This data is
handled in accordance with our privacy policy
<https://policies.google.com/privacy>. You may choose to opt in this
collection now (by choosing 'Y' at the below prompt), or at any time in the
future by running the following command:

    gcloud config set disable_usage_reporting false
""")

        usage_reporting = console_io.PromptContinue(
            prompt_string='Do you want to help improve the Google Cloud SDK',
            default=False)
  properties.PersistProperty(
      properties.VALUES.core.disable_usage_reporting, not usage_reporting,
      scope=properties.Scope.INSTALLATION)


def Install(override_components, additional_components):
  """Do the normal installation of the Cloud SDK."""
  # Install the OS specific wrapper scripts for gcloud and any pre-configured
  # components for the SDK.
  to_install = (override_components if override_components is not None
                else bootstrapping.GetDefaultInstalledComponents())

  # If there are components that are to be installed by default, this means we
  # are working with an incomplete Cloud SDK package.  This comes from the curl
  # installer or the Windows installer or downloading a seed directly.  In this
  # case, we will update to the latest version of the SDK.  If there are no
  # default components, this is a fully packaged SDK.  If there are additional
  # components requested, just install them without updating the version.
  update = bool(to_install)

  if additional_components:
    to_install.extend(additional_components)

  InstallOrUpdateComponents(to_install, update=update)

  # Show the list of components if there were no pre-configured ones.
  if not to_install:
    _CLI.Execute(['--quiet', 'components', 'list'])


def ReInstall(component_ids):
  """Do a forced reinstallation of the Cloud SDK.

  Args:
    component_ids: [str], The components that should be automatically installed.
  """
  to_install = bootstrapping.GetDefaultInstalledComponents()
  to_install.extend(component_ids)

  # We always run in update mode here because we are reinstalling and trying
  # to get the latest version anyway.
  InstallOrUpdateComponents(component_ids, update=True)


def InstallOrUpdateComponents(component_ids, update):
  """Installs or updates the given components.

  Args:
    component_ids: [str], The components to install or update.
    update: bool, True if we should run update, False to run install.  If there
      are no components to install, this does nothing unless in update mode (in
      which case everything gets updated).
  """
  # If we are in installation mode, and there are no specific components to
  # install, there is nothing to do.  If there are no components in update mode
  # things will still get updated to latest.
  if not update and not component_ids:
    return

  print("""
This will install all the core command line tools necessary for working with
the Google Cloud Platform.
""")

  verb = 'update' if update else 'install'
  _CLI.Execute(
      ['--quiet', 'components', verb, '--allow-no-backup'] + component_ids)


def main():
  pargs = ParseArgs()
  update_manager.RestartIfUsingBundledPython(sdk_root=config.Paths().sdk_root,
                                             command=__file__)
  reinstall_components = encoding.GetEncodedValue(
      os.environ, 'CLOUDSDK_REINSTALL_COMPONENTS')
  try:
    if reinstall_components:
      ReInstall(reinstall_components.split(','))
    else:
      Prompts(pargs.usage_reporting)
      bootstrapping.CommandStart('INSTALL', component_id='core')
      if not config.INSTALLATION_CONFIG.disable_updater:
        Install(pargs.override_components, pargs.additional_components)

      platforms_install.UpdateRC(
          completion_update=pargs.command_completion,
          path_update=pargs.path_update,
          rc_path=pargs.rc_path,
          bin_path=bootstrapping.BIN_DIR,
          sdk_root=bootstrapping.SDK_ROOT,
      )

      print("""\

For more information on how to get started, please visit:
  https://cloud.google.com/sdk/docs/quickstarts

""")
  except exceptions.ToolException as e:
    print(e)
    sys.exit(1)


if __name__ == '__main__':
  main()
