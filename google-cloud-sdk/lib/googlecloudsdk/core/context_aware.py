# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Helper module for context aware access."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import atexit
import io
import json
import os

from googlecloudsdk.core import config
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files

DEFAULT_AUTO_DISCOVERY_FILE_PATH = os.path.join(
    files.GetHomeDir(), '.secureConnect', 'context_aware_metadata.json')


def _AutoDiscoveryFilePath():
  """Return the file path of the context aware configuration file."""
  # auto_discovery_file_path is an override used for testing purposes.
  cfg_file = properties.VALUES.context_aware.auto_discovery_file_path.Get()
  if cfg_file is not None:
    return cfg_file
  return DEFAULT_AUTO_DISCOVERY_FILE_PATH


def _SplitPemIntoSections(contents):
  """Returns dict with {name: section} by parsing contents in PEM format.

  A simple parser for PEM file. Please see RFC 7468 for the format of PEM
  file.
  Note: this parser requires the post-encapsulation label of a section to
  match its pre-encapsulation label, and ignores the section without a
  matching label.

  Args:
    contents: contents of a PEM file.

  Returns:
    A diction of sections in a PEM file.
  """
  def IsMarker(l):
    """Returns (begin:bool, end:bool, name:str)."""
    if l.startswith('-----BEGIN ') and l.endswith('-----'):
      return (True, False, l[11:-5])
    elif l.startswith('-----END ') and l.endswith('-----'):
      return (False, True, l[9:-5])
    else:
      return False, False, ''

  result = {}
  pem_lines = []
  pem_section_name = None

  for line in contents.splitlines():
    line = line.strip()
    if not line:
      continue

    (begin, end, name) = IsMarker(line)
    if begin:
      if pem_section_name:
        log.warning('section %s misses end line, thus is ignored' %
                    pem_section_name)
      if name in result.keys():
        log.warning('section %s already exists, and the older section will '
                    'be ignored' % name)
      pem_section_name = name
      pem_lines = []
    elif end:
      if not pem_section_name:
        log.warning('section %s misses a beginning line, thus is ignored' %
                    name)
      elif pem_section_name != name:
        log.warning('section %s misses a matching end line, found %s' %
                    (pem_section_name, name))
        pem_section_name = None

    if pem_section_name:
      pem_lines.append(line)
      if end:
        result[name] = '\n'.join(pem_lines) + '\n'
        pem_section_name = None

  if pem_section_name:
    log.warning('section %s misses an end line' % pem_section_name)

  return result


class ConfigException(exceptions.Error):
  pass


class CertProviderUnexpectedExit(exceptions.Error):
  pass


class CertProvisionException(exceptions.Error):
  """Represents errors when provisioning a client certificate."""
  pass


class _ConfigImpl(object):
  """Represents the configurations associated with context aware access.

  Only one instance of Config can be created for the program.
  """

  def __init__(self):
    self.use_client_certificate = (
        properties.VALUES.context_aware.use_client_certificate.GetBool())
    self._cert_and_key_path = None
    self.client_cert_path = None
    self.client_cert_password = None
    atexit.register(self.Cleanup)
    if self.use_client_certificate:
      # Search for configuration produced by endpoint verification
      cfg_file = _AutoDiscoveryFilePath()
      # Autodiscover context aware settings from configuration file created by
      # end point verification agent
      try:
        contents = files.ReadFileContents(cfg_file)
        log.debug('context aware settings detected at %s', cfg_file)
        json_out = json.loads(contents)
        if 'cert_provider_command' in json_out:
          # Execute the cert provider to provision client certificates for
          # context aware access
          cmd = json_out['cert_provider_command']
          # Remember the certificate path when auto provisioning
          # to cleanup after use
          self._cert_and_key_path = os.path.join(
              config.Paths().global_config_dir, 'caa_cert.pem')
          # Certs provisioned using endpoint verification are stored as a
          # single file holding both the public certificate
          # and the private key
          self._ProvisionClientCert(cmd, self._cert_and_key_path)
          self.client_cert_path = self._cert_and_key_path
        else:
          raise CertProvisionException('no cert provider detected')
      except files.Error as e:
        log.debug('context aware settings discovery file %s - %s', cfg_file, e)
      except CertProvisionException as e:
        log.error('failed to provision client certificate - %s', e)
      if self.client_cert_path is None:
        raise ConfigException(
            'Use of client certificate requires endpoint verification agent. '
            'Run `gcloud topic client-certificate` for installation guide.')

  def Cleanup(self):
    """Cleanup any files or resource provisioned during config init."""
    self._UnprovisionClientCert()

  def _ProvisionClientCert(self, cmd, cert_path):
    """Executes certificate provider to obtain client certificate and keys."""
    try:
      # monkey-patch command line args to get password protected cert
      pass_arg = '--with_passphrase'
      if '--print_certificate' in cmd and pass_arg not in cmd:
        cmd.append(pass_arg)

      cert_pem_io = io.StringIO()
      ret_val = execution_utils.Exec(
          cmd, no_exit=True, out_func=cert_pem_io.write,
          err_func=log.file_only_logger.debug)
      if ret_val:
        raise CertProviderUnexpectedExit(
            'certificate provider exited with error')

      sections = _SplitPemIntoSections(cert_pem_io.getvalue())
      with files.FileWriter(cert_path) as f:
        f.write(sections['CERTIFICATE'])
        f.write(sections['ENCRYPTED PRIVATE KEY'])
      self.client_cert_password = sections['PASSPHRASE'].splitlines()[1]
    except (files.Error,
            execution_utils.PermissionError,
            execution_utils.InvalidCommandError,
            CertProviderUnexpectedExit) as e:
      raise CertProvisionException(e)
    except KeyError as e:
      raise CertProvisionException(
          'Invalid output format from certificate provider, no %s' % e)

  def _UnprovisionClientCert(self):
    if self._cert_and_key_path is not None:
      try:
        os.remove(self._cert_and_key_path)
        log.debug('unprovisioned client cert - %s', self._cert_and_key_path)
      except (files.Error) as e:
        log.error('failed to remove client certificate - %s', e)


class _NoCertConfig(object):
  """Config with client certificate disabled."""

  def __init__(self):
    self.use_client_certificate = False
    self.client_cert_path = None
    self.client_cert_password = None


singleton_config = None


class Config(object):
  """Represents the configurations associated with context aware access."""

  def __init__(self):
    global singleton_config
    if not singleton_config:
      singleton_config = _ConfigImpl()
    self.use_client_certificate = singleton_config.use_client_certificate
    self.client_cert_path = singleton_config.client_cert_path
    self.client_cert_password = singleton_config.client_cert_password


def DisableCerts():
  """Disables cert provisioning and mtls support."""
  global singleton_config
  singleton_config = _NoCertConfig()
