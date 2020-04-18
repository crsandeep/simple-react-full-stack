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

"""One-line documentation for auth module.

A detailed description of auth.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


import datetime
import json
import os
import textwrap
import time

import dateutil
from googlecloudsdk.core import config
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import http
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.configurations import named_configs
from googlecloudsdk.core.credentials import creds
from googlecloudsdk.core.credentials import devshell as c_devshell
from googlecloudsdk.core.credentials import gce as c_gce
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import times


import httplib2
from oauth2client import client
from oauth2client import crypt
from oauth2client import service_account
from oauth2client.contrib import gce as oauth2client_gce
from oauth2client.contrib import reauth_errors
import six
from six.moves import urllib
from google.auth import exceptions as google_auth_exceptions
from google.auth.transport import requests
from google.oauth2 import service_account as google_auth_service_account


GOOGLE_OAUTH2_PROVIDER_AUTHORIZATION_URI = (
    'https://accounts.google.com/o/oauth2/auth')
GOOGLE_OAUTH2_PROVIDER_REVOKE_URI = (
    'https://accounts.google.com/o/oauth2/revoke')
GOOGLE_OAUTH2_PROVIDER_TOKEN_URI = (
    'https://accounts.google.com/o/oauth2/token')
_GRANT_TYPE = 'urn:ietf:params:oauth:grant-type:jwt-bearer'

_CREDENTIALS_EXPIRY_WINDOW = '300s'


class Error(exceptions.Error):
  """Exceptions for the credentials module."""


class AuthenticationException(Error):
  """Exceptions that tell the users to run auth login."""

  def __init__(self, message):
    super(AuthenticationException, self).__init__(textwrap.dedent("""\
        {message}
        Please run:

          $ gcloud auth login

        to obtain new credentials, or if you have already logged in with a
        different account:

          $ gcloud config set account ACCOUNT

        to select an already authenticated account to use.""".format(
            message=message)))


class PrintTokenAuthenticationException(Error):
  """Exceptions that tell the users to run auth login."""

  def __init__(self, message):
    super(PrintTokenAuthenticationException, self).__init__(textwrap.dedent("""\
        {message}
        Please run:

          $ gcloud auth login

        to obtain new credentials.

        For service account, please activate it first:

          $ gcloud auth activate-service-account ACCOUNT""".format(
              message=message)))


class NoCredentialsForAccountException(PrintTokenAuthenticationException):
  """Exception for when no credentials are found for an account."""

  def __init__(self, account):
    super(NoCredentialsForAccountException, self).__init__(
        'Your current active account [{account}] does not have any'
        ' valid credentials'.format(account=account))


class NoActiveAccountException(AuthenticationException):
  """Exception for when there are no valid active credentials."""

  def __init__(self, active_config_path=None):
    if active_config_path:
      if not os.path.exists(active_config_path):
        log.warning('Could not open the configuration file: [%s].',
                    active_config_path)
    super(NoActiveAccountException, self).__init__(
        'You do not currently have an active account selected.')


class TokenRefreshError(AuthenticationException,
                        client.AccessTokenRefreshError):
  """An exception raised when the auth tokens fail to refresh."""

  def __init__(self, error):
    message = ('There was a problem refreshing your current auth tokens: {0}'
               .format(error))
    super(TokenRefreshError, self).__init__(message)


class ReauthenticationException(Error):
  """Exceptions that tells the user to retry his command or run auth login."""

  def __init__(self, message):
    super(ReauthenticationException, self).__init__(textwrap.dedent("""\
        {message}
        Please retry your command or run:

          $ gcloud auth login

        to obtain new credentials.""".format(message=message)))


class TokenRefreshReauthError(ReauthenticationException):
  """An exception raised when the auth tokens fail to refresh due to reauth."""

  def __init__(self, error):
    message = ('There was a problem reauthenticating while refreshing your '
               'current auth tokens: {0}').format(error)
    super(TokenRefreshReauthError, self).__init__(message)


class WebLoginRequiredReauthError(Error):
  """An exception raised when login through browser is required for reauth.

  This applies to SAML users who set password as their reauth method today.
  Since SAML uers do not have knowledge of their Google password, we require
  web login and allow users to be authenticated by their IDP.
  """

  def __init__(self):
    super(WebLoginRequiredReauthError, self).__init__(textwrap.dedent("""\
        Please run:

          $ gcloud auth login

        to complete reauthentication."""))


class InvalidCredentialFileException(Error):
  """Exception for when an external credential file could not be loaded."""

  def __init__(self, f, e):
    super(InvalidCredentialFileException, self).__init__(
        'Failed to load credential file: [{f}].  {message}'
        .format(f=f, message=six.text_type(e)))


class AccountImpersonationError(Error):
  """Exception for when attempting to impersonate a service account fails."""
  pass


class FlowError(Error):
  """Exception for when something goes wrong with a web flow."""


class RevokeError(Error):
  """Exception for when there was a problem revoking."""


class InvalidCodeVerifierError(Error):
  """Exception for invalid code verifier for pkce."""


IMPERSONATION_TOKEN_PROVIDER = None


class StaticCredentialProviders(object):
  """Manages a list of credential providers."""

  def __init__(self):
    self._providers = []

  def AddProvider(self, provider):
    self._providers.append(provider)

  def RemoveProvider(self, provider):
    self._providers.remove(provider)

  def GetCredentials(self, account):
    for provider in self._providers:
      cred = provider.GetCredentials(account)
      if cred is not None:
        return cred
    return None

  def GetAccounts(self):
    accounts = set()
    for provider in self._providers:
      accounts |= provider.GetAccounts()
    return accounts


STATIC_CREDENTIAL_PROVIDERS = StaticCredentialProviders()


class DevShellCredentialProvider(object):
  """Provides account, project and credential data for devshell env."""

  def GetCredentials(self, account):
    devshell_creds = c_devshell.LoadDevshellCredentials()
    if devshell_creds and (devshell_creds.devshell_response.user_email ==
                           account):
      return devshell_creds
    return None

  def GetAccount(self):
    return c_devshell.DefaultAccount()

  def GetAccounts(self):
    devshell_creds = c_devshell.LoadDevshellCredentials()
    if devshell_creds:
      return set([devshell_creds.devshell_response.user_email])
    return set()

  def GetProject(self):
    return c_devshell.Project()

  def Register(self):
    properties.VALUES.core.account.AddCallback(self.GetAccount)
    properties.VALUES.core.project.AddCallback(self.GetProject)
    STATIC_CREDENTIAL_PROVIDERS.AddProvider(self)

  def UnRegister(self):
    properties.VALUES.core.account.RemoveCallback(self.GetAccount)
    properties.VALUES.core.project.RemoveCallback(self.GetProject)
    STATIC_CREDENTIAL_PROVIDERS.RemoveProvider(self)


class GceCredentialProvider(object):
  """Provides account, project and credential data for gce vm env."""

  def GetCredentials(self, account):
    if account in c_gce.Metadata().Accounts():
      return AcquireFromGCE(account)
    return None

  def GetAccount(self):
    if properties.VALUES.core.check_gce_metadata.GetBool():
      return c_gce.Metadata().DefaultAccount()
    return None

  def GetAccounts(self):
    return set(c_gce.Metadata().Accounts())

  def GetProject(self):
    if properties.VALUES.core.check_gce_metadata.GetBool():
      return c_gce.Metadata().Project()
    return None

  def Register(self):
    properties.VALUES.core.account.AddCallback(self.GetAccount)
    properties.VALUES.core.project.AddCallback(self.GetProject)
    STATIC_CREDENTIAL_PROVIDERS.AddProvider(self)

  def UnRegister(self):
    properties.VALUES.core.account.RemoveCallback(self.GetAccount)
    properties.VALUES.core.project.RemoveCallback(self.GetProject)
    STATIC_CREDENTIAL_PROVIDERS.RemoveProvider(self)


def AvailableAccounts():
  """Get all accounts that have credentials stored for the CloudSDK.

  This function will also ping the GCE metadata server to see if GCE credentials
  are available.

  Returns:
    [str], List of the accounts.

  """
  store = creds.GetCredentialStore()
  accounts = store.GetAccounts() | STATIC_CREDENTIAL_PROVIDERS.GetAccounts()

  return sorted(accounts)


def _TokenExpiresWithinWindow(expiry_window,
                              token_expiry_time,
                              max_window_seconds=3600):
  """Determines if token_expiry_time is within expiry_window_duration.

  Calculates the amount of time between utcnow() and token_expiry_time and
  returns true, if that amount is less than the provided duration window. All
  calculations are done in number of seconds for consistency.


  Args:
    expiry_window: string, Duration representing the amount of time between
      now and token_expiry_time to compare against.
    token_expiry_time: datetime, The time when token expires.
    max_window_seconds: int, Maximum size of expiry window, in seconds.

  Raises:
    ValueError: If expiry_window is invalid or can not be parsed.

  Returns:
    True if token is expired or will expire with in the provided window,
    False otherwise.
  """
  try:
    min_expiry = times.ParseDuration(expiry_window, default_suffix='s')
    if min_expiry.total_seconds > max_window_seconds:
      raise ValueError('Invalid expiry window duration [{}]: '
                       'Must be between 0s and 1h'.format(expiry_window))
  except times.Error as e:
    message = six.text_type(e).rstrip('.')
    raise ValueError('Error Parsing expiry window duration '
                     '[{}]: {}'.format(expiry_window, message))

  token_expiry_time = times.LocalizeDateTime(token_expiry_time,
                                             tzinfo=dateutil.tz.tzutc())
  window_end = times.GetDateTimePlusDuration(
      times.Now(tzinfo=dateutil.tz.tzutc()), min_expiry)

  return token_expiry_time <= window_end


def LoadFreshCredential(account=None,
                        scopes=None,
                        min_expiry_duration='1h',
                        allow_account_impersonation=True):
  """Get Load credentials and force a refresh.

    Will always refresh loaded credential if it is expired or would expire
    within min_expiry_duration.

  Args:
    account: str, The account address for the credentials being fetched. If
        None, the account stored in the core.account property is used.
    scopes: tuple, Custom auth scopes to request. By default CLOUDSDK_SCOPES
        are requested.
    min_expiry_duration: Duration str, Refresh the credentials if they are
        within this duration from expiration. Must be a valid duration between
        0 seconds and 1 hour (e.g. '0s' >x< '1h').
    allow_account_impersonation: bool, True to allow use of impersonated service
      account credentials (if that is configured). If False, the active user
      credentials will always be loaded.

  Returns:
    oauth2client.client.Credentials, The specified credentials.

  Raises:
    NoActiveAccountException: If account is not provided and there is no
        active account.
    NoCredentialsForAccountException: If there are no valid credentials
        available for the provided or active account.
    c_gce.CannotConnectToMetadataServerException: If the metadata server cannot
        be reached.
    TokenRefreshError: If the credentials fail to refresh.
    TokenRefreshReauthError: If the credentials fail to refresh due to reauth.
    AccountImpersonationError: If impersonation is requested but an
      impersonation provider is not configured.
   ValueError:
  """
  cred = Load(account=account,
              scopes=scopes,
              allow_account_impersonation=allow_account_impersonation)
  if not cred.token_expiry or _TokenExpiresWithinWindow(
      expiry_window=min_expiry_duration,
      token_expiry_time=cred.token_expiry):
    Refresh(cred)

  return cred


def LoadIfEnabled(allow_account_impersonation=True, use_google_auth=False):
  """Get the credentials associated with the current account.

  If credentials have been disabled via properties, this will return None.
  Otherwise it will load credentials like normal. If credential loading fails
  for any reason (including the user not being logged in), the usual exception
  is raised.

  Args:
    allow_account_impersonation: bool, True to allow use of impersonated service
      account credentials (if that is configured). If False, the active user
      credentials will always be loaded.
    use_google_auth: bool, True to load credentials of google-auth if it is
      supported in the current authentication scenario. False to load
      credentials of oauth2client.

  Returns:
    The credentials or None. The returned credentails will be type of
    oauth2client.client.Credentials or google.auth.credentials.Credentials based
    on use_google_auth and whether google-auth is supported in the current
    authentication scenario. The only two scenarios that google-auth is not
    supported are,
    1) Property auth/disable_google_auth is set to True;
    2) P12 service account key is being used.

    The only time None is returned is when credentials are disabled via
    properties. If no credentials are present but credentials are enabled via
    properties, it will be an error.

  Raises:
    NoActiveAccountException: If account is not provided and there is no
        active account.
    c_gce.CannotConnectToMetadataServerException: If the metadata server cannot
        be reached.
    TokenRefreshError: If the credentials fail to refresh.
    TokenRefreshReauthError: If the credentials fail to refresh due to reauth.
  """
  if properties.VALUES.auth.disable_credentials.GetBool():
    return None
  return Load(
      allow_account_impersonation=allow_account_impersonation,
      use_google_auth=use_google_auth)


def Load(account=None,
         scopes=None,
         prevent_refresh=False,
         allow_account_impersonation=True,
         use_google_auth=False):
  """Get the credentials associated with the provided account.

  This loads credentials regardless of whether credentials have been disabled
  via properties. Only use this when the functionality of the caller absolutely
  requires credentials (like printing out a token) vs logically requiring
  credentials (like for an http request).

  Credential information may come from the stored credential file (representing
  the last gcloud auth command), or the credential cache (representing the last
  time the credentials were refreshed). If they come from the cache, the
  token_response field will be None, as the full server response from the cached
  request was not stored.

  Args:
    account: str, The account address for the credentials being fetched. If
        None, the account stored in the core.account property is used.
    scopes: tuple, Custom auth scopes to request. By default CLOUDSDK_SCOPES
        are requested.
    prevent_refresh: bool, If True, do not refresh the access token even if it
        is out of date. (For use with operations that do not require a current
        access token, such as credential revocation.)
    allow_account_impersonation: bool, True to allow use of impersonated service
      account credentials (if that is configured). If False, the active user
      credentials will always be loaded.
    use_google_auth: bool, True to load credentials of google-auth if it is
      supported in the current authentication scenario. False to load
      credentials of oauth2client.

  Returns:
    oauth2client.client.Credentials or google.auth.credentials.Credentials based
    on use_google_auth and whether google-auth is supported in the current
    authentication sceanrio. The only two scenarios that google-auth is not
    supported are,
    1) Property auth/disable_google_auth is set to True;
    2) P12 service account key is being used.

  Raises:
    NoActiveAccountException: If account is not provided and there is no
        active account.
    NoCredentialsForAccountException: If there are no valid credentials
        available for the provided or active account.
    c_gce.CannotConnectToMetadataServerException: If the metadata server cannot
        be reached.
    TokenRefreshError: If the credentials fail to refresh.
    TokenRefreshReauthError: If the credentials fail to refresh due to reauth.
    AccountImpersonationError: If impersonation is requested but an
      impersonation provider is not configured.
  """
  google_auth_disabled = properties.VALUES.auth.disable_google_auth.GetBool()
  use_google_auth = use_google_auth and (not google_auth_disabled)

  impersonate_service_account = (
      properties.VALUES.auth.impersonate_service_account.Get())
  if allow_account_impersonation and impersonate_service_account:
    if not IMPERSONATION_TOKEN_PROVIDER:
      raise AccountImpersonationError(
          'gcloud is configured to impersonate service account [{}] but '
          'impersonation support is not available.'.format(
              impersonate_service_account))
    log.warning(
        'This command is using service account impersonation. All API calls will '
        'be executed as [{}].'.format(impersonate_service_account))
    cred = IMPERSONATION_TOKEN_PROVIDER.GetElevationAccessToken(
        impersonate_service_account, scopes or config.CLOUDSDK_SCOPES)
  else:
    cred = _Load(account, scopes, prevent_refresh, use_google_auth)

  cred = creds.MaybeConvertToGoogleAuthCredentials(cred, use_google_auth)
  return cred


def _Load(account, scopes, prevent_refresh, use_google_auth=False):
  """Helper for Load()."""
  # If a credential file is set, just use that and ignore the active account
  # and whatever is in the credential store.
  cred_file_override = properties.VALUES.auth.credential_file_override.Get()
  if cred_file_override:
    log.info('Using alternate credentials from file: [%s]',
             cred_file_override)
    try:
      cred = client.GoogleCredentials.from_stream(cred_file_override)
    except client.Error as e:
      raise InvalidCredentialFileException(cred_file_override, e)

    if cred.create_scoped_required():
      if scopes is None:
        scopes = config.CLOUDSDK_SCOPES
      cred = cred.create_scoped(scopes)

    # Set token_uri after scopes since token_uri needs to be explicitly
    # preserved when scopes are applied.
    token_uri_override = properties.VALUES.auth.token_host.Get()
    if token_uri_override:
      cred_type = creds.CredentialType.FromCredentials(cred)
      if cred_type in (creds.CredentialType.SERVICE_ACCOUNT,
                       creds.CredentialType.P12_SERVICE_ACCOUNT):
        cred.token_uri = token_uri_override
    # The credential override is not stored in credential store, but we still
    # want to cache access tokens between invocations.
    cred = creds.MaybeAttachAccessTokenCacheStore(cred)
  else:
    if not account:
      account = properties.VALUES.core.account.Get()

    if not account:
      raise NoActiveAccountException(
          named_configs.ActiveConfig(False).file_path)

    cred = STATIC_CREDENTIAL_PROVIDERS.GetCredentials(account)
    if cred is not None:
      return cred

    store = creds.GetCredentialStore()
    cred = store.Load(account, use_google_auth)
    if not cred:
      raise NoCredentialsForAccountException(account)

  if not prevent_refresh:
    _RefreshIfAlmostExpire(cred)

  return cred


def Refresh(credentials,
            http_client=None,
            is_impersonated_credential=False,
            include_email=False,
            gce_token_format='standard',
            gce_include_license=False):
  """Refresh credentials.

  Calls credentials.refresh(), unless they're SignedJwtAssertionCredentials.
  If the credentials correspond to a service account or impersonated credentials
  issue an additional request to generate a fresh id_token.

  Args:
    credentials: oauth2client.client.Credentials or
      google.auth.credentials.Credentials, The credentials to refresh.
    http_client: httplib2.Http or google.auth.transport.requests, The http
      transport to refresh with.
    is_impersonated_credential: bool, True treat provided credential as an
      impersonated service account credential. If False, treat as service
      account or user credential. Needed to avoid circular dependency on
      IMPERSONATION_TOKEN_PROVIDER.
    include_email: bool, Specifies whether or not the service account email is
      included in the identity token. Only applicable to impersonated service
      account.
    gce_token_format: str, Specifies whether or not the project and instance
      details are included in the identity token. Choices are "standard",
      "full".
    gce_include_license: bool, Specifies whether or not license codes for images
      associated with GCE instance are included in their identity tokens.

  Raises:
    TokenRefreshError: If the credentials fail to refresh.
    TokenRefreshReauthError: If the credentials fail to refresh due to reauth.
  """
  if creds.IsOauth2ClientCredentials(credentials):
    _Refresh(credentials, http_client, is_impersonated_credential,
             include_email, gce_token_format, gce_include_license)
  else:
    _RefreshGoogleAuth(credentials, http_client)


def _Refresh(credentials,
             http_client=None,
             is_impersonated_credential=False,
             include_email=False,
             gce_token_format='standard',
             gce_include_license=False):
  """Refreshes oauth2client credentials."""
  response_encoding = None if six.PY2 else 'utf-8'
  request_client = http_client or http.Http(response_encoding=response_encoding)
  try:
    credentials.refresh(request_client)

    id_token = None
    # Service accounts require an additional request to receive a fresh id_token
    if is_impersonated_credential:
      if not IMPERSONATION_TOKEN_PROVIDER:
        raise AccountImpersonationError(
            'gcloud is configured to impersonate a service account but '
            'impersonation support is not available.')
      if not IMPERSONATION_TOKEN_PROVIDER.IsImpersonationCredential(
          credentials):
        raise AccountImpersonationError(
            'Invalid impersonation account for refresh {}'.format(credentials))
      id_token = _RefreshImpersonatedAccountIdToken(
          credentials, include_email=include_email)
    # Service accounts require an additional request to receive a fresh id_token
    elif isinstance(credentials, service_account.ServiceAccountCredentials):
      id_token = _RefreshServiceAccountIdToken(credentials, request_client)
    elif isinstance(credentials, oauth2client_gce.AppAssertionCredentials):
      id_token = c_gce.Metadata().GetIdToken(
          config.CLOUDSDK_CLIENT_ID,
          token_format=gce_token_format,
          include_license=gce_include_license)

    if id_token:
      if credentials.token_response:
        credentials.token_response['id_token'] = id_token
      credentials.id_tokenb64 = id_token

  except (client.AccessTokenRefreshError, httplib2.ServerNotFoundError) as e:
    raise TokenRefreshError(six.text_type(e))
  except reauth_errors.ReauthSamlLoginRequiredError:
    raise WebLoginRequiredReauthError()
  except reauth_errors.ReauthError as e:
    raise TokenRefreshReauthError(str(e))


def _RefreshGoogleAuth(credentials, http_client=None):
  """Refreshes google-auth credentials.

  Args:
    credentials: google.auth.credentials.Credentials, A google-auth credentials
      to refresh.
    http_client: google.auth.transport.requests, The http transport to refresh
      with.
  """
  request_client = http_client or requests
  try:
    credentials.refresh(request_client.Request())

    id_token = None
    if isinstance(credentials, google_auth_service_account.Credentials):
      id_token = _RefreshServiceAccountIdTokenGoogleAuth(
          credentials, request_client)
    else:
      # TODO(b/151370064): ID token refresh should support GCE and impersonated
      # credentials.
      pass

    if id_token:
      # '_id_token' is the field supported in google-auth natively. gcloud
      # keeps an additional field 'id_tokenb64' to store this information
      # which is referenced in several places
      credentials._id_token = id_token  # pylint: disable=protected-access
      credentials.id_tokenb64 = id_token
  except google_auth_exceptions.RefreshError as e:
    raise TokenRefreshError(six.text_type(e))
  # TODO(b/147893169): Throws TokenRefreshReauthError on reauth errors once
  #   supporting reauth is ready for google-auth user credentials.


def _RefreshIfAlmostExpire(credentials):
  """Refreshes credentials if they are expired or will expire soon.

  For oauth2client credentials, refreshes if they expire within the expiry
  window. oauth2client credentials may be converted to google-auth credentials
  later in the call stack. The latter do not currently support reauth. So it is
  essential to ensure oauth2client credentials will remain valid during
  a command.

  For google-auth credentials, refreshes if they are expired.

  Args:
    credentials: google.auth.credentials.Credentials or
      client.OAuth2Credentials, the credentials to refresh.
  """
  if creds.IsOauth2ClientCredentials(credentials):
    almost_expire = not credentials.token_expiry or _TokenExpiresWithinWindow(
        _CREDENTIALS_EXPIRY_WINDOW, credentials.token_expiry)
  else:
    almost_expire = not credentials.valid

  if almost_expire:
    Refresh(credentials)


def _RefreshImpersonatedAccountIdToken(cred, include_email):
  """Get a fresh id_token for the given impersonated service account."""
  # pylint: disable=protected-access
  service_account_email = cred._service_account_id
  return IMPERSONATION_TOKEN_PROVIDER.GetElevationIdToken(
      service_account_email, config.CLOUDSDK_CLIENT_ID, include_email)
  # pylint: enable=protected-access


def _RefreshServiceAccountIdToken(cred, http_client):
  """Get a fresh id_token for the given oauth2client credentials.

  Args:
    cred: service_account.ServiceAccountCredentials, the credentials for which
      to refresh the id_token.
    http_client: httplib2.Http, the http transport to refresh with.

  Returns:
    str, The id_token if refresh was successful. Otherwise None.
  """
  http_request = http_client.request

  now = int(time.time())
  # pylint: disable=protected-access
  payload = {
      'aud': cred.token_uri,
      'iat': now,
      'exp': now + cred.MAX_TOKEN_LIFETIME_SECS,
      'iss': cred._service_account_email,
      'target_audience': config.CLOUDSDK_CLIENT_ID,
  }
  assertion = crypt.make_signed_jwt(
      cred._signer, payload, key_id=cred._private_key_id)

  body = urllib.parse.urlencode({
      'assertion': assertion,
      'grant_type': _GRANT_TYPE,
  })

  resp, content = http_request(
      cred.token_uri.encode('idna'), method='POST', body=body,
      headers=cred._generate_refresh_request_headers())
  # pylint: enable=protected-access
  if resp.status == 200:
    d = json.loads(content)
    return d.get('id_token', None)
  else:
    return None


def _RefreshServiceAccountIdTokenGoogleAuth(cred, http_client):
  """Get a fresh id_token for the given google-auth credentials.

  Args:
    cred: service_account.ServiceAccountCredentials, the credentials for which
      to refresh the id_token.
    http_client: google.auth.transport.requests, the http transport to refresh
      with.

  Returns:
    str, The id_token if refresh was successful. Otherwise None.
  """
  cred_dict = {
      'client_email': cred.service_account_email,
      'token_uri': cred._token_uri,  # pylint: disable=protected-access
      'private_key': cred.private_key,
      'private_key_id': cred.private_key_id,
  }

  id_token_credentails = (
      google_auth_service_account.IDTokenCredentials.from_service_account_info)
  id_token_cred = id_token_credentails(
      cred_dict, target_audience=config.CLOUDSDK_CLIENT_ID)
  id_token_cred.refresh(http_client.Request())

  return id_token_cred.token


def Store(credentials, account=None, scopes=None):
  """Store credentials according for an account address.

  gcloud only stores user account credentials, service account credentials and
  p12 service account credentials. GCE, IAM impersonation, and Devshell
  credentials are generated in runtime.

  Args:
    credentials: oauth2client.client.Credentials or
      google.auth.credentials.Credentials, The credentials to be stored.
    account: str, The account address of the account they're being stored for.
        If None, the account stored in the core.account property is used.
    scopes: tuple, Custom auth scopes to request. By default CLOUDSDK_SCOPES
        are requested.

  Raises:
    NoActiveAccountException: If account is not provided and there is no
        active account.
  """

  if creds.IsOauth2ClientCredentials(credentials):
    cred_type = creds.CredentialType.FromCredentials(credentials)
  else:
    cred_type = creds.CredentialTypeGoogleAuth.FromCredentials(credentials)

  if not cred_type.is_serializable:
    return

  if not account:
    account = properties.VALUES.core.account.Get()
  if not account:
    raise NoActiveAccountException()

  store = creds.GetCredentialStore()
  store.Store(account, credentials)

  _LegacyGenerator(account, credentials, scopes).WriteTemplate()


def ActivateCredentials(account, credentials):
  """Validates, stores and activates credentials with given account."""
  Refresh(credentials)
  Store(credentials, account)

  properties.PersistProperty(properties.VALUES.core.account, account)


def RevokeCredentials(credentials):
  credentials.revoke(http.Http())


def Revoke(account=None):
  """Revoke credentials and clean up related files.

  Args:
    account: str, The account address for the credentials to be revoked. If
        None, the currently active account is used.

  Returns:
    'True' if this call revoked the account; 'False' if the account was already
    revoked.

  Raises:
    NoActiveAccountException: If account is not provided and there is no
        active account.
    NoCredentialsForAccountException: If the provided account is not tied to any
        known credentials.
    RevokeError: If there was a more general problem revoking the account.
  """
  if not account:
    account = properties.VALUES.core.account.Get()
  if not account:
    raise NoActiveAccountException()

  if account in c_gce.Metadata().Accounts():
    raise RevokeError('Cannot revoke GCE-provided credentials.')

  credentials = Load(account, prevent_refresh=True)
  if not credentials:
    raise NoCredentialsForAccountException(account)

  if isinstance(credentials, c_devshell.DevshellCredentials):
    raise RevokeError(
        'Cannot revoke the automatically provisioned Cloud Shell credential.'
        'This comes from your browser session and will not persist outside'
        'of your connected Cloud Shell session.')

  rv = False
  try:
    if not account.endswith('.gserviceaccount.com'):
      RevokeCredentials(credentials)
      rv = True
  except client.TokenRevokeError as e:
    if e.args[0] == 'invalid_token':
      # Malformed or already revoked
      pass
    elif e.args[0] == 'invalid_request':
      # Service account token
      pass
    else:
      raise

  store = creds.GetCredentialStore()
  store.Remove(account)

  _LegacyGenerator(account, credentials).Clean()
  files.RmTree(config.Paths().LegacyCredentialsDir(account))
  return rv


def AcquireFromWebFlow(launch_browser=True,
                       auth_uri=None,
                       token_uri=None,
                       scopes=None,
                       client_id=None,
                       client_secret=None):
  """Get credentials via a web flow.

  Args:
    launch_browser: bool, Open a new web browser window for authorization.
    auth_uri: str, URI to open for authorization.
    token_uri: str, URI to use for refreshing.
    scopes: string or iterable of strings, scope(s) of the credentials being
      requested.
    client_id: str, id of the client requesting authorization
    client_secret: str, client secret of the client requesting authorization

  Returns:
    client.Credentials, Newly acquired credentials from the web flow.

  Raises:
    FlowError: If there is a problem with the web flow.
  """
  if auth_uri is None:
    auth_uri = properties.VALUES.auth.auth_host.Get(required=True)
  if token_uri is None:
    token_uri = properties.VALUES.auth.token_host.Get(required=True)
  if scopes is None:
    scopes = config.CLOUDSDK_SCOPES
  if client_id is None:
    client_id = properties.VALUES.auth.client_id.Get(required=True)
  if client_secret is None:
    client_secret = properties.VALUES.auth.client_secret.Get(required=True)

  webflow = client.OAuth2WebServerFlow(
      client_id=client_id,
      client_secret=client_secret,
      scope=scopes,
      user_agent=config.CLOUDSDK_USER_AGENT,
      auth_uri=auth_uri,
      token_uri=token_uri,
      pkce=True,
      prompt='select_account')
  return RunWebFlow(webflow, launch_browser=launch_browser)


def RunWebFlow(webflow, launch_browser=True):
  """Runs a preconfigured webflow to get an auth token.

  Args:
    webflow: client.OAuth2WebServerFlow, The configured flow to run.
    launch_browser: bool, Open a new web browser window for authorization.

  Returns:
    client.Credentials, Newly acquired credentials from the web flow.

  Raises:
    FlowError: If there is a problem with the web flow.
  """
  # pylint:disable=g-import-not-at-top, This is imported on demand for
  # performance reasons.
  from googlecloudsdk.core.credentials import flow

  try:
    cred = flow.Run(webflow, launch_browser=launch_browser, http=http.Http())
  except flow.Error as e:
    raise FlowError(e)
  return cred


def AcquireFromToken(refresh_token,
                     token_uri=GOOGLE_OAUTH2_PROVIDER_TOKEN_URI,
                     revoke_uri=GOOGLE_OAUTH2_PROVIDER_REVOKE_URI):
  """Get credentials from an already-valid refresh token.

  Args:
    refresh_token: An oauth2 refresh token.
    token_uri: str, URI to use for refreshing.
    revoke_uri: str, URI to use for revoking.

  Returns:
    client.Credentials, Credentials made from the refresh token.
  """
  cred = client.OAuth2Credentials(
      access_token=None,
      client_id=properties.VALUES.auth.client_id.Get(required=True),
      client_secret=properties.VALUES.auth.client_secret.Get(required=True),
      refresh_token=refresh_token,
      # always start expired
      token_expiry=datetime.datetime.utcnow(),
      token_uri=token_uri,
      user_agent=config.CLOUDSDK_USER_AGENT,
      revoke_uri=revoke_uri)
  return cred


def AcquireFromGCE(account=None):
  """Get credentials from a GCE metadata server.

  Args:
    account: str, The account name to use. If none, the default is used.

  Returns:
    client.Credentials, Credentials taken from the metadata server.

  Raises:
    c_gce.CannotConnectToMetadataServerException: If the metadata server cannot
      be reached.
    TokenRefreshError: If the credentials fail to refresh.
    TokenRefreshReauthError: If the credentials fail to refresh due to reauth.
  """
  credentials = oauth2client_gce.AppAssertionCredentials(email=account)
  Refresh(credentials)
  return credentials


class _LegacyGenerator(object):
  """A class to generate the credential file for other tools, like gsutil & bq.

  The supported credentials types are user account credentials, service account
  credentials, and p12 service account credentials. Gcloud supports two auth
  libraries - oauth2client and google-auth. Eventually, we will deprecate
  oauth2client.
  """

  def __init__(self, account, credentials, scopes=None):
    self.credentials = credentials
    if self._cred_type not in (creds.USER_ACCOUNT_CREDS_NAME,
                               creds.SERVICE_ACCOUNT_CREDS_NAME,
                               creds.P12_SERVICE_ACCOUNT_CREDS_NAME):
      raise creds.CredentialFileSaveError(
          'Unsupported credentials type {0}'.format(type(self.credentials)))
    if scopes is None:
      self.scopes = config.CLOUDSDK_SCOPES
    else:
      self.scopes = scopes

    paths = config.Paths()
    # Bq file is not generated here. bq CLI generates it using the adc at
    # self._adc_path and uses it as the cache.
    # Register so it is cleaned up.
    self._bq_path = paths.LegacyCredentialsBqPath(account)
    self._gsutil_path = paths.LegacyCredentialsGSUtilPath(account)
    self._p12_key_path = paths.LegacyCredentialsP12KeyPath(account)
    self._adc_path = paths.LegacyCredentialsAdcPath(account)

  @property
  def _is_oauth2client(self):
    return creds.IsOauth2ClientCredentials(self.credentials)

  @property
  def _cred_type(self):
    if self._is_oauth2client:
      return creds.CredentialType.FromCredentials(self.credentials).key
    else:
      return creds.CredentialTypeGoogleAuth.FromCredentials(
          self.credentials).key

  def Clean(self):
    """Remove the credential file."""

    paths = [
        self._bq_path,
        self._gsutil_path,
        self._p12_key_path,
        self._adc_path,
    ]
    for p in paths:
      try:
        os.remove(p)
      except OSError:
        # file did not exist, so we're already done.
        pass

  def WriteTemplate(self):
    """Write the credential file."""

    # Generates credentials used by bq and gsutil.
    if self._cred_type == creds.P12_SERVICE_ACCOUNT_CREDS_NAME:
      cred = self.credentials
      key = cred._private_key_pkcs12  # pylint: disable=protected-access
      password = cred._private_key_password  # pylint: disable=protected-access
      files.WriteBinaryFileContents(self._p12_key_path, key, private=True)

      # the .boto file gets some different fields
      self._WriteFileContents(
          self._gsutil_path, '\n'.join([
              '[Credentials]',
              'gs_service_client_id = {account}',
              'gs_service_key_file = {key_file}',
              'gs_service_key_file_password = {key_password}',
          ]).format(account=self.credentials.service_account_email,
                    key_file=self._p12_key_path,
                    key_password=password))
      return
    creds.ADC(self.credentials).DumpADCToFile(file_path=self._adc_path)

    if self._cred_type == creds.USER_ACCOUNT_CREDS_NAME:
      # We create a small .boto file for gsutil, to be put in BOTO_PATH.
      # Our client_id and client_secret should accompany our refresh token;
      # if a user loaded any other .boto files that specified a different
      # id and secret, those would override our id and secret, causing any
      # attempts to obtain an access token with our refresh token to fail.
      self._WriteFileContents(
          self._gsutil_path, '\n'.join([
              '[OAuth2]',
              'client_id = {cid}',
              'client_secret = {secret}',
              '',
              '[Credentials]',
              'gs_oauth2_refresh_token = {token}',
          ]).format(cid=config.CLOUDSDK_CLIENT_ID,
                    secret=config.CLOUDSDK_CLIENT_NOTSOSECRET,
                    token=self.credentials.refresh_token))
    else:
      self._WriteFileContents(
          self._gsutil_path, '\n'.join([
              '[Credentials]',
              'gs_service_key_file = {key_file}',
          ]).format(key_file=self._adc_path))

  def _WriteFileContents(self, filepath, contents):
    """Writes contents to a path, ensuring mkdirs.

    Args:
      filepath: str, The path of the file to write.
      contents: str, The contents to write to the file.
    """

    full_path = os.path.realpath(files.ExpandHomeDir(filepath))
    files.WriteFileContents(full_path, contents, private=True)
