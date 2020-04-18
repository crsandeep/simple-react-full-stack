# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""A library to support auth commands."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.credentials import flow as c_flow
from googlecloudsdk.core.credentials import store as c_store
from googlecloudsdk.core.util import files

from oauth2client import client


# Client ID from project "usable-auth-library", configured for
# general purpose API testing
# pylint: disable=g-line-too-long
DEFAULT_CREDENTIALS_DEFAULT_CLIENT_ID = '764086051850-6qr4p6gpi6hn506pt8ejuq83di341hur.apps.googleusercontent.com'
DEFAULT_CREDENTIALS_DEFAULT_CLIENT_SECRET = 'd-FL95Q19q7MQmFpd7hHD0Ty'
CLOUD_PLATFORM_SCOPE = 'https://www.googleapis.com/auth/cloud-platform'
GOOGLE_DRIVE_SCOPE = 'https://www.googleapis.com/auth/drive'
USER_EMAIL_SCOPE = 'https://www.googleapis.com/auth/userinfo.email'

DEFAULT_SCOPES = [
    USER_EMAIL_SCOPE,
    CLOUD_PLATFORM_SCOPE
]

CLIENT_SECRET_INSTALLED_TYPE = 'installed'


class Error(exceptions.Error):
  """A base exception for this class."""
  pass


class InvalidClientSecretsError(Error):
  """An error for when we fail to load the client secrets file."""
  pass


def DoInstalledAppBrowserFlowGoogleAuth(launch_browser,
                                        scopes,
                                        client_id_file=None):
  """Launches a 3LO oauth2 flow to get google-auth credentials.

  Args:
    launch_browser: bool, True to launch the browser, false to ask users to copy
      the auth url to a browser.
    scopes: [str], The list of scopes to authorize.
    client_id_file: str, The path to a file containing the client id and secret
      to use for the flow.  If None, the default client id for the Cloud SDK is
      used.
  Returns:
    google.auth.credentials.Credentials, The credentials obtained from the flow.
  """
  if client_id_file:
    AssertClientSecretIsInstalledType(client_id_file)
  google_auth_flow = c_flow.CreateGoogleAuthFlow(scopes, client_id_file)
  return c_flow.RunGoogleAuthFlow(google_auth_flow, launch_browser)


def DoInstalledAppBrowserFlow(launch_browser, scopes, client_id_file=None,
                              client_id=None, client_secret=None):
  """Launches a browser to get credentials.

  Args:
    launch_browser: bool, True to do a browser flow, false to allow the user to
      type in a token from a different browser.
    scopes: [str], The list of scopes to authorize.
    client_id_file: str, The path to a file containing the client id and secret
      to use for the flow.  If None, the default client id for the Cloud SDK is
      used.
    client_id: str, An alternate client id to use.  This is ignored if you give
      a client id file.  If None, the default client id for the Cloud SDK is
      used.
    client_secret: str, The secret to go along with client_id if specified.

  Returns:
    The clients obtained from the web flow.
  """
  try:
    if client_id_file:
      AssertClientSecretIsInstalledType(client_id_file)
      webflow = client.flow_from_clientsecrets(
          filename=client_id_file,
          scope=scopes)
      return c_store.RunWebFlow(webflow, launch_browser=launch_browser)
    else:
      return c_store.AcquireFromWebFlow(
          launch_browser=launch_browser,
          scopes=scopes,
          client_id=client_id,
          client_secret=client_secret)
  except c_store.FlowError:
    msg = 'There was a problem with web authentication.'
    if launch_browser:
      msg += ' Try running again with --no-launch-browser.'
    log.error(msg)
    raise


def GetClientSecretsType(client_id_file):
  """Get the type of the client secrets file (web or installed)."""
  invalid_file_format_msg = (
      'Invalid file format. See '
      'https://developers.google.com/api-client-library/'
      'python/guide/aaa_client_secrets')
  try:
    obj = json.loads(files.ReadFileContents(client_id_file))
  except files.Error:
    raise InvalidClientSecretsError(
        'Cannot read file: "%s"' % client_id_file)
  if obj is None:
    raise InvalidClientSecretsError(invalid_file_format_msg)
  if len(obj) != 1:
    raise InvalidClientSecretsError(
        invalid_file_format_msg + ' '
        'Expected a JSON object with a single property for a "web" or '
        '"installed" application')
  return tuple(obj)[0]


def AssertClientSecretIsInstalledType(client_id_file):
  client_type = GetClientSecretsType(client_id_file)
  if client_type != CLIENT_SECRET_INSTALLED_TYPE:
    raise InvalidClientSecretsError(
        'Only client IDs of type \'%s\' are allowed, but encountered '
        'type \'%s\'' % (CLIENT_SECRET_INSTALLED_TYPE, client_type))
