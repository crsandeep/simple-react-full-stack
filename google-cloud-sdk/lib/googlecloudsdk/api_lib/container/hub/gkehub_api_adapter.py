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

"""Adapter for interaction with gkehub One Platform APIs."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import base64
import binascii
import json

from googlecloudsdk.api_lib.container import api_adapter
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import resources as cloud_resources
from googlecloudsdk.core.credentials import http
from googlecloudsdk.core.util import encoding as core_encoding
from six.moves import urllib


def NewAPIAdapter(api_version):
  return InitAPIAdapter(api_version, APIAdapter)


def InitAPIAdapter(api_version, adapter):
  """Initialize an api adapter.

  Args:
    api_version: the api version we want.
    adapter: the api adapter constructor.
  Returns:
    APIAdapter object.
  """

  api_client = core_apis.GetClientInstance('gkehub', api_version)
  api_client.check_response_func = api_adapter.CheckResponse
  messages = api_client.MESSAGES_MODULE

  registry = cloud_resources.REGISTRY.Clone()
  registry.RegisterApiByName('gkehub', api_version)

  return adapter(registry, api_client, messages, api_version)


class APIAdapter(object):
  """Handles making api requests in a version-agnostic way."""

  _HTTP_ERROR_FORMAT = ('HTTP request failed with status code {}. '
                        'Response content: {}')

  def __init__(self, registry, client, messages, api_version):
    self.registry = registry
    self.client = client
    self.messages = messages
    self.api_version = api_version

  def GenerateConnectAgentManifest(self, option):
    """Generate the YAML manifest to deploy the Connect Agent.

    Args:
      option: an instance of ConnectAgentOption.

    Returns:
      A slice of connect agent manifest resources.
    Raises:
      Error: if the API call to generate connect agent manifest failed.
    """
    # Can't directly use the generated API client given that it currently
    # doesn't support nested messages. See the discussion here:
    # https://groups.google.com/a/google.com/forum/#!msg/cloud-sdk-eng/hwdwUTEmvlw/fRdrvK26AAAJ
    query_params = [
        ('connectAgent.namespace', option.namespace),
        ('connectAgent.proxy', option.proxy),
        ('isUpgrade', option.is_upgrade),
        ('version', option.version),
        ('registry', option.registry),
        ('image_pull_secret_content', option.image_pull_secret_content)
    ]
    base_url = self.client.url
    url = '{}/{}/{}:generateConnectManifest?{}'.format(
        base_url,
        self.api_version,
        option.membership_ref,
        urllib.parse.urlencode(query_params))
    response, raw_content = http.Http().request(uri=url)
    content = core_encoding.Decode(raw_content)
    status_code = response.get('status')
    if status_code != '200':
      msg = self._HTTP_ERROR_FORMAT.format(status_code, content)
      raise exceptions.HttpException(msg)
    return json.loads(content).get('manifest')


class ConnectAgentOption(object):
  """Option for generating connect agent manifest."""

  def __init__(self,
               name,
               proxy,
               namespace,
               is_upgrade,
               version,
               registry,
               image_pull_secret_content,
               membership_ref):
    # TODO(b/143641551): make sure GKE On-Prem is compatible with non-base64
    # encoded string before removing this check.
    if proxy:
      try:
        base64.standard_b64decode(proxy)
      # Python 2 and Python 3 use different errors.
      except (TypeError, binascii.Error):
        proxy = base64.standard_b64encode(proxy.encode('ascii'))
    self.name = name
    self.proxy = proxy
    self.namespace = namespace
    self.is_upgrade = is_upgrade
    self.version = version
    self.registry = registry
    self.image_pull_secret_content = image_pull_secret_content
    self.membership_ref = membership_ref
