# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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

"""A module to get a credentialed http object for making API calls."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import google_auth_httplib2

from googlecloudsdk.core import exceptions
from googlecloudsdk.core import http
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import creds as core_creds
from googlecloudsdk.core.credentials import store
from googlecloudsdk.core.util import files
from oauth2client import client
import six

ENCODING = None if six.PY2 else 'utf8'


class Error(exceptions.Error):
  """Exceptions for the http module."""


def Http(timeout='unset',
         enable_resource_quota=True,
         force_resource_quota=False,
         response_encoding=None,
         ca_certs=None,
         allow_account_impersonation=True,
         use_google_auth=False):
  """Get an httplib2.Http client for working with the Google API.

  Args:
    timeout: double, The timeout in seconds to pass to httplib2.  This is the
        socket level timeout.  If timeout is None, timeout is infinite.  If
        default argument 'unset' is given, a sensible default is selected.
    enable_resource_quota: bool, By default, we are going to tell APIs to use
        the quota of the project being operated on. For some APIs we want to use
        gcloud's quota, so you can explicitly disable that behavior by passing
        False here.
    force_resource_quota: bool, If true resource project quota will be used by
      this client regardless of the settings in gcloud. This should be used for
      newer APIs that cannot work with legacy project quota.
    response_encoding: str, the encoding to use to decode the response.
    ca_certs: str, absolute filename of a ca_certs file that overrides the
        default
    allow_account_impersonation: bool, True to allow use of impersonated service
      account credentials for calls made with this client. If False, the active
      user credentials will always be used.
    use_google_auth: bool, True if the calling command indicates to use
      google-auth library for authentication. If False, authentication will
      fallback to using the oauth2client library.

  Returns:
    1. A regular httplib2.Http object if no credentials are available;
    2. Or a httplib2.Http client object authorized by oauth2client
       credentials if use_google_auth==False;
    3. Or a google_auth_httplib2.AuthorizedHttp client object authorized by
       google-auth credentials.

  Raises:
    c_store.Error: If an error loading the credentials occurs.
  """
  http_client = http.Http(timeout=timeout, response_encoding=response_encoding,
                          ca_certs=ca_certs)

  # Wrappers for IAM header injection.
  authority_selector = properties.VALUES.auth.authority_selector.Get()
  authorization_token_file = (
      properties.VALUES.auth.authorization_token_file.Get())
  handlers = _GetIAMAuthHandlers(authority_selector, authorization_token_file)

  creds = store.LoadIfEnabled(allow_account_impersonation, use_google_auth)
  if creds:
    # Inject the resource project header for quota unless explicitly disabled.
    if enable_resource_quota or force_resource_quota:
      quota_project = core_creds.GetQuotaProject(creds, force_resource_quota)
      if quota_project:
        handlers.append(http.Modifiers.Handler(
            http.Modifiers.SetHeader('X-Goog-User-Project', quota_project)))

    if core_creds.IsGoogleAuthCredentials(creds):
      http_client = google_auth_httplib2.AuthorizedHttp(creds, http_client)
    else:
      http_client = creds.authorize(http_client)

    # Wrap the request method to put in our own error handling.
    http_client = http.Modifiers.WrapRequest(http_client, handlers,
                                             _HandleAuthError,
                                             client.AccessTokenRefreshError)

  return http_client


def _GetIAMAuthHandlers(authority_selector, authorization_token_file):
  """Get the request handlers for IAM authority selctors and auth tokens..

  Args:
    authority_selector: str, The authority selector string we want to use for
        the request or None.
    authorization_token_file: str, The file that contains the authorization
        token we want to use for the request or None.

  Returns:
    [http.Modifiers]: A list of request modifier functions to use to wrap an
    http request.
  """
  authorization_token = None
  if authorization_token_file:
    try:
      authorization_token = files.ReadFileContents(authorization_token_file)
    except files.Error as e:
      raise Error(e)

  handlers = []
  if authority_selector:
    handlers.append(http.Modifiers.Handler(
        http.Modifiers.SetHeader('x-goog-iam-authority-selector',
                                 authority_selector)))

  if authorization_token:
    handlers.append(http.Modifiers.Handler(
        http.Modifiers.SetHeader('x-goog-iam-authorization-token',
                                 authorization_token)))

  return handlers


def _HandleAuthError(e):
  """Handle a generic auth error and raise a nicer message.

  Args:
    e: The exception that was caught.

  Raises:
    sore.TokenRefreshError: If an auth error occurs.
  """
  msg = six.text_type(e)
  log.debug('Exception caught during HTTP request: %s', msg,
            exc_info=True)
  raise store.TokenRefreshError(msg)
