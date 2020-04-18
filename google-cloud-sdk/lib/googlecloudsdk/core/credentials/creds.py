# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Utilities to manage credentials."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
import base64
import copy
import json
import os

import enum

from googlecloudsdk.core import config
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import devshell as c_devshell
from googlecloudsdk.core.credentials import reauth
from googlecloudsdk.core.util import files

from oauth2client import client
from oauth2client import service_account
from oauth2client.contrib import gce as oauth2client_gce
import six
import sqlite3
from google.auth import _oauth2client as oauth2client_helper
from google.auth import compute_engine as google_auth_compute_engine
from google.auth import credentials as google_auth_creds
from google.oauth2 import service_account as google_auth_service_account

ADC_QUOTA_PROJECT_FIELD_NAME = 'quota_project_id'

_TOKEN_URI = 'https://oauth2.googleapis.com/token'
_REVOKE_URI = 'https://accounts.google.com/o/oauth2/revoke'

UNKNOWN_CREDS_NAME = 'unknown'
USER_ACCOUNT_CREDS_NAME = 'authorized_user'
SERVICE_ACCOUNT_CREDS_NAME = 'service_account'
P12_SERVICE_ACCOUNT_CREDS_NAME = 'service_account_p12'
DEVSHELL_CREDS_NAME = 'devshell'
GCE_CREDS_NAME = 'gce'


class Error(exceptions.Error):
  """Exceptions for this module."""


class UnknownCredentialsType(Error):
  """An error for when we fail to determine the type of the credentials."""


class CredentialFileSaveError(Error):
  """An error for when we fail to save a credential file."""


class ADCError(Error):
  """An error when processing application default credentials."""


def IsOauth2ClientCredentials(creds):
  return isinstance(creds, client.OAuth2Credentials)


def IsGoogleAuthCredentials(creds):
  return isinstance(creds, google_auth_creds.Credentials)


@six.add_metaclass(abc.ABCMeta)
class CredentialStore(object):
  """Abstract definition of credential store."""

  @abc.abstractmethod
  def GetAccounts(self):
    """Get all accounts that have credentials stored for the CloudSDK.

    Returns:
      {str}, Set of accounts.
    """
    return NotImplemented

  @abc.abstractmethod
  def Load(self, account_id):
    return NotImplemented

  @abc.abstractmethod
  def Store(self, account_id, credentials):
    return NotImplemented

  @abc.abstractmethod
  def Remove(self, account_id):
    return NotImplemented

_CREDENTIAL_TABLE_NAME = 'credentials'


class _SqlCursor(object):
  """Context manager to access sqlite store."""

  def __init__(self, store_file):
    self._store_file = store_file
    self._connection = None
    self._cursor = None

  def __enter__(self):
    self._connection = sqlite3.connect(
        self._store_file,
        detect_types=sqlite3.PARSE_DECLTYPES,
        isolation_level=None,  # Use autocommit mode.
        check_same_thread=True  # Only creating thread may use the connection.
    )
    # Wait up to 1 second for any locks to clear up.
    # https://sqlite.org/pragma.html#pragma_busy_timeout
    self._connection.execute('PRAGMA busy_timeout = 1000')
    self._cursor = self._connection.cursor()
    return self

  def __exit__(self, exc_type, unused_value, unused_traceback):
    if not exc_type:
      # Don't try to commit if exception is in progress.
      self._connection.commit()
    self._connection.close()

  def Execute(self, *args):
    return self._cursor.execute(*args)


class SqliteCredentialStore(CredentialStore):
  """Sqllite backed credential store."""

  def __init__(self, store_file):
    self._cursor = _SqlCursor(store_file)
    self._Execute(
        'CREATE TABLE IF NOT EXISTS "{}" '
        '(account_id TEXT PRIMARY KEY, value BLOB)'
        .format(_CREDENTIAL_TABLE_NAME))

  def _Execute(self, *args):
    with self._cursor as cur:
      return cur.Execute(*args)

  def GetAccounts(self):
    with self._cursor as cur:
      return set(key[0] for key in cur.Execute(
          'SELECT account_id FROM "{}" ORDER BY rowid'
          .format(_CREDENTIAL_TABLE_NAME)))

  def Load(self, account_id, use_google_auth=False):
    with self._cursor as cur:
      item = cur.Execute(
          'SELECT value FROM "{}" WHERE account_id = ?'
          .format(_CREDENTIAL_TABLE_NAME), (account_id,)).fetchone()
    if item is None:
      return None
    if use_google_auth:
      try:
        return FromJsonGoogleAuth(item[0])
      except UnknownCredentialsType:
        pass
    return FromJson(item[0])

  def Store(self, account_id, credentials):
    """Stores the input credentials to the record of account_id in the cache.

    Args:
      account_id: string, the account ID of the input credentials.
      credentials: google.auth.credentials.Credentials or
        client.OAuth2Credentials, the credentials to be stored.
    """
    if IsOauth2ClientCredentials(credentials):
      value = ToJson(credentials)
    else:
      value = ToJsonGoogleAuth(credentials)
    self._Execute(
        'REPLACE INTO "{}" (account_id, value) VALUES (?,?)'
        .format(_CREDENTIAL_TABLE_NAME), (account_id, value))

  def Remove(self, account_id):
    self._Execute(
        'DELETE FROM "{}" WHERE account_id = ?'
        .format(_CREDENTIAL_TABLE_NAME), (account_id,))


_ACCESS_TOKEN_TABLE = 'access_tokens'


class AccessTokenCache(object):
  """Sqlite implementation of for access token cache."""

  def __init__(self, store_file):
    self._cursor = _SqlCursor(store_file)
    self._Execute(
        'CREATE TABLE IF NOT EXISTS "{}" '
        '(account_id TEXT PRIMARY KEY, '
        'access_token TEXT, '
        'token_expiry TIMESTAMP, '
        'rapt_token TEXT, '
        'id_token TEXT)'.format(_ACCESS_TOKEN_TABLE))

    # Older versions of the access_tokens database may not have the id_token
    # column, so we will add it if we can't access it.
    try:
      self._Execute(
          'SELECT id_token FROM "{}" LIMIT 1'.format(_ACCESS_TOKEN_TABLE))
    except sqlite3.OperationalError:
      self._Execute('ALTER TABLE "{}" ADD COLUMN id_token TEXT'.format(
          _ACCESS_TOKEN_TABLE))

  def _Execute(self, *args):
    with self._cursor as cur:
      cur.Execute(*args)

  def Load(self, account_id):
    with self._cursor as cur:
      return cur.Execute(
          'SELECT access_token, token_expiry, rapt_token, id_token '
          'FROM "{}" WHERE account_id = ?'
          .format(_ACCESS_TOKEN_TABLE), (account_id,)).fetchone()

  def Store(self, account_id, access_token, token_expiry, rapt_token, id_token):
    try:
      self._Execute(
          'REPLACE INTO "{}" '
          '(account_id, access_token, token_expiry, rapt_token, id_token) '
          'VALUES (?,?,?,?,?)'
          .format(_ACCESS_TOKEN_TABLE),
          (account_id, access_token, token_expiry, rapt_token, id_token))
    except sqlite3.OperationalError as e:
      log.warning('Could not store access token in cache: {}'.format(str(e)))

  def Remove(self, account_id):
    try:
      self._Execute(
          'DELETE FROM "{}" WHERE account_id = ?'
          .format(_ACCESS_TOKEN_TABLE), (account_id,))
    except sqlite3.OperationalError as e:
      log.warning('Could not delete access token from cache: {}'.format(str(e)))


class AccessTokenStore(client.Storage):
  """Oauth2client adapted for access token cache.

  This class works with Oauth2client model where access token is part of
  credential serialization format and get captured as part of that.
  By extending client.Storage this class pretends to serialize credentials, but
  only serializes access token.

  When fetching the more recent credentials from the cache, this does not return
  token_response, as it is now out of date.
  """

  def __init__(self, access_token_cache, account_id, credentials):
    """Sets up token store for given acount.

    Args:
      access_token_cache: AccessTokenCache, cache for access tokens.
      account_id: str, account for which token is stored.
      credentials: oauth2client.client.OAuth2Credentials, they are auto-updated
        with cached access token.
    """
    super(AccessTokenStore, self).__init__(lock=None)
    self._access_token_cache = access_token_cache
    self._account_id = account_id
    self._credentials = credentials

  def locked_get(self):
    token_data = self._access_token_cache.Load(self._account_id)
    if token_data:
      access_token, token_expiry, rapt_token, id_token = token_data
      self._credentials.access_token = access_token
      self._credentials.token_expiry = token_expiry
      if rapt_token is not None:
        self._credentials.rapt_token = rapt_token
      self._credentials.id_tokenb64 = id_token
      self._credentials.token_response = None
    return self._credentials

  def locked_put(self, credentials):
    if getattr(self._credentials, 'token_response'):
      id_token = self._credentials.token_response.get('id_token', None)
    else:
      id_token = None

    self._access_token_cache.Store(
        self._account_id,
        self._credentials.access_token,
        self._credentials.token_expiry,
        getattr(self._credentials, 'rapt_token', None),
        id_token)

  def locked_delete(self):
    self._access_token_cache.Remove(self._account_id)


class AccessTokenStoreGoogleAuth(object):
  """google-auth adapted for access token cache.

  This class works with google-auth credentials and serializes its short lived
  tokens, including access token, token expiry, rapt token, id token into the
  access token cache.
  """

  def __init__(self, access_token_cache, account_id, credentials):
    """Sets up token store for given account.

    Args:
      access_token_cache: AccessTokenCache, cache for access tokens.
      account_id: str, account for which token is stored.
      credentials: google.auth.credentials.Credentials, credentials of account
        of account_id.
    """
    self._access_token_cache = access_token_cache
    self._account_id = account_id
    self._credentials = credentials

  def Get(self):
    """Gets credentials with short lived tokens from the internal cache.

    Retrieves the short lived tokens from the internal access token cache,
    populates the credentials with these tokens and returns the credentials.

    Returns:
       google.auth.credentials.Credentials
    """
    token_data = self._access_token_cache.Load(self._account_id)
    if token_data:
      access_token, token_expiry, rapt_token, id_token = token_data
      self._credentials.token = access_token
      self._credentials.expiry = token_expiry
      self._credentials._rapt_token = rapt_token  # pylint: disable=protected-access
      # The id_token in cache and in google-auth creds is encoded. However,
      # the id_token of oauth2client creds is decoded and it adds another field
      # 'id_tokenb64' to store the encoded copy. To keep google-auth creds
      # consistent with oauth2client, we add it.
      self._credentials._id_token = id_token  # pylint: disable=protected-access
      self._credentials.id_tokenb64 = id_token
    return self._credentials

  def Put(self):
    """Puts the short lived tokens of the credentials to the internal cache."""
    id_token = getattr(self._credentials, 'id_tokenb64', None) or getattr(
        self._credentials, 'id_token', None)
    expiry = getattr(self._credentials, 'expiry', None)
    rapt_token = getattr(self._credentials, 'rapt_token', None)
    self._access_token_cache.Store(self._account_id, self._credentials.token,
                                   expiry, rapt_token, id_token)

  def Delete(self):
    """Removes the tokens of the account from the internal cache."""
    self._access_token_cache.Remove(self._account_id)


def MaybeAttachAccessTokenCacheStore(credentials,
                                     access_token_file=None):
  """Attaches access token cache to given credentials if no store set.

  Note that credentials themselves will not be persisted only access token. Use
  this whenever access token caching is desired, yet credentials themselves
  should not be persisted.

  Args:
    credentials: oauth2client.client.OAuth2Credentials.
    access_token_file: str, optional path to use for access token storage.
  Returns:
    oauth2client.client.OAuth2Credentials, reloaded credentials.
  """
  if credentials.store is not None:
    return credentials
  account_id = getattr(credentials, 'service_account_email', None)
  if not account_id:
    account_id = six.text_type(hash(credentials.refresh_token))

  access_token_cache = AccessTokenCache(
      access_token_file or config.Paths().access_token_db_path)
  store = AccessTokenStore(access_token_cache, account_id, credentials)
  credentials.set_store(store)
  # Return from the store, which will reload credentials with access token info.
  return store.get()


class CredentialStoreWithCache(CredentialStore):
  """Implements CredentialStore for caching credentials information.

  Static credentials information, such as client ID and service account email,
  are stored in credentials.db. The short lived credentials tokens, such as
  access token, are cached in access_tokens.db.
  """

  def __init__(self, credential_store, access_token_cache):
    """Sets up credentials store for caching credentials.

    Args:
      credential_store: SqliteCredentialStore, for caching static credentials
        information, such as client ID, service account email, etc.
      access_token_cache: AccessTokenCache, for caching short lived credentials
        tokens, such as access token.
    """
    self._credential_store = credential_store
    self._access_token_cache = access_token_cache

  def _WrapCredentialsRefreshWithAutoCaching(self, credentials, store):
    """Wraps the refresh method of credentials with auto caching logic.

    For auto caching short lived tokens of google-auth credentials, such as
    access token, on credentials refresh.

    Args:
      credentials: google.auth.credentials.Credentials, the credentials updated
        by this method.
      store: AccessTokenStoreGoogleAuth, the store that caches the tokens of the
        input credentials.

    Returns:
      google.auth.credentials.Credentials, the updated credentials.
    """
    orig_refresh = credentials.refresh

    def _WrappedRefresh(request):
      orig_refresh(request)
      # credentials are part of store. Calling Put() on store caches the
      # short lived tokens of the credentials.
      store.Put()

    credentials.refresh = _WrappedRefresh
    return credentials

  def GetAccounts(self):
    """Returns all the accounts stored in the cache."""
    return self._credential_store.GetAccounts()

  def Load(self, account_id, use_google_auth=False):
    """Loads the credentials of account_id from the cache.

    Args:
      account_id: string, ID of the account to load.
      use_google_auth: bool, True to load google-auth credentials if the type of
        the credentials is supported by the cache. False to load oauth2client
        credentials.

    Returns:
      1. None, if credentials are not found in the cache.
      2. google.auth.credentials.Credentials, if use_google_auth is true.
      3. client.OAuth2Credentials.
    """
    # Loads static credentials information from self._credential_store.
    credentials = self._credential_store.Load(account_id, use_google_auth)
    if credentials is None:
      return None

    # Loads short lived tokens from self._access_token_cache.
    if IsOauth2ClientCredentials(credentials):
      store = AccessTokenStore(self._access_token_cache, account_id,
                               credentials)
      credentials.set_store(store)
      return store.get()
    else:
      store = AccessTokenStoreGoogleAuth(self._access_token_cache, account_id,
                                         credentials)
      credentials = store.Get()

      # google-auth credentials do not support auto caching access token on
      # credentials refresh. This logic needs to be implemented in gcloud.
      return self._WrapCredentialsRefreshWithAutoCaching(credentials, store)

  def Store(self, account_id, credentials):
    """Stores credentials into the cache with account of account_id.

    Args:
      account_id: string, the account that will be associated with credentials
        in the cache.
      credentials: google.auth.credentials.Credentials or
        client.OAuth2Credentials, the credentials to be stored.
    """
    # Stores short lived tokens to self._access_token_cache.
    if IsOauth2ClientCredentials(credentials):
      store = AccessTokenStore(self._access_token_cache, account_id,
                               credentials)
      credentials.set_store(store)
      store.put(credentials)
    else:
      store = AccessTokenStoreGoogleAuth(self._access_token_cache, account_id,
                                         credentials)
      store.Put()

    # Stores static credentials information to self._credential_store.
    self._credential_store.Store(account_id, credentials)

  def Remove(self, account_id):
    """Removes credentials of account_id from the cache."""
    self._credential_store.Remove(account_id)
    self._access_token_cache.Remove(account_id)


def GetCredentialStore(store_file=None, access_token_file=None):
  """Constructs credential store.

  Args:
    store_file: str, optional path to use for storage. If not specified
      config.Paths().credentials_path will be used.

    access_token_file: str, optional path to use for access token storage. Note
      that some implementations use store_file to also store access_tokens, in
      which case this argument is ignored.

  Returns:
    CredentialStore object.
  """
  return _GetSqliteStore(store_file, access_token_file)


class CredentialType(enum.Enum):
  """Enum of oauth2client credential types managed by gcloud."""

  UNKNOWN = (0, UNKNOWN_CREDS_NAME, False, False)
  USER_ACCOUNT = (1, USER_ACCOUNT_CREDS_NAME, True, True)
  SERVICE_ACCOUNT = (2, SERVICE_ACCOUNT_CREDS_NAME, True, False)
  P12_SERVICE_ACCOUNT = (3, P12_SERVICE_ACCOUNT_CREDS_NAME, True, False)
  DEVSHELL = (4, DEVSHELL_CREDS_NAME, False, True)
  GCE = (5, GCE_CREDS_NAME, False, False)

  def __init__(self, type_id, key, is_serializable, is_user):
    self.type_id = type_id
    self.key = key
    self.is_serializable = is_serializable
    # True if this corresponds to a "user" or 3LO credential as opposed to a
    # service account of some kind.
    self.is_user = is_user

  @staticmethod
  def FromTypeKey(key):
    for cred_type in CredentialType:
      if cred_type.key == key:
        return cred_type
    return CredentialType.UNKNOWN

  @staticmethod
  def FromCredentials(creds):
    if isinstance(creds, c_devshell.DevshellCredentials):
      return CredentialType.DEVSHELL
    if isinstance(creds, oauth2client_gce.AppAssertionCredentials):
      return CredentialType.GCE
    if isinstance(creds, service_account.ServiceAccountCredentials):
      if getattr(creds, '_private_key_pkcs12', None) is not None:
        return CredentialType.P12_SERVICE_ACCOUNT
      return CredentialType.SERVICE_ACCOUNT
    if getattr(creds, 'refresh_token', None) is not None:
      return CredentialType.USER_ACCOUNT
    return CredentialType.UNKNOWN


class CredentialTypeGoogleAuth(enum.Enum):
  """Enum of google-auth credential types managed by gcloud."""

  UNKNOWN = (0, UNKNOWN_CREDS_NAME, False, False)
  USER_ACCOUNT = (1, USER_ACCOUNT_CREDS_NAME, True, True)
  SERVICE_ACCOUNT = (2, SERVICE_ACCOUNT_CREDS_NAME, True, False)
  GCE = (3, GCE_CREDS_NAME, False, False)
  DEVSHELL = (4, DEVSHELL_CREDS_NAME, False, True)

  def __init__(self, type_id, key, is_serializable, is_user):
    """Builds a credentials type instance given the credentials information.

    Args:
      type_id: string, ID for the credentials type, based on the enum constant
        value of the type.
      key: string, key of the credentials type, based on the enum constant value
        of the type.
      is_serializable: bool, whether the type of the credentials is
        serializable, based on the enum constant value of the type.
      is_user: bool, True if the credentials are of user account. False
        otherwise.

    Returns:
      CredentialTypeGoogleAuth, an instance of CredentialTypeGoogleAuth which
        is a gcloud internal representation of type of the google-auth
        credentials.
    """
    self.type_id = type_id
    self.key = key
    self.is_serializable = is_serializable
    # True if this corresponds to a "user" or 3LO credential as opposed to a
    # service account of some kind.
    self.is_user = is_user

  @staticmethod
  def FromTypeKey(key):
    """Returns the credentials type based on the input key."""
    for cred_type in CredentialTypeGoogleAuth:
      if cred_type.key == key:
        return cred_type
    return CredentialTypeGoogleAuth.UNKNOWN

  @staticmethod
  def FromCredentials(creds):
    """Returns the credentials type based on the input credentials."""
    if isinstance(creds, c_devshell.DevShellCredentialsGoogleAuth):
      return CredentialTypeGoogleAuth.DEVSHELL
    if isinstance(creds, google_auth_compute_engine.Credentials):
      return CredentialTypeGoogleAuth.GCE
    if isinstance(creds, google_auth_service_account.Credentials):
      return CredentialTypeGoogleAuth.SERVICE_ACCOUNT
    if getattr(creds, 'refresh_token', None) is not None:
      return CredentialTypeGoogleAuth.USER_ACCOUNT
    return CredentialTypeGoogleAuth.UNKNOWN


def ToJson(credentials):
  """Given Oauth2client credentials return library independent json for it."""
  creds_type = CredentialType.FromCredentials(credentials)
  if creds_type == CredentialType.USER_ACCOUNT:
    creds_dict = {
        'type': creds_type.key,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'refresh_token': credentials.refresh_token
    }
    # These fields are optionally serialized as they are not required for
    # credentials to be usable, these are used by Oauth2client.
    for field in ('id_token', 'invalid', 'revoke_uri', 'scopes',
                  'token_response', 'token_uri', 'user_agent', 'rapt_token'):
      value = getattr(credentials, field, None)
      if value:
        # Sets are not json serializable as is, so encode as a list.
        if isinstance(value, set):
          value = list(value)
        creds_dict[field] = value

  elif creds_type == CredentialType.SERVICE_ACCOUNT:
    creds_dict = credentials.serialization_data
  elif creds_type == CredentialType.P12_SERVICE_ACCOUNT:
    # pylint: disable=protected-access
    creds_dict = {
        'client_email': credentials._service_account_email,
        'type': creds_type.key,
        # The base64 only deals with bytes. The encoded value is bytes but is
        # known to be a safe ascii string. To serialize it, convert it to a
        # text object.
        'private_key': (base64.b64encode(credentials._private_key_pkcs12)
                        .decode('ascii')),
        'password': credentials._private_key_password
    }
  else:
    raise UnknownCredentialsType(creds_type)
  return json.dumps(creds_dict, sort_keys=True,
                    indent=2, separators=(',', ': '))


def ToJsonGoogleAuth(credentials):
  """Given google-auth credentials, return library independent json for it."""
  creds_type = CredentialTypeGoogleAuth.FromCredentials(credentials)
  if creds_type == CredentialTypeGoogleAuth.SERVICE_ACCOUNT:
    creds_dict = {
        'type': creds_type.key,
        'client_email': credentials.service_account_email,
        'private_key_id': credentials.private_key_id,
        'private_key': credentials.private_key,
        'client_id': credentials.client_id,
        # '_token_uri' is not exposed in a public property in the service
        # credentials implementation which does not currently support
        # serialization, so pylint: disable=protected-access
        'token_uri': credentials._token_uri,  # pylint: disable=protected-access
        'project_id': credentials.project_id,
    }
  elif creds_type == CredentialTypeGoogleAuth.USER_ACCOUNT:
    creds_dict = {
        'type': creds_type.key,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'refresh_token': credentials.refresh_token,
        'revoke_uri': _REVOKE_URI,
        'scopes': credentials._scopes,  # pylint: disable=protected-access
        'token_uri': credentials.token_uri,
    }
  else:
    raise UnknownCredentialsType(
        'Google auth does not support serialization of {} credentials.'.format(
            creds_type.key))
  return json.dumps(
      creds_dict, sort_keys=True, indent=2, separators=(',', ': '))


def FromJson(json_value):
  """Returns Oauth2client credentials from library independent json format."""
  json_key = json.loads(json_value)
  cred_type = CredentialType.FromTypeKey(json_key['type'])
  if cred_type == CredentialType.SERVICE_ACCOUNT:
    cred = service_account.ServiceAccountCredentials.from_json_keyfile_dict(
        json_key, scopes=config.CLOUDSDK_SCOPES)
    cred.user_agent = cred._user_agent = config.CLOUDSDK_USER_AGENT
  elif cred_type == CredentialType.USER_ACCOUNT:
    cred = client.OAuth2Credentials(
        access_token=None,
        client_id=json_key['client_id'],
        client_secret=json_key['client_secret'],
        refresh_token=json_key['refresh_token'],
        token_expiry=None,
        token_uri=json_key.get('token_uri'),
        user_agent=json_key.get('user_agent'),
        revoke_uri=json_key.get('revoke_uri'),
        id_token=json_key.get('id_token'),
        token_response=json_key.get('token_response'),
        scopes=json_key.get('scopes'),
        token_info_uri=json_key.get('token_info_uri'),
        rapt_token=json_key.get('rapt_token'),
    )
  elif cred_type == CredentialType.P12_SERVICE_ACCOUNT:
    # pylint: disable=protected-access
    cred = service_account.ServiceAccountCredentials._from_p12_keyfile_contents(
        service_account_email=json_key['client_email'],
        private_key_pkcs12=base64.b64decode(json_key['private_key']),
        private_key_password=json_key['password'],
        scopes=config.CLOUDSDK_SCOPES)
    cred.user_agent = cred._user_agent = config.CLOUDSDK_USER_AGENT
  else:
    raise UnknownCredentialsType(json_key['type'])
  return cred


def FromJsonGoogleAuth(json_value):
  """Returns google-auth credentials from library independent json format.

  The type of the credentials could be service account, user account,
  or p12 service account. p12 service account was deprecated and is not
  supported by google-auth, so we raise an exception for the callers to handle.

  Args:
    json_value: string, A string of the JSON representation of the credentials.

  Returns:
    google.auth.credentials.Credentials if the credentials type is supported
    by this method.

  Raises:
    UnknownCredentialsType: when the type of the credentials is not service
      account or user account.
  """
  json_key = json.loads(json_value)
  cred_type = CredentialTypeGoogleAuth.FromTypeKey(json_key['type'])
  if cred_type == CredentialTypeGoogleAuth.SERVICE_ACCOUNT:
    # To be backward compatible with oauth2client, which sets the token URI
    # internally if it is not provided.
    if not json_key.get('token_uri'):
      json_key['token_uri'] = _TOKEN_URI
    service_account_credentials = (
        google_auth_service_account.Credentials.from_service_account_info)
    cred = service_account_credentials(json_key, scopes=config.CLOUDSDK_SCOPES)
    # The following fields are not members of the google-auth credentials which
    # are not designed to support persistent caching. These fields will be used
    # by gcloud to build google-auth credentials from cache data.
    cred.private_key = json_key.get('private_key')
    cred.private_key_id = json_key.get('private_key_id')
    cred.client_id = json_key.get('client_id')
    return cred
  if cred_type == CredentialTypeGoogleAuth.USER_ACCOUNT:
    return reauth.UserCredWithReauth.from_authorized_user_info(
        json_key, scopes=json_key.get('scopes'))
  raise UnknownCredentialsType(
      'Google auth does not support deserialization of {} credentials.'.format(
          json_key['type']))


def _GetSqliteStore(sqlite_credential_file=None, sqlite_access_token_file=None):
  """Get a sqlite-based Credential Store."""
  sqlite_credential_file = (sqlite_credential_file or
                            config.Paths().credentials_db_path)
  files.PrivatizeFile(sqlite_credential_file)
  credential_store = SqliteCredentialStore(sqlite_credential_file)

  sqlite_access_token_file = (sqlite_access_token_file or
                              config.Paths().access_token_db_path)
  files.PrivatizeFile(sqlite_access_token_file)
  access_token_cache = AccessTokenCache(sqlite_access_token_file)
  return CredentialStoreWithCache(credential_store, access_token_cache)


def GetQuotaProject(credentials, force_resource_quota):
  """Gets the value to use for the X-Goog-User-Project header.

  Args:
    credentials: The credentials that are going to be used for requests.
    force_resource_quota: bool, If true, resource project quota will be used
      even if gcloud is set to use legacy mode for quota. This should be set
      when calling newer APIs that would not work without resource quota.

  Returns:
    str, The project id to send in the header or None to not populate the
    header.
  """
  if IsOauth2ClientCredentials(credentials):
    if not CredentialType.FromCredentials(credentials).is_user:
      return None
  elif IsGoogleAuthCredentials(credentials):
    if not CredentialTypeGoogleAuth.FromCredentials(credentials).is_user:
      return None

  quota_project = properties.VALUES.billing.quota_project.Get()
  if quota_project == properties.VALUES.billing.CURRENT_PROJECT:
    return properties.VALUES.core.project.Get()
  elif quota_project == properties.VALUES.billing.LEGACY:
    if force_resource_quota:
      return properties.VALUES.core.project.Get()
    return None
  return quota_project


class ADC(object):
  """Application default credential object."""

  def __init__(self, credentials):
    self._credentials = credentials

  @property
  def _is_oauth2client(self):
    return IsOauth2ClientCredentials(self._credentials)

  @property
  def is_user(self):
    if self._is_oauth2client:
      return CredentialType.FromCredentials(self._credentials).is_user
    else:
      return CredentialTypeGoogleAuth.FromCredentials(self._credentials).is_user

  @property
  def adc(self):
    """Json representation of the credentials for ADC."""
    if self._is_oauth2client:
      return _ConvertOauth2ClientCredentialsToADC(self._credentials)
    else:
      return _ConvertGoogleAuthCredentialsToADC(self._credentials)

  def DumpADCToFile(self, file_path=None):
    """Dumps the credentials to the ADC json file."""
    file_path = file_path or config.ADCFilePath()
    return _DumpADCJsonToFile(self.adc, file_path)

  def DumpExtendedADCToFile(self, file_path=None, quota_project=None):
    """Dumps the credentials and the quota project to the ADC json file."""
    if not self.is_user:
      raise CredentialFileSaveError(
          'The credential is not a user credential, so we cannot insert a '
          'quota project to application default credential.')
    file_path = file_path or config.ADCFilePath()
    if not quota_project:
      quota_project = GetQuotaProject(
          self._credentials, force_resource_quota=True)
    extended_adc = self._ExtendADCWithQuotaProject(quota_project)
    return _DumpADCJsonToFile(extended_adc, file_path)

  def _ExtendADCWithQuotaProject(self, quota_project):
    """Add quota_project_id field to ADC json."""
    extended_adc = copy.deepcopy(self.adc)
    if quota_project:
      extended_adc[ADC_QUOTA_PROJECT_FIELD_NAME] = quota_project
    else:
      log.warning(
          'Cannot find a project to insert into application default '
          'credentials (ADC) as a quota project.\n'
          'Run $gcloud auth application-default set-quota-project to insert a '
          'quota project to ADC.')
    return extended_adc


def _DumpADCJsonToFile(adc, file_path):
  """Dumps ADC json object to file."""
  try:
    contents = json.dumps(adc, sort_keys=True, indent=2, separators=(',', ': '))
    files.WriteFileContents(file_path, contents, private=True)
  except files.Error as e:
    log.debug(e, exc_info=True)
    raise CredentialFileSaveError(
        'Error saving Application Default Credentials: ' + six.text_type(e))
  return os.path.abspath(file_path)


def _ConvertOauth2ClientCredentialsToADC(credentials):
  """Converts an oauth2client credentials to application default credentials."""
  creds_type = CredentialType.FromCredentials(credentials)
  if creds_type not in (CredentialType.USER_ACCOUNT,
                        CredentialType.SERVICE_ACCOUNT):
    raise ADCError('Cannot convert credentials of type {} to application '
                   'default credentials.'.format(type(credentials)))
  if creds_type == CredentialType.USER_ACCOUNT:
    credentials = client.GoogleCredentials(
        credentials.access_token, credentials.client_id,
        credentials.client_secret, credentials.refresh_token,
        credentials.token_expiry, credentials.token_uri, credentials.user_agent,
        credentials.revoke_uri)
  return credentials.serialization_data


def _ConvertGoogleAuthCredentialsToADC(credentials):
  """Converts a google-auth credentials to application default credentials."""
  creds_type = CredentialTypeGoogleAuth.FromCredentials(credentials)
  if creds_type == CredentialTypeGoogleAuth.USER_ACCOUNT:
    adc = credentials.to_json(strip=('token', 'token_uri', 'scopes'))
    adc = json.loads(adc)
    adc['type'] = creds_type.key
    return adc
  if creds_type == CredentialTypeGoogleAuth.SERVICE_ACCOUNT:
    return {
        'type': creds_type.key,
        'client_email': credentials.service_account_email,
        'private_key_id': credentials.private_key_id,
        'private_key': credentials.private_key,
        'client_id': credentials.client_id
    }
  raise ADCError('Cannot convert credentials of type {} to application '
                 'default credentials.'.format(type(credentials)))


# TODO(b/147098689): Deprecate this method once credentials store is ready
# to produce credentials of google-auth directly.
def MaybeConvertToGoogleAuthCredentials(credentials, use_google_auth):
  """Converts credentials to type of google-auth under certain conditions.

  The conversion will take place when the below conditions are all met,
  1. use_google_auth is True;
  2. credentials is of type oauth2client;
  3. The input credentials are not built from P12 service account key. The
     reason is that this legacy service account key is not supported by
     google-auth. Additionally, gcloud plans to deprecate P12 service account
     key support. The authentication logic of credentials of this type will be
     left on oauth2client for now and will be removed in the deprecation.

  Args:
    credentials: oauth2client.client.Credentials or
      google.auth.credentials.Credentials
    use_google_auth: bool, True if the calling command indicates to use
      google-auth library for authentication.

  Returns:
    google.auth.credentials.Credentials or oauth2client.client.Credentials
  """
  if not use_google_auth:
    return credentials
  if not IsOauth2ClientCredentials(credentials):
    return credentials
  if CredentialType.FromCredentials(
      credentials) == CredentialType.P12_SERVICE_ACCOUNT:
    return credentials

  # pylint: disable=g-import-not-at-top
  # To work around the circular dependency between this the util and the creds
  # modules.
  from googlecloudsdk.api_lib.iamcredentials import util

  if isinstance(credentials, c_devshell.DevshellCredentials):
    target_creds_type = c_devshell.DevShellCredentialsGoogleAuth
    return target_creds_type.from_devshell_credentials(credentials)
  if isinstance(credentials, util.ImpersonationCredentials):
    target_creds_type = util.ImpersonationCredentialsGoogleAuth
    return target_creds_type.from_impersonation_credentials(credentials)

  target_creds = oauth2client_helper.convert(credentials)
  # token expiry is lost in the conversion.
  target_creds.expiry = getattr(credentials, 'token_expiry', None)
  if (isinstance(target_creds, google_auth_service_account.Credentials) or
      isinstance(target_creds, google_auth_compute_engine.Credentials)):
    # Access token and scopes are lost in the conversions of service acccount
    # and GCE credentials.
    target_creds.token = getattr(credentials, 'access_token', None)
    scopes = getattr(credentials, 'scopes', [])
    scopes = scopes if scopes else config.CLOUDSDK_SCOPES
    # client.OAuth2Credentials converts scopes into a set. google-auth requires
    # scopes to be of a Sequence type.
    target_creds._scopes = list(scopes)  # pylint: disable=protected-access
  return target_creds
