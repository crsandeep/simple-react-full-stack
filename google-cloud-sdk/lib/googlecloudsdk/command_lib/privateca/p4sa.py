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
"""Helpers for dealing with the Private CA P4SA."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudkms import iam as kms_iam
from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.api_lib.services import serviceusage
from googlecloudsdk.api_lib.storage import storage_api


def GetOrCreate(project_ref):
  """Gets (or creates) the P4SA for Private CA in the given project.

  If the P4SA does not exist for this project, it will be created. Otherwise,
  the email address of the existing P4SA will be returned.

  Args:
    project_ref: resources.Resource reference to the project for the P4SA.

  Returns:
    Email address of the Private CA P4SA for the given project.
  """
  service_name = privateca_base.GetServiceName()
  email, _ = serviceusage.GenerateServiceIdentity(project_ref.Name(),
                                                  service_name)
  return email


def AddResourceRoleBindings(p4sa_email, kms_key_ref, bucket_ref):
  """Adds the necessary P4SA role bindings on the given key and bucket.

  Args:
    p4sa_email: Email address of the P4SA for which to add role bindings. This
                can come from a call to GetOrCreate().
    kms_key_ref: resources.Resource reference to the KMS key on which to add
                 a role binding.
    bucket_ref: storage_util.BucketReference to the GCS bucket on which to add
                a role binding.
  """
  principal = 'serviceAccount:{}'.format(p4sa_email)
  kms_iam.AddPolicyBindingToCryptoKey(kms_key_ref, principal,
                                      'roles/cloudkms.signerVerifier')
  client = storage_api.StorageClient()
  client.AddIamPolicyBinding(bucket_ref, principal, 'roles/storage.objectAdmin')
