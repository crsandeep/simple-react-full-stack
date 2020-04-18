# Copyright 2017 Google Inc. All Rights Reserved.
#
"""A convenience wrapper for starting Dataflow SQL shell."""

import os

import bootstrapping
from googlecloudsdk.command_lib.util import java
from googlecloudsdk.core.updater import update_manager

# Path to the unpacked component
_COMPONENT_DIR = os.path.join('platform', 'dataflow-sql')

# Path to the directory of unpacked jars relative to the SDK root
_JAR_DIR = os.path.join(_COMPONENT_DIR, 'lib')

# The main jar in the _JAR_DIR, must be first for precedence
_MAIN_JAR = 'dataflow_sql_shell.jar'

# Name of the main class
_CLASSNAME = 'org.apache.beam.sdk.extensions.sql.jdbc.BeamSqlLine'


def main():
  """Launches the Dataflow SQL shell."""
  bootstrapping.CommandStart('dataflow-sql', component_id='dataflow-sql')
  bootstrapping.CheckUpdates('dataflow-sql')
  update_manager.UpdateManager.EnsureInstalledAndRestart(
      ['dataflow-sql'], command=__file__)
  java_bin = java.RequireJavaInstalled('Dataflow SQL')
  bootstrapping.ExecuteJavaClass(
      java_bin,
      jar_dir=_JAR_DIR,
      main_jar=_MAIN_JAR,
      main_class=_CLASSNAME,
      main_args=['-nn', 'DFSQL', '-u', 'jdbc:beam:userAgent=DataflowSQL'])


if __name__ == '__main__':
  main()
