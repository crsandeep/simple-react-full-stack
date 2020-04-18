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

"""Library for defining Binary backed operations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
import collections
import os

from googlecloudsdk.core import config
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import execution_utils as exec_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import yaml
from googlecloudsdk.core.updater import local_state
from googlecloudsdk.core.updater import update_manager
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import platforms

import six


_DEFAULT_FAILURE_ERROR_MESSAGE = (
    'Error executing command [{command}] (with context [{context}]). '
    'Process exited with code {exit_code}')

_DEFAULT_MISSING_EXEC_MESSAGE = 'Executable [{}] not found.'


def _LogDefaultFailure(result_object):
  log.error(_DEFAULT_FAILURE_ERROR_MESSAGE.format(
      command=result_object.executed_command,
      context=result_object.context,
      exit_code=result_object.exit_code))


class BinaryOperationError(core_exceptions.Error):
  """Base class for binary operation errors."""


class InvalidOperationForBinary(BinaryOperationError):
  """Raised when an invalid Operation is invoked on a binary."""


class MissingExecutableException(BinaryOperationError):
  """Raised if an executable can not be found on the path."""

  def __init__(self, exec_name, custom_message=None):

    if custom_message:
      error_msg = custom_message
    else:
      error_msg = _DEFAULT_MISSING_EXEC_MESSAGE.format(exec_name)

    super(MissingExecutableException, self).__init__(error_msg)


class ExecutionError(BinaryOperationError):
  """Raised if there is an error executing the executable."""

  def __init__(self, command, error):
    super(ExecutionError, self).__init__(
        'Error executing command on [{}]: [{}]'.format(command, error))


class InvalidWorkingDirectoryError(BinaryOperationError):
  """Raised when an invalid path is passed for binary working directory."""

  def __init__(self, command, path):
    super(InvalidWorkingDirectoryError, self).__init__(
        'Error executing command on [{}]. Invalid Path [{}]'.format(
            command, path))


class ArgumentError(BinaryOperationError):
  """Raised if there is an error parsing argument to a command."""


def DefaultStdOutHandler(result_holder):
  """Default processing for stdout from subprocess."""
  def HandleStdOut(stdout):
    if stdout:
      stdout.rstrip()
    result_holder.stdout = stdout
  return HandleStdOut


def DefaultStdErrHandler(result_holder):
  """Default processing for stderr from subprocess."""
  def HandleStdErr(stderr):
    if stderr:
      stderr.rstrip()
    result_holder.stderr = stderr
  return HandleStdErr


def DefaultFailureHandler(result_holder, show_exec_error=False):
  """Default processing for subprocess failure status."""
  if result_holder.exit_code != 0:
    result_holder.failed = True
  if show_exec_error and result_holder.failed:
    _LogDefaultFailure(result_holder)


def DefaultStreamOutHandler(result_holder, do_capture=False):
  """Default processing for streaming stdout from subprocess."""
  def HandleStdOut(line):
    if line:
      line.rstrip()
      log.Print(line)
    if do_capture:
      if not result_holder.stdout:
        result_holder.stdout = []
      result_holder.stdout.append(line)
  return HandleStdOut


def DefaultStreamErrHandler(result_holder, do_capture=False):
  """Default processing for streaming stderr from subprocess."""
  def HandleStdErr(line):
    if line:
      log.status.Print(line)
    if do_capture:
      if not result_holder.stderr:
        result_holder.stderr = []
      result_holder.stderr.append(line)
  return HandleStdErr


# Some golang binary commands (e.g. kubectl diff) behave this way
# so this is for those known exceptional cases.
def NonZeroSuccessFailureHandler(result_holder, show_exec_error=False):
  """Processing for subprocess where non-zero exit status is not always failure.

  Uses rule of thumb that defines success as:
  - a process with zero exit status OR
  - a process with non-zero exit status AND some stdout output.

  All others are considered failed.

  Args:
    result_holder: OperationResult, result of command execution
    show_exec_error: bool, if true log the process command and exit status the
      terminal for failed executions.

  Returns:
    None. Sets the failed attribute of the result_holder.
  """
  if result_holder.exit_code != 0 and not result_holder.stdout:
    result_holder.failed = True
  if show_exec_error and result_holder.failed:
    _LogDefaultFailure(result_holder)


def CheckBinaryComponentInstalled(component_name):
  platform = platforms.Platform.Current() if config.Paths().sdk_root else None
  try:
    manager = update_manager.UpdateManager(platform_filter=platform, warn=False)
    return component_name in manager.GetCurrentVersionsInformation()
  except local_state.Error:
    log.warning('Component check failed. Could not verify SDK install path.')
    return None


def CheckForInstalledBinary(binary_name, custom_message=None):
  """Check if binary is installed and return path or raise error.

  Prefer the installed component over any version found on path.

  Args:
    binary_name: str, name of binary to search for.
    custom_message: str, custom message to used by
      MissingExecutableException if thrown.

  Returns:
    Path to executable if found on path or installed component.

  Raises:
    MissingExecutableException: if executable can not be found and is not
     installed as a component.
  """
  is_component = CheckBinaryComponentInstalled(binary_name)

  if is_component:
    return os.path.join(config.Paths().sdk_bin_path, binary_name)

  path_executable = files.FindExecutableOnPath(binary_name)
  if path_executable:
    return path_executable

  raise MissingExecutableException(binary_name, custom_message)


class BinaryBackedOperation(six.with_metaclass(abc.ABCMeta, object)):
  """Class for declarative operations implemented as external binaries."""

  class OperationResult(object):
    """Generic Holder for Operation return values and errors."""

    def __init__(self,
                 command_str,
                 output=None,
                 errors=None,
                 status=0,
                 failed=False,
                 execution_context=None):
      self.executed_command = command_str
      self.stdout = output
      self.stderr = errors
      self.exit_code = status
      self.context = execution_context
      self.failed = failed

    def __str__(self):
      output = collections.OrderedDict()
      output['executed_command'] = self.executed_command
      output['stdout'] = self.stdout
      output['stderr'] = self.stderr
      output['exit_code'] = self.exit_code
      output['failed'] = self.failed
      output['execution_context'] = self.context
      return yaml.dump(output)

    def __eq__(self, other):
      if isinstance(other, BinaryBackedOperation.OperationResult):
        return (self.executed_command == other.executed_command and
                self.stdout == other.stdout and
                self.stderr == other.stderr and
                self.exit_code == other.exit_code and
                self.failed == other.failed and
                self.context == other.context)
      return False

  def __init__(self, binary, binary_version=None, std_out_func=None,
               std_err_func=None, failure_func=None, default_args=None,
               custom_errors=None):
    """Creates the Binary Operation.

    Args:
      binary: executable, the name of binary containing the underlying
        operations that this class will invoke.
      binary_version: string, version of the wrapped binary.
      std_out_func: callable(str), function to call to process stdout from
        executable
      std_err_func: callable(str), function to call to process stderr from
        executable
      failure_func: callable(OperationResult), function to call to determine if
        the operation result is a failure. Useful for cases where underlying
        binary can exit with non-zero error code yet still succeed.
      default_args: dict{str:str}, mapping of parameter names to values
        containing default/static values that should always be passed to the
        command.
      custom_errors: dict(str:str}, map of custom exception messages to be used
        for known errors.
    """
    self._executable = CheckForInstalledBinary(
        binary, custom_errors['MISSING_EXEC'] if custom_errors else None)
    self._binary = binary
    self._version = binary_version
    self._default_args = default_args
    self.std_out_handler = std_out_func
    self.std_err_handler = std_err_func
    self.set_failure_status = failure_func

  @property
  def binary_name(self):
    return self._binary

  @property
  def executable(self):
    return self._executable

  @property
  def defaults(self):
    return self._default_args

  def _Execute(self, cmd, stdin=None, env=None, **kwargs):
    """Execute binary and return operation result.

     Will parse args from kwargs into a list of args to pass to underlying
     binary and then attempt to execute it. Will use configured stdout, stderr
     and failure handlers for this operation if configured or module defaults.

    Args:
      cmd: [str], command to be executed with args
      stdin: str, data to send to binary on stdin
      env: {str, str}, environment vars to send to binary.
      **kwargs: mapping of additional arguments to pass to the underlying
        executor.

    Returns:
      OperationResult: execution result for this invocation of the binary.

    Raises:
      ArgumentError, if there is an error parsing the supplied arguments.
      BinaryOperationError, if there is an error executing the binary.
    """
    op_context = {'env': env, 'stdin': stdin,
                  'exec_dir': kwargs.get('execution_dir')}
    result_holder = self.OperationResult(command_str=cmd,
                                         execution_context=op_context)

    std_out_handler = (self.std_out_handler or
                       DefaultStdOutHandler(result_holder))
    std_err_handler = (self.std_out_handler or
                       DefaultStdErrHandler(result_holder))
    failure_handler = (self.set_failure_status or DefaultFailureHandler)
    short_cmd_name = os.path.basename(cmd[0])  # useful for error messages

    try:
      working_dir = kwargs.get('execution_dir')
      if working_dir and not os.path.isdir(working_dir):
        raise InvalidWorkingDirectoryError(short_cmd_name, working_dir)

      exit_code = exec_utils.Exec(args=cmd,
                                  no_exit=True,
                                  out_func=std_out_handler,
                                  err_func=std_err_handler,
                                  in_str=stdin,
                                  cwd=working_dir,
                                  env=env)
    except (exec_utils.PermissionError, exec_utils.InvalidCommandError) as e:
      raise ExecutionError(short_cmd_name, e)
    result_holder.exit_code = exit_code
    failure_handler(result_holder, kwargs.get('show_exec_error', False))
    return result_holder

  @abc.abstractmethod
  def _ParseArgsForCommand(self, **kwargs):
    """Parse and validate kwargs into command argument list.

    Will process any default_args first before processing kwargs, overriding as
    needed. Will also perform any validation on passed arguments. If calling a
    named sub-command on the underlying binary (vs. just executing the root
    binary), the sub-command should be the 1st argument returned in the list.

    Args:
      **kwargs: keyword arguments for the underlying command.

    Returns:
     list of arguments to pass to execution of underlying command.

    Raises:
      ArgumentError: if there is an error parsing or validating arguments.
    """
    pass

  def __call__(self, **kwargs):
    cmd = [self.executable]
    cmd.extend(self._ParseArgsForCommand(**kwargs))
    return self._Execute(cmd, **kwargs)


class StreamingBinaryBackedOperation(six.with_metaclass(abc.ABCMeta,
                                                        BinaryBackedOperation)):
  """Extend Binary Operations for binaries which require streaming output."""

  def __init__(self, binary, binary_version=None, std_out_func=None,
               std_err_func=None, failure_func=None, default_args=None,
               custom_errors=None, capture_output=False):
    super(StreamingBinaryBackedOperation, self).__init__(binary,
                                                         binary_version,
                                                         std_out_func,
                                                         std_err_func,
                                                         failure_func,
                                                         default_args,
                                                         custom_errors)
    self.capture_output = capture_output

  def _Execute(self, cmd, stdin=None, env=None, **kwargs):
    """Execute binary and return operation result.

     Will parse args from kwargs into a list of args to pass to underlying
     binary and then attempt to execute it. Will use configured stdout, stderr
     and failure handlers for this operation if configured or module defaults.

    Args:
      cmd: [str], command to be executed with args
      stdin: str, data to send to binary on stdin
      env: {str, str}, environment vars to send to binary.
      **kwargs: mapping of additional arguments to pass to the underlying
        executor.

    Returns:
      OperationResult: execution result for this invocation of the binary.

    Raises:
      ArgumentError, if there is an error parsing the supplied arguments.
      BinaryOperationError, if there is an error executing the binary.
    """
    op_context = {'env': env, 'stdin': stdin,
                  'exec_dir': kwargs.get('execution_dir')}
    result_holder = self.OperationResult(command_str=cmd,
                                         execution_context=op_context)

    std_out_handler = (self.std_out_handler or
                       DefaultStreamOutHandler(result_holder,
                                               self.capture_output))
    std_err_handler = (self.std_out_handler or
                       DefaultStreamErrHandler(result_holder,
                                               self.capture_output))
    failure_handler = (self.set_failure_status or DefaultFailureHandler)
    short_cmd_name = os.path.basename(cmd[0])  # useful for error messages

    try:
      working_dir = kwargs.get('execution_dir')
      if working_dir and not os.path.isdir(working_dir):
        raise InvalidWorkingDirectoryError(short_cmd_name, working_dir)
      exit_code = exec_utils.ExecWithStreamingOutput(args=cmd,
                                                     no_exit=True,
                                                     out_func=std_out_handler,
                                                     err_func=std_err_handler,
                                                     in_str=stdin,
                                                     cwd=working_dir,
                                                     env=env)
    except (exec_utils.PermissionError, exec_utils.InvalidCommandError) as e:
      raise ExecutionError(short_cmd_name, e)
    result_holder.exit_code = exit_code
    failure_handler(result_holder, kwargs.get('show_exec_error', False))
    return result_holder
