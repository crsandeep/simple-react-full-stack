# Copyright 2017 Google Inc. All Rights Reserved.
#
"""Wrapper for Gcloud-installed Schema Conversion Tool."""

import os

import bootstrapping
from googlecloudsdk.command_lib.util import java
from googlecloudsdk.core.updater import update_manager

# Path to the unpacked component
_COMPONENT_DIR = os.path.join(bootstrapping.SDK_ROOT,
                              'platform', 'schema_conversion_tool')

# Path to the directory of unpacked jars relative to the SDK root
_JAR_DIR = os.path.join(_COMPONENT_DIR, 'lib')

_COMPONENT_ID = 'schema-conversion-tool'


def main():
  """Launches the Schema Conversion Tool."""
  bootstrapping.CommandStart(_COMPONENT_ID, component_id=_COMPONENT_ID)
  bootstrapping.CheckUpdates(_COMPONENT_ID)
  update_manager.UpdateManager.EnsureInstalledAndRestart(
      [_COMPONENT_ID], command=__file__)
  try:
    java_bin = java.RequireJavaInstalled('Schema Conversion Tool',
                                         min_version=9)
    java_9plus = True
  except java.JavaVersionError:
    java_bin = java.RequireJavaInstalled('Schema Conversion Tool',
                                         min_version=8)
    java_9plus = False

  os.environ.setdefault('SCT_UPDATE_CHECK', 'false')
  jar_name = 'schema_conversion_gui.jar'
  main_jar = os.path.join(_JAR_DIR, jar_name)

  # Accept a platform-appropriate default added as 1st arg in sct.sh/sct.cmd.
  working_dir_default = bootstrapping.GetDecodedArgv()[1]

  flags = [
      '-Djava.util.logging.manager=org.apache.logging.log4j.jul.LogManager',
      '-Dspring.profiles.active=production',
      '-Dgcloud.component.dir={}'.format(_COMPONENT_DIR),
      '-Dsct.working.dir.default={}'.format(working_dir_default),
      '-jar',
      main_jar,
  ]

  if java_9plus:
    # Open modules to reflection explicitly to avoid Java 9+ warnings.
    flags = [
        '--add-opens', 'java.base/java.io=ALL-UNNAMED',
        '--add-opens', 'java.base/java.lang=ALL-UNNAMED',
        '--add-opens', 'java.base/java.net=ALL-UNNAMED',
        '--add-opens', 'java.rmi/sun.rmi.transport=ALL-UNNAMED',
    ] + flags

  bootstrapping.ExecuteJarTool(
      java_bin,
      _JAR_DIR,
      jar_name,
      None,  # No main classname for Springboot JAR. Use -jar flag instead.
      flags,
      '--server.address=127.0.0.1')


if __name__ == '__main__':
  main()
