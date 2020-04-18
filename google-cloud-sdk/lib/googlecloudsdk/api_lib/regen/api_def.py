# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Base template using which the apis_map.py is generated."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


class APIDef(object):
  """Struct for info required to instantiate clients/messages for API versions.

  Attributes:
    class_path: str, Path to the package containing api related modules.
    client_classpath: str, Relative path to the client class for an API version.
    client_full_classpath: str, Full path to the client class for an API
      version.
    messages_modulepath: str, Relative path to the messages module for an API
      version.
    messages_full_modulepath: str, Full path to the messages module for an API
      version.
    default_version: bool, Whether this API version is the default version for
      the API.
    enable_mtls: bool, Whether this API version supports mTLS.
    mtls_endpoint_override: str, The mTLS endpoint for this API version. If
      empty, the MTLS_BASE_URL in the API client will be used.
  """

  def __init__(self,
               class_path,
               client_classpath,
               messages_modulepath,
               default_version=False,
               enable_mtls=False,
               mtls_endpoint_override=''):
    self.class_path = class_path
    self.client_classpath = client_classpath
    self.messages_modulepath = messages_modulepath
    self.default_version = default_version
    self.enable_mtls = enable_mtls
    self.mtls_endpoint_override = mtls_endpoint_override

  @property
  def client_full_classpath(self):
    return self.class_path + '.' + self.client_classpath

  @property
  def messages_full_modulepath(self):
    return self.class_path + '.' + self.messages_modulepath

  def __eq__(self, other):
    return (isinstance(other, self.__class__) and
            self.__dict__ == other.__dict__)

  def __ne__(self, other):
    return not self.__eq__(other)

  def get_init_source(self):
    src_fmt = 'APIDef("{0}", "{1}", "{2}", {3}, {4}, "{5}")'
    return src_fmt.format(self.class_path, self.client_classpath,
                          self.messages_modulepath, self.default_version,
                          self.enable_mtls, self.mtls_endpoint_override)

  def __repr__(self):
    return self.get_init_source()
