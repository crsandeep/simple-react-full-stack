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
"""Provides util methods for iam operations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.api_lib.iam import util as iam_util
from googlecloudsdk.command_lib.projects import util as projects_util
from googlecloudsdk.core import properties


def CreateServiceAccountKey(service_account_ref):
  """Creates and returns a new service account key."""
  iam_client, iam_messages = iam_util.GetClientAndMessages()
  key_request = iam_messages.CreateServiceAccountKeyRequest(
      privateKeyType=(
          iam_messages.CreateServiceAccountKeyRequest
          .PrivateKeyTypeValueValuesEnum.TYPE_GOOGLE_CREDENTIALS_FILE))
  return iam_client.projects_serviceAccounts_keys.Create(
      iam_messages.IamProjectsServiceAccountsKeysCreateRequest(
          name=service_account_ref.RelativeName(),
          createServiceAccountKeyRequest=key_request))


def GetProjectRolesForServiceAccount(service_account_ref):
  """Returns the project roles the given service account is a member of."""
  project_ref = projects_util.ParseProject(properties.VALUES.core.project.Get())
  iam_policy = projects_api.GetIamPolicy(project_ref)

  roles = set()
  # iam_policy.bindings looks like:
  # list[<Binding
  #       members=['serviceAccount:member@thing.iam.gserviceaccount.com',...]
  #       role='roles/somerole'>...]
  for binding in iam_policy.bindings:
    if any(
        m.endswith(':' + service_account_ref.Name()) for m in binding.members):
      roles.add(binding.role)
  return roles
