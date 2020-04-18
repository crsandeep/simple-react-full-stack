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
"""Command for running a local development environment."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import contextlib
import os.path
import signal
import subprocess
import sys
import tempfile

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.code import kubernetes
from googlecloudsdk.command_lib.code import local
from googlecloudsdk.command_lib.code import local_files
from googlecloudsdk.command_lib.code import yaml_helper
from googlecloudsdk.core import config
from googlecloudsdk.core import yaml
from googlecloudsdk.core.updater import update_manager
from googlecloudsdk.core.util import files as file_utils
from googlecloudsdk.core.util import platforms
import six

DEFAULT_CLUSTER_NAME = 'gcloud-local-dev'


def _EmptyHandler(unused_signum, unused_stack):
  """Do nothing signal handler."""
  pass


class _SigInterruptedHandler(object):
  """Context manager to capture CTRL-C and send it to a handler."""

  def __init__(self, handler):
    self._orig_handler = None
    self._handler = handler

  def __enter__(self):
    self._orig_handler = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, self._handler)

  def __exit__(self, exc_type, exc_value, tb):
    signal.signal(signal.SIGINT, self._orig_handler)


def _FindOrInstallSkaffoldComponent():
  if (config.Paths().sdk_root and
      update_manager.UpdateManager.EnsureInstalledAndRestart(['skaffold'])):
    return os.path.join(config.Paths().sdk_root, 'bin', 'skaffold')
  return None


def _FindSkaffold():
  """Find the path to the skaffold executable."""
  skaffold = (
      _FindOrInstallSkaffoldComponent() or
      file_utils.FindExecutableOnPath('skaffold'))
  if not skaffold:
    raise EnvironmentError('Unable to locate skaffold.')
  return skaffold


class WindowsNamedTempFile(object):
  """Wrapper around named temporary file for Windows.

  NamedTemporaryFiles cannot be read by other processes on windows because
  only one process can open a file at a time. This file will be unlinked
  at the end of the context.
  """

  def __init__(self, *args, **kwargs):
    self._args = args
    self._kwargs = kwargs.copy()
    self._kwargs['delete'] = False
    self._f = None

  def __enter__(self):
    self._f = tempfile.NamedTemporaryFile(*self._args, **self._kwargs)
    return self._f

  def __exit__(self, exc_type, exc_value, tb):
    if self._f:
      try:
        os.unlink(self._f.name)
      except OSError:
        # File already unlinked. No need to clean up.
        pass


@contextlib.contextmanager
def _NamedTempFile(contents):
  """Write a named temporary with given contents.

  Args:
    contents: (str) File contents.

  Yields:
    The temporary file object.
  """
  if os.name == 'nt':
    with WindowsNamedTempFile(mode='w+t') as f:
      f.write(contents)
      f.close()
      yield f
  else:
    with tempfile.NamedTemporaryFile(mode='w+t') as f:
      f.write(contents)
      f.flush()
      yield f


@contextlib.contextmanager
def Skaffold(skaffold_config,
             context_name=None,
             namespace=None,
             env_vars=None,
             additional_flags=None):
  """Run skaffold and catch keyboard interrupts to kill the process.

  Args:
    skaffold_config: Path to skaffold configuration yaml file.
    context_name: Kubernetes context name.
    namespace: Kubernetes namespace name.
    env_vars: Additional environment variables with which to run skaffold.
    additional_flags: Extra skaffold flags.

  Yields:
    The skaffold process.
  """
  cmd = [_FindSkaffold(), 'dev', '-f', skaffold_config, '--port-forward']
  if context_name:
    cmd += ['--kube-context', context_name]
  if namespace:
    cmd += ['--namespace', namespace]
  if additional_flags:
    cmd += additional_flags

  # Supress the current Ctrl-C handler and pass the signal to the child
  # process.
  with _SigInterruptedHandler(_EmptyHandler):
    # Skaffold needs to be able to run minikube and kind. Those tools
    # may live in the SDK root as installed gcloud components. Place the
    # SDK root in the path for skaffold.
    env = os.environ.copy()
    if env_vars:
      env.update((six.ensure_str(name), six.ensure_str(value))
                 for name, value in env_vars.items())
    if config.Paths().sdk_root:
      env['PATH'] = six.ensure_str(env['PATH'] + os.pathsep +
                                   config.Paths().sdk_root)

    try:
      p = subprocess.Popen(cmd, env=env)
      yield p
    except KeyboardInterrupt:
      p.terminate()
      p.wait()

    sys.stdout.flush()
    sys.stderr.flush()


@contextlib.contextmanager
def _SetImagePush(skaffold_file, shared_docker):
  """Set build.local.push value in skaffold file.

  Args:
    skaffold_file: Skaffold file handle.
    shared_docker: Boolean that is true if docker instance is shared between the
      kubernetes cluster and local docker builder.

  Yields:
    Path of skaffold file with build.local.push value set to the proper value.
  """
  # TODO(b/149935260): This function can be removed when
  # https://github.com/GoogleContainerTools/skaffold/issues/3668 is resolved.
  if not shared_docker:
    # If docker is not shared, use the default value (false). There is no need
    # to rewrite the skaffold file.
    yield skaffold_file
  else:
    sakffold_yaml = yaml.load_path(skaffold_file.name)
    local_block = yaml_helper.GetOrCreate(sakffold_yaml, ('build', 'local'))
    local_block['push'] = False
    with _NamedTempFile(yaml.dump(sakffold_yaml)) as patched_skaffold_file:
      yield patched_skaffold_file


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Dev(base.Command):
  """Run a Cloud Run service in a local development environment.

  By default, this command runs the user's containers on minikube on the local
  machine. To run on another kubernetes cluster, use the --kube-context flag.

  When using minikube, if the minikube cluster is not running, this command
  will start a new minikube cluster with that name.
  """

  @classmethod
  def Args(cls, parser):
    group = parser.add_mutually_exclusive_group(required=False)

    group.add_argument('--kube-context', help='Kubernetes context.')

    group.add_argument('--minikube-profile', help='Minikube profile.')

    group.add_argument('--kind-cluster', help='Kind cluster.')

    parser.add_argument(
        '--stop-cluster',
        default=False,
        action='store_true',
        help='If running on minikube or kind, stop the minkube profile or '
        'kind cluster at the end of the session.')

    parser.add_argument(
        '--minikube-vm-driver',
        default='docker',
        help='If running on minikube, use this vm driver.')

    parser.add_argument(
        '--namespace',
        help='Kubernetes namespace for development kubernetes objects.')

    # For testing only
    parser.add_argument(
        '--additional-skaffold-flags',
        type=arg_parsers.ArgList(),
        metavar='FLAG',
        hidden=True,
        help='Additional flags with which to run skaffold.')

  def Run(self, args):
    settings = local.Settings.FromArgs(args)
    local_file_generator = local_files.LocalRuntimeFiles(settings)

    kubernetes_config = six.ensure_text(local_file_generator.KubernetesConfig())

    with _NamedTempFile(kubernetes_config) as kubernetes_file:
      skaffold_config = six.ensure_text(
          local_file_generator.SkaffoldConfig(kubernetes_file.name))
      with _NamedTempFile(skaffold_config) as skaffold_file, \
           self._GetKubernetesEngine(args) as kube_context, \
           self._WithKubeNamespace(args.namespace, kube_context.context_name), \
           _SetImagePush(skaffold_file, kube_context.shared_docker) as patched_skaffold_file, \
           Skaffold(patched_skaffold_file.name, kube_context.context_name,
                    args.namespace, kube_context.env_vars,
                    args.additional_skaffold_flags) as skaffold:
        skaffold.wait()

  @staticmethod
  def _GetKubernetesEngine(args):
    """Get the appropriate kubernetes implementation from the args.

    Args:
      args: The namespace containing the args.

    Returns:
      The context manager for the appropriate kubernetes implementation.
    """

    def External():
      return kubernetes.ExternalClusterContext(args.kube_context)

    def Kind():
      if args.IsSpecified('kind_cluster'):
        cluster_name = args.kind_cluster
      else:
        cluster_name = DEFAULT_CLUSTER_NAME
      return kubernetes.KindClusterContext(cluster_name, args.stop_cluster)

    def Minikube():
      if args.IsSpecified('minikube_profile'):
        cluster_name = args.minikube_profile
      else:
        cluster_name = DEFAULT_CLUSTER_NAME

      return kubernetes.Minikube(cluster_name, args.stop_cluster,
                                 args.minikube_vm_driver)

    if args.IsSpecified('kube_context'):
      return External()
    elif args.IsSpecified('kind_cluster'):
      return Kind()
    elif args.IsSpecified('minikube_profile'):
      return Minikube()
    elif platforms.OperatingSystem.Current() == platforms.OperatingSystem.LINUX:
      return Kind()
    else:
      return Minikube()

  @staticmethod
  @contextlib.contextmanager
  def _WithKubeNamespace(namespace_name, context_name):
    """Create and destory a kubernetes namespace if one is specified.

    Args:
      namespace_name: Namespace name.
      context_name: Kubernetes context name.

    Yields:
      None
    """
    if namespace_name:
      with kubernetes.KubeNamespace(namespace_name, context_name):
        yield
    else:
      yield
