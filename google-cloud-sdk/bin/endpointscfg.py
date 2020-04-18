#!/usr/bin/env python
#
# Copyright 2015 Google Inc. All Rights Reserved.
#

"""A convenience wrapper for endpointscfg.py for appengine for python."""

from __future__ import absolute_import
from __future__ import unicode_literals
import os

from bootstrapping import bootstrapping
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core.updater import update_manager


def main():
  """Runs endpointscfg.py."""
  update_manager.UpdateManager.EnsureInstalledAndRestart(
      ['app-engine-python'],
      command=__file__)

  bootstrapping.ExecutePythonTool(
      os.path.join('platform', 'google_appengine'), 'endpointscfg.py')


if __name__ == '__main__':
  bootstrapping.DisallowPython3()
  try:
    bootstrapping.CommandStart('endpointscfg', component_id='core')
    bootstrapping.CheckUpdates('endpointscfg')
    main()
  except Exception as e:  # pylint: disable=broad-except
    exceptions.HandleError(e, 'endpointscfg')
