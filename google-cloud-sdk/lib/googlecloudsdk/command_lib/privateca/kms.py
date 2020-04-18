# Lint as: python3
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
"""Utilities for dealing with KMS resources in Private CA."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudkms import cryptokeyversions
from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.command_lib.privateca import exceptions


def _KmsKeyAlgorithmToPrivateCaKeyType(messages, kms_algorithm):
  name = kms_algorithm.name
  if name.startswith('RSA_SIGN_PSS_') or name.startswith('RSA_SIGN_PKCS1_'):
    return messages.PublicKey.TypeValueValuesEnum.PEM_RSA_KEY
  if name.startswith('EC_'):
    return messages.PublicKey.TypeValueValuesEnum.PEM_EC_KEY

  raise exceptions.UnsupportedKmsKeyTypeException()


def GetPublicKey(kms_key_version_ref):
  """Get a KMS key version's public key as a Private CA proto message."""
  messages = privateca_base.GetMessagesModule()

  public_key = cryptokeyversions.GetPublicKey(kms_key_version_ref)
  key_type = _KmsKeyAlgorithmToPrivateCaKeyType(messages, public_key.algorithm)

  return messages.PublicKey(
      key=public_key.pem.encode('utf-8'),
      type=key_type)
