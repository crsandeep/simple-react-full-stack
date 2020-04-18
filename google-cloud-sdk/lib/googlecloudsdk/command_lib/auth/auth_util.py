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

"""Support library for the auth command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import os
import textwrap

from googlecloudsdk.api_lib.iamcredentials import util as impersonation_util
from googlecloudsdk.core import config
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.credentials import creds as c_creds
from googlecloudsdk.core.credentials import store as c_store
from googlecloudsdk.core.util import files

from oauth2client import client
from oauth2client import service_account
from oauth2client.contrib import gce as oauth2client_gce


ACCOUNT_TABLE_FORMAT = ("""\
    table[title='Credentialed Accounts'](
        status.yesno(yes='*', no=''):label=ACTIVE,
        account
    )""")


class _AcctInfo(object):
  """An auth command resource list item.

  Attributes:
    account: The account name.
    status: The account status, one of ['ACTIVE', ''].
  """

  def __init__(self, account, active):
    self.account = account
    self.status = 'ACTIVE' if active else ''


def AllAccounts():
  """The resource list return value for the auth command Run() method."""
  active_account = properties.VALUES.core.account.Get()
  return [_AcctInfo(account, account == active_account)
          for account in c_store.AvailableAccounts()]


def IsGceAccountCredentials(cred):
  """Checks if the credential is a Compute Engine service account credential."""
  return isinstance(cred, oauth2client_gce.AppAssertionCredentials)


def IsServiceAccountCredential(cred):
  """Checks if the credential is a service account credential."""
  return isinstance(cred, service_account.ServiceAccountCredentials)


def IsImpersonationCredential(cred):
  """Checks if the credential is an impersonated service account credential."""
  return (impersonation_util.
          ImpersonationAccessTokenProvider.IsImpersonationCredential(cred))


def ValidIdTokenCredential(cred):
  return (IsImpersonationCredential(cred) or
          IsServiceAccountCredential(cred) or
          IsGceAccountCredentials(cred))


def PromptIfADCEnvVarIsSet():
  """Warns users if ADC environment variable is set."""
  override_file = config.ADCEnvVariable()
  if override_file:
    message = textwrap.dedent("""
          The environment variable [{envvar}] is set to:
            [{override_file}]
          Credentials will still be generated to the default location:
            [{default_file}]
          To use these credentials, unset this environment variable before
          running your application.
          """.format(
              envvar=client.GOOGLE_APPLICATION_CREDENTIALS,
              override_file=override_file,
              default_file=config.ADCFilePath()))
    console_io.PromptContinue(
        message=message, throw_if_unattended=True, cancel_on_no=True)


def WriteGcloudCredentialsToADC(creds, add_quota_project=False):
  """Writes gclouds's credential from auth login to ADC json."""
  if c_creds.CredentialType.FromCredentials(
      creds) != c_creds.CredentialType.USER_ACCOUNT:
    log.warning('Credentials cannot be written to application default '
                'credentials because it is not a user credential.')
    return
  PromptIfADCEnvVarIsSet()
  if add_quota_project:
    c_creds.ADC(creds).DumpExtendedADCToFile()
  else:
    c_creds.ADC(creds).DumpADCToFile()


def GetADCAsJson():
  """Reads ADC from disk and converts it to a json object."""
  if not os.path.isfile(config.ADCFilePath()):
    return None
  with files.FileReader(config.ADCFilePath()) as f:
    return json.load(f)


def GetQuotaProjectFromADC():
  """Reads the quota project ID from ADC json file and return it."""
  adc_json = GetADCAsJson()
  try:
    return adc_json['quota_project_id']
  except (KeyError, TypeError):
    return None


