# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Provides functions to handle reauth for google auth."""

# TODO(b/151628904): Add reauth to google-auth.
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import http
from googlecloudsdk.core.util import retry

from oauth2client import client as oauth2client_client
from oauth2client.contrib import reauth
import six
from six.moves import http_client
from six.moves import urllib

from google.auth import exceptions as google_auth_exceptions
from google.oauth2 import _client as google_auth_client
from google.oauth2 import credentials


class Error(core_exceptions.Error):
  """Exceptions for reauth in google auth."""


class ReauthRequiredError(Error):
  """Exceptions when reauth is required."""


# In gcloud, UserCredWithReauth should be used for user account credentials.
# Do not use its parent class credentials.Credentials because it
# does not support reauth.
class UserCredWithReauth(credentials.Credentials):
  """Extended user credentials of the google auth library for reauth.

  reauth is not supported by the google auth library. However, gcloud supports
  reauth. This class is to override the refresh method to handle reauth.
  """

  def __init__(self,
               token,
               refresh_token=None,
               id_token=None,
               token_uri=None,
               client_id=None,
               client_secret=None,
               scopes=None,
               quota_project_id=None,
               rapt_token=None):
    super(UserCredWithReauth,
          self).__init__(token, refresh_token, id_token, token_uri,
                         client_id, client_secret, scopes, quota_project_id)
    self._rapt_token = rapt_token

  @property
  def rapt_token(self):
    """Reauth proof token."""
    return self._rapt_token

  def refresh(self, request):
    """Refreshes the access token and handles reauth request when it is asked.

    Args:
      request: google.auth.transport.Request, a callable used to make HTTP
        requests.
    """
    try:
      return self._Refresh(request)
    except ReauthRequiredError:
      # reauth.GetRaptToken is implemented in oauth2client and it is built on
      # httplib2. GetRaptToken does not work with
      # google.auth.transport.Request.
      response_encoding = None if six.PY2 else 'utf-8'
      http_request = http.Http(response_encoding=response_encoding).request
      self._rapt_token = reauth.GetRaptToken(http_request, self._client_id,
                                             self._client_secret,
                                             self._refresh_token,
                                             self._token_uri, list(self.scopes))
    return self._Refresh(request)

  def _Refresh(self, request):
    if (self._refresh_token is None or self._token_uri is None or
        self._client_id is None or self._client_secret is None):
      raise google_auth_exceptions.RefreshError(
          'The credentials do not contain the necessary fields need to '
          'refresh the access token. You must specify refresh_token, '
          'token_uri, client_id, and client_secret.')
    rapt_token = getattr(self, '_rapt_token', None)
    access_token, refresh_token, expiry, grant_response = _RefreshGrant(
        request, self._token_uri, self._refresh_token, self._client_id,
        self._client_secret, self._scopes, rapt_token)

    self.token = access_token
    self.expiry = expiry
    self._refresh_token = refresh_token
    self._id_token = grant_response.get('id_token')
    # id_token in oauth2client creds is decoded and it uses id_tokenb64 to
    # store the encoded copy. id_token in google-auth creds is encoded.
    # Here, we add id_tokenb64 to google-auth creds for consistency.
    self.id_tokenb64 = grant_response.get('id_token')

    if self._scopes and 'scope' in grant_response:
      requested_scopes = frozenset(self._scopes)
      granted_scopes = frozenset(grant_response['scope'].split())
      scopes_requested_but_not_granted = requested_scopes - granted_scopes
      if scopes_requested_but_not_granted:
        raise google_auth_exceptions.RefreshError(
            'Not all requested scopes were granted by the '
            'authorization server, missing scopes {}.'.format(
                ', '.join(scopes_requested_but_not_granted)))

  @classmethod
  def FromGoogleAuthUserCredentials(cls, creds):
    """Creates an object from creds of google.oauth2.credentials.Credentials.

    Args:
      creds: google.oauth2.credentials.Credentials, The input credentials.
    Returns:
      Credentials of UserCredWithReauth.
    """
    res = cls(
        creds.token,
        refresh_token=creds.refresh_token,
        id_token=creds.id_token,
        token_uri=creds.token_uri,
        client_id=creds.client_id,
        client_secret=creds.client_secret,
        scopes=creds.scopes,
        quota_project_id=creds.quota_project_id)
    res.expiry = creds.expiry
    return res


def _RefreshGrant(request,
                  token_uri,
                  refresh_token,
                  client_id,
                  client_secret,
                  scopes=None,
                  rapt_token=None):
  """Prepares the request to send to auth server to refresh tokens."""
  body = [
      ('grant_type', google_auth_client._REFRESH_GRANT_TYPE),  # pylint: disable=protected-access
      ('client_id', client_id),
      ('client_secret', client_secret),
      ('refresh_token', refresh_token),
  ]
  if scopes:
    body.append(('scope', ' '.join(scopes)))
  if rapt_token:
    body.append(('rapt', rapt_token))
  response_data = _TokenEndpointRequestWithRetry(request, token_uri, body)

  try:
    access_token = response_data['access_token']
  except KeyError as caught_exc:
    new_exc = google_auth_exceptions.RefreshError(
        'No access token in response.', response_data)
    six.raise_from(new_exc, caught_exc)

  refresh_token = response_data.get('refresh_token', refresh_token)
  expiry = google_auth_client._parse_expiry(response_data)  # pylint: disable=protected-access

  return access_token, refresh_token, expiry, response_data


def _ShouldRetryServerInternalError(exc_type, exc_value, exc_traceback, state):
  """Whether to retry the request when receive errors.

  Only retry when the error is not a reauth-related error. Retrying won't help
  if we are asked to reauth.

  Args:
    exc_type: type of the raised exception.
    exc_value: the instance of the raise the exception.
    exc_traceback: Traceback, traceback encapsulating  the call stack at the the
      point where the exception occurred.
    state: RetryerState, state of the retryer.

  Returns:
    True if the exception is google.auth.exceptions.RefreshError
  """
  del exc_value, exc_traceback, state
  return exc_type == google_auth_exceptions.RefreshError


@retry.RetryOnException(
    max_retrials=1, should_retry_if=_ShouldRetryServerInternalError)
def _TokenEndpointRequestWithRetry(request, token_uri, body):
  """Makes a request to the OAuth 2.0 authorization server's token endpoint.

  Args:
      request: google.auth.transport.Request, A callable used to make HTTP
        requests.
      token_uri: str, The OAuth 2.0 authorizations server's token endpoint URI.
      body: {str: str}, The parameters to send in the request body.

  Returns:
      The JSON-decoded response data.
  """
  body = urllib.parse.urlencode(body)
  headers = {
      'content-type': google_auth_client._URLENCODED_CONTENT_TYPE,  # pylint: disable=protected-access
  }

  response = request(method='POST', url=token_uri, headers=headers, body=body)

  response_body = six.ensure_text(response.data)

  if response.status != http_client.OK:
    _HandleErrorResponse(response_body)

  response_data = json.loads(response_body)

  return response_data


def _HandleErrorResponse(response_body):
  """"Translates an error response into an exception.

  Args:
      response_body: str, The decoded response data.

  Raises:
      google.auth.exceptions.RefreshError: If the token endpoint returned
          an server internal error.
      ReauthRequiredError: If reauth is required.
  """
  error_data = json.loads(response_body)

  error_code = error_data.get('error')
  error_subtype = error_data.get('error_subtype')
  if error_code == oauth2client_client.REAUTH_NEEDED_ERROR and (
      error_subtype == oauth2client_client.REAUTH_NEEDED_ERROR_INVALID_RAPT or
      error_subtype == oauth2client_client.REAUTH_NEEDED_ERROR_RAPT_REQUIRED):
    raise ReauthRequiredError('The reauth is required.')
  google_auth_client._handle_error_response(response_body)  # pylint: disable=protected-access
