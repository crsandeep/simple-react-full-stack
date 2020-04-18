# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Dynamic context for connection to Cloud Run."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import abc
import base64
import contextlib
import os
import re
import ssl
import sys
import tempfile
from googlecloudsdk.api_lib.run import gke
from googlecloudsdk.api_lib.run import global_methods
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import exceptions as serverless_exceptions
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files

import httplib2
import six
from six.moves.urllib import parse as urlparse


_EVENTS_API_VERSION = 'v1alpha1'


@contextlib.contextmanager
def _OverrideEndpointOverrides(override):
  """Context manager to override the Cloud Run endpoint overrides for a while.

  Args:
    override: str, New value for Cloud Run endpoint.
  Yields:
    None.
  """
  old_endpoint = properties.VALUES.api_endpoint_overrides.run.Get()
  try:
    properties.VALUES.api_endpoint_overrides.run.Set(override)
    yield
  finally:
    properties.VALUES.api_endpoint_overrides.run.Set(old_endpoint)


class ConnectionInfo(six.with_metaclass(abc.ABCMeta)):
  """Information useful in constructing an API client."""

  def __init__(self, version):
    """Initialize a connection context.

    Args:
      version: str, api version to use for making requests.
    """
    self.endpoint = None
    self.ca_certs = None
    self.region = None
    self._cm = None
    self._version = version

  @property
  def api_name(self):
    return global_methods.SERVERLESS_API_NAME

  @property
  def api_version(self):
    return self._version

  @property
  def active(self):
    return self._active

  @abc.abstractmethod
  def Connect(self):
    pass

  @abc.abstractproperty
  def operator(self):
    pass

  @abc.abstractproperty
  def ns_label(self):
    pass

  @abc.abstractproperty
  def supports_one_platform(self):
    pass

  @abc.abstractproperty
  def location_label(self):
    pass

  def HttpClient(self):
    """The HTTP client to use to connect.

    May only be called inside the context represented by this ConnectionInfo

    Returns: An HTTP client specialized to connect in this context, or None if
    a standard HTTP client is appropriate.
    """
    return None

  def __enter__(self):
    self._active = True
    self._cm = self.Connect()
    return self._cm.__enter__()

  def __exit__(self, typ, value, traceback):
    self._active = False
    return self._cm.__exit__(typ, value, traceback)


def _CheckTLSSupport():
  """Provide a useful error message if the user's doesn't have TLS 1.2."""
  if re.match('OpenSSL 0\\.', ssl.OPENSSL_VERSION):
    # User's OpenSSL is too old.
    raise serverless_exceptions.NoTLSError(
        'Your Python installation is using the SSL library {}, '
        'which does not support TLS 1.2. TLS 1.2 is required to connect to '
        'Cloud Run on Kubernetes Engine. Please use python with '
        'OpenSSL >1.0'.format(
            ssl.OPENSSL_VERSION))
  # PROTOCOL_TLSv1_2 applies to [2.7.9, 2.7.13) or [3.4, 3.6).
  # PROTOCOL_TLS applies to 2.7.13 and above, or 3.6 and above.
  if not (hasattr(ssl, 'PROTOCOL_TLS') or hasattr(ssl, 'PROTOCOL_TLSv1_2')):
    # User's Python is too old.
    min_required_version = ('2.7.9' if sys.version_info.major == 2 else '3.4')
    raise serverless_exceptions.NoTLSError(
        'Your Python {}.{}.{} installation does not support TLS 1.2, which is'
        ' required to connect to Cloud Run on Kubernetes Engine. '
        'Please upgrade to Python {} or greater.'.format(
            sys.version_info.major,
            sys.version_info.minor,
            sys.version_info.micro,
            min_required_version))


class _GKEConnectionContext(ConnectionInfo):
  """Context manager to connect to the GKE Cloud Run add-in."""

  def __init__(self, cluster_ref, version):
    super(_GKEConnectionContext, self).__init__(version)
    self.cluster_ref = cluster_ref

  @contextlib.contextmanager
  def Connect(self):
    _CheckTLSSupport()
    with gke.ClusterConnectionInfo(self.cluster_ref) as (ip, ca_certs):
      self.ca_certs = ca_certs
      with gke.MonkeypatchAddressChecking('kubernetes.default', ip) as endpoint:
        self.endpoint = 'https://{}/'.format(endpoint)
        with _OverrideEndpointOverrides(self.endpoint):
          yield self

  @property
  def operator(self):
    return 'Cloud Run for Anthos'

  def HttpClient(self):
    # Import http only when needed, as it depends on credential infrastructure
    # which is not needed in all cases.
    assert self.active
    from googlecloudsdk.core.credentials import http as http_creds  # pylint: disable=g-import-not-at-top
    http_client = http_creds.Http(
        response_encoding=http_creds.ENCODING,
        ca_certs=self.ca_certs)
    return http_client

  @property
  def location_label(self):
    return ' of cluster [{{{{bold}}}}{}{{{{reset}}}}]'.format(
        self.cluster_name)

  @property
  def cluster_name(self):
    return self.cluster_ref.Name()

  @property
  def cluster_location(self):
    return self.cluster_ref.zone

  @property
  def supports_one_platform(self):
    return False

  @property
  def ns_label(self):
    return 'namespace'


class _KubeconfigConnectionContext(ConnectionInfo):
  """Context manager to connect to a cluster defined in a Kubeconfig file."""

  def __init__(self, kubeconfig, version, context=None):
    """Initialize connection context based on kubeconfig file.

    Args:
      kubeconfig: googlecloudsdk.api_lib.container.kubeconfig.Kubeconfig object
      version: str, api version to use for making requests
      context: str, current context name
    """
    super(_KubeconfigConnectionContext, self).__init__(version)
    self.kubeconfig = kubeconfig
    self.kubeconfig.SetCurrentContext(context or kubeconfig.current_context)
    self.client_cert_data = None
    self.client_cert = None
    self.client_key = None
    self.client_cert_domain = None

  @contextlib.contextmanager
  def Connect(self):
    _CheckTLSSupport()
    with self._LoadClusterDetails():
      try:
        if self.ca_data:
          with gke.MonkeypatchAddressChecking(
              'kubernetes.default', self.raw_hostname) as endpoint:
            self.endpoint = 'https://{}/'.format(endpoint)
            with _OverrideEndpointOverrides(self.endpoint):
              yield self
        else:
          self.endpoint = 'https://{}/'.format(self.raw_hostname)
          with _OverrideEndpointOverrides(self.endpoint):
            yield self
      except httplib2.HttpLib2Error as e:
        if 'CERTIFICATE_VERIFY_FAILED' in six.text_type(e):
          raise gke.NoCaCertError(
              'Missing or invalid [certificate-authority] or '
              '[certificate-authority-data] field in kubeconfig file.')
        else:
          raise

  def HttpClient(self):
    assert self.active
    if not self.client_key and self.client_cert and self.client_cert_domain:
      raise ValueError(
          'Kubeconfig authentication requires a client certificate '
          'authentication method.')
    if self.client_cert_domain:
      # Import http only when needed, as it depends on credential infrastructure
      # which is not needed in all cases.
      from googlecloudsdk.core import http as http_core  # pylint: disable=g-import-not-at-top
      http_client = http_core.Http(
          response_encoding=http_core.ENCODING,
          ca_certs=self.ca_certs)
      http_client.add_certificate(
          self.client_key, self.client_cert, self.client_cert_domain)
      return http_client
    from googlecloudsdk.core.credentials import http as http_creds  # pylint: disable=g-import-not-at-top
    http_client = http_creds.Http(
        response_encoding=http_creds.ENCODING,
        ca_certs=self.ca_certs)
    return http_client

  @property
  def operator(self):
    return 'Cloud Run for Anthos'

  @property
  def location_label(self):
    return (' of context [{{{{bold}}}}{}{{{{reset}}}}]'
            ' referenced by config file [{{{{bold}}}}{}{{{{reset}}}}]'.format(
                self.curr_ctx['name'],
                self.kubeconfig.filename))

  @property
  def cluster_name(self):
    return self.cluster['name']

  @property
  def cluster_location(self):
    return None

  @property
  def supports_one_platform(self):
    return False

  @property
  def ns_label(self):
    return 'namespace'

  @contextlib.contextmanager
  def _WriteDataIfNoFile(self, f, d):
    if f:
      yield f
    elif d:
      fd, f = tempfile.mkstemp()
      os.close(fd)
      try:
        files.WriteBinaryFileContents(f, base64.b64decode(d), private=True)
        yield f
      finally:
        os.remove(f)
    else:
      yield None

  @contextlib.contextmanager
  def _LoadClusterDetails(self):
    """Get the current cluster and its connection info from the kubeconfig.

    Yields:
      None.
    Raises:
      flags.KubeconfigError: if the config file has missing keys or values.
    """
    try:
      self.curr_ctx = self.kubeconfig.contexts[self.kubeconfig.current_context]
      self.cluster = self.kubeconfig.clusters[
          self.curr_ctx['context']['cluster']]
      self.ca_certs = self.cluster['cluster'].get('certificate-authority', None)
      if not self.ca_certs:
        self.ca_data = self.cluster['cluster'].get(
            'certificate-authority-data', None)

      parsed_server = urlparse.urlparse(self.cluster['cluster']['server'])
      self.raw_hostname = parsed_server.hostname
      self.user = self.kubeconfig.users[self.curr_ctx['context']['user']]
      self.client_key = self.user.get('client-key', None)
      if not self.client_key:
        self.client_key_data = self.user['user'].get('client-key-data', None)
      self.client_cert = self.user['user'].get('client-certificate', None)
      if not self.client_cert:
        self.client_cert_data = self.user['user'].get('client-certificate-data',
                                                      None)
    except KeyError as e:
      raise flags.KubeconfigError('Missing key `{}` in kubeconfig.'.format(
          e.args[0]))
    with self._WriteDataIfNoFile(self.ca_certs, self.ca_data) as ca_certs, \
        self._WriteDataIfNoFile(self.client_key, self.client_key_data) as client_key, \
        self._WriteDataIfNoFile(self.client_cert, self.client_cert_data) as client_cert:
      self.ca_certs = ca_certs
      self.client_key = client_key
      self.client_cert = client_cert
      if self.client_cert:
        # The "domain" we're connecting to is different between PY2 and PY3
        # (TLS address checking is handled differently) so compensate for that
        # here.p
        if six.PY2:
          self.client_cert_domain = 'kubernetes.default'
        else:
          self.client_cert_domain = self.raw_hostname
      yield


def DeriveRegionalEndpoint(endpoint, region):
  scheme, netloc, path, params, query, fragment = urlparse.urlparse(endpoint)
  netloc = '{}-{}'.format(region, netloc)
  return urlparse.urlunparse((scheme, netloc, path, params, query, fragment))


class _RegionalConnectionContext(ConnectionInfo):
  """Context manager to connect a particular Cloud Run region."""

  def __init__(self, region, version):
    super(_RegionalConnectionContext, self).__init__(version)
    self.region = region

  @property
  def ns_label(self):
    return 'project'

  @property
  def operator(self):
    return 'Cloud Run'

  @property
  def location_label(self):
    return ' region [{{{{bold}}}}{}{{{{reset}}}}]'.format(
        self.region)

  @contextlib.contextmanager
  def Connect(self):
    global_endpoint = apis.GetEffectiveApiEndpoint(
        global_methods.SERVERLESS_API_NAME, self._version)
    self.endpoint = DeriveRegionalEndpoint(global_endpoint, self.region)
    with _OverrideEndpointOverrides(self.endpoint):
      yield self

  @property
  def supports_one_platform(self):
    return True


def _GetApiVersion(product,
                   release_track,
                   is_cluster=False,
                   version_override=None):
  """Returns the api version to use depending on the current context."""
  del release_track
  del is_cluster

  if version_override is not None:
    return version_override

  if product == flags.Product.RUN:
    return global_methods.SERVERLESS_API_VERSION
  elif product == flags.Product.EVENTS:
    return _EVENTS_API_VERSION
  else:
    raise ValueError('Unrecognized product: ' + six.u(product))


def GetConnectionContext(args,
                         product=flags.Product.RUN,
                         release_track=base.ReleaseTrack.GA,
                         version_override=None):
  """Gets the regional, kubeconfig, or GKE connection context.

  Args:
    args: Namespace, the args namespace.
    product: Which product is requesting connection context.
    release_track: Release track of the command being run.
    version_override: If specified, the given api version will be used no matter
      the other parameters.

  Raises:
    ArgumentError if region or cluster is not specified.

  Returns:
    A GKE or regional ConnectionInfo object.
  """
  if flags.GetPlatform() == flags.PLATFORM_KUBERNETES:
    kubeconfig = flags.GetKubeconfig(args)
    api_version = _GetApiVersion(
        product,
        release_track,
        is_cluster=True,
        version_override=version_override)
    return _KubeconfigConnectionContext(kubeconfig, api_version, args.context)

  if flags.GetPlatform() == flags.PLATFORM_GKE:
    cluster_ref = args.CONCEPTS.cluster.Parse()
    if not cluster_ref:
      raise flags.ArgumentError(
          'You must specify a cluster in a given location. '
          'Either use the `--cluster` and `--cluster-location` flags '
          'or set the run/cluster and run/cluster_location properties.')
    api_version = _GetApiVersion(
        product,
        release_track,
        is_cluster=True,
        version_override=version_override)
    return _GKEConnectionContext(cluster_ref, api_version)

  if flags.GetPlatform() == flags.PLATFORM_MANAGED:
    region = flags.GetRegion(args, prompt=True)
    if not region:
      raise flags.ArgumentError(
          'You must specify a region. Either use the `--region` flag '
          'or set the run/region property.')
    api_version = _GetApiVersion(
        product, release_track, version_override=version_override)
    return _RegionalConnectionContext(region, api_version)
