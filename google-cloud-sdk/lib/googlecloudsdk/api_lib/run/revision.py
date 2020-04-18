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
"""Wraps a Cloud Run revision message with convenience methods."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import functools
from googlecloudsdk.api_lib.run import k8s_object


# Label names as to be stored in k8s object metadata
AUTHOR_ANNOTATION = 'serving.knative.dev/creator'
SERVICE_LABEL = 'serving.knative.dev/service'
# Used to force a new revision, and also to tie a particular request for changes
# to a particular created revision.
NONCE_LABEL = 'client.knative.dev/nonce'
# Annotation for the user-specified image.
USER_IMAGE_ANNOTATION = k8s_object.CLIENT_GROUP + '/user-image'
CLOUDSQL_ANNOTATION = k8s_object.RUN_GROUP + '/cloudsql-instances'


class Revision(k8s_object.KubernetesObject):
  """Wraps a Cloud Run Revision message, making fields more convenient."""

  API_CATEGORY = 'serving.knative.dev'
  KIND = 'Revision'
  READY_CONDITION = 'Ready'
  _ACTIVE_CONDITION = 'Active'
  TERMINAL_CONDITIONS = {
      READY_CONDITION,
  }

  FIELD_BLACKLIST = ['container']

  @classmethod
  def New(cls, client, namespace):
    """Produces a new Revision object.

    Args:
      client: The Cloud Run API client.
      namespace: str, The serving namespace.

    Returns:
      A new Revision object to be deployed.
    """
    ret = super(Revision, cls).New(client, namespace)
    ret.spec.containers = [client.MESSAGES_MODULE.Container()]
    return ret

  @property
  def env_vars(self):
    """Returns a mutable, dict-like object to manage env vars.

    The returned object can be used like a dictionary, and any modifications to
    the returned object (i.e. setting and deleting keys) modify the underlying
    nested env vars fields.
    """
    if self.container:
      return EnvVarsAsDictionaryWrapper(self.container.env,
                                        self._messages.EnvVar)

  @property
  def author(self):
    return self.annotations.get(AUTHOR_ANNOTATION)

  @property
  def creation_timestamp(self):
    return self._m.metadata.creationTimestamp

  @property
  def gcs_location(self):
    return self._m.status.gcs.location

  @property
  def service_name(self):
    return self.labels[SERVICE_LABEL]

  @property
  def serving_state(self):
    return self.spec.servingState

  @property
  def image(self):
    """URL to container."""
    return self.container.image

  @image.setter
  def image(self, value):
    self.container.image = value

  def UserImage(self, service_user_image=None):
    """Human-readable "what's deployed".

    Sometimes references a client.knative.dev/user-image annotation on the
    revision or service to determine what the user intended to deploy. In that
    case, we can display that, and show the user the hash prefix as a note that
    it's at that specific hash.

    Arguments:
      service_user_image: Optional[str], the contents of the user image annot
        on the service.
    Returns:
      a string representing the user deployment intent.
    """
    if not self.image:
      return None
    if '@' not in self.image:
      return self.image
    user_image = (
        self.annotations.get(USER_IMAGE_ANNOTATION) or service_user_image)
    if not user_image:
      return self.image
    # The image should  be in the format base@sha256:hashhashhash
    base, h = self.image.split('@')
    if ':' in h:
      _, h = h.split(':')
    if not user_image.startswith(base):
      # The user-image is out of date.
      return self.image
    if len(h) > 8:
      h = h[:8] + '...'
    return user_image + ' at ' + h

  @property
  def active(self):
    cond = self.conditions
    if self._ACTIVE_CONDITION in cond:
      return cond[self._ACTIVE_CONDITION]['status']
    return None

  def _EnsureResources(self):
    limits_cls = self._messages.ResourceRequirements.LimitsValue
    if self.container.resources is not None:
      if self.container.resources.limits is None:
        self.container.resources.limits = k8s_object.InitializedInstance(
            limits_cls)
    else:
      self.container.resources = k8s_object.InitializedInstance(
          self._messages.ResourceRequirements)
    # These fields are in the schema due to an error in interperetation of the
    # Knative spec. We're removing them, so never send any contents for them.
    try:
      self.container.resources.limitsInMap = None
      self.container.resources.requestsInMap = None
    except AttributeError:
      # The fields only exist in the v1alpha1 spec, if we're working with a
      # different version, this is safe to ignore
      pass

  def _EnsureMeta(self):
    if self.metadata is None:
      self.metadata = self._messages.ObjectMeta()
    return self.metadata

  @property
  def container(self):
    """The container in the revisionTemplate."""
    if hasattr(self.spec, 'container'):
      if self.spec.container and self.spec.containers:
        raise ValueError(
            'Revision can have only one of `container` or `containers` set')
      elif self.spec.container:
        return self.spec.container
    if self.spec.containers:
      if self.spec.containers[0] is None or len(self.spec.containers) != 1:
        raise ValueError('List of containers must contain exactly one element')
      return self.spec.containers[0]
    else:
      raise ValueError('Either `container` or `containers` must be set')

  @property
  def resource_limits(self):
    """The resource limits as a dictionary { resource name: limit}."""
    self._EnsureResources()
    return k8s_object.ListAsDictionaryWrapper(
        self.container.resources.limits.additionalProperties,
        self._messages.ResourceRequirements.LimitsValue.AdditionalProperty,
        key_field='key',
        value_field='value',
    )

  @property
  def concurrency(self):
    """The concurrency number in the revisionTemplate.

    0: Multiple concurrency, max unspecified.
    1: Single concurrency
    n>1: Allow n simultaneous requests per instance.
    """
    return self.spec.containerConcurrency

  @concurrency.setter
  def concurrency(self, value):
    # Clear the old, deperecated string field
    try:
      self.spec.concurrencyModel = None
    except AttributeError:
      # This field only exists in the v1alpha1 spec, if we're working with a
      # different version, this is safe to ignore
      pass
    self.spec.containerConcurrency = value

  @property
  def timeout(self):
    """The timeout number in the revisionTemplate.

    The lib can accept either a duration format like '1m20s' or integer like
    '80' to set the timeout. The returned object is an integer value, which
    assumes second the unit, e.g., 80.
    """
    return self.spec.timeoutSeconds

  @timeout.setter
  def timeout(self, value):
    self.spec.timeoutSeconds = value

  @property
  def service_account(self):
    """The service account in the revisionTemplate."""
    return self.spec.serviceAccountName

  @service_account.setter
  def service_account(self, value):
    self.spec.serviceAccountName = value

  @property
  def image_digest(self):
    """The URL of the image, by digest. Stable when tags are not."""
    return self.status.imageDigest

  @property
  def volumes(self):
    """Returns a dict-like object to manage volumes.

    There are additional properties on the object (e.g. `.secrets`) that can
    be used to access a mutable, dict-like object for managing volumes of a
    given type. Any modifications to the returned object for these properties
    (i.e. setting and deleting keys) modify the underlying nested volumes.
    """
    return VolumesAsDictionaryWrapper(self.spec.volumes, self._messages.Volume)

  @property
  def volume_mounts(self):
    """Returns a mutable, dict-like object to manage volume mounts.

    The returned object can be used like a dictionary, and any modifications to
    the returned object (i.e. setting and deleting keys) modify the underlying
    nested volume mounts. There are additional properties on the object
    (e.g. `.secrets` that can be used to access a mutable dict-like object for
    a volume mounts that mount volumes of a given type.
    """
    if self.container:
      return VolumeMountsAsDictionaryWrapper(self.volumes,
                                             self.container.volumeMounts,
                                             self._messages.VolumeMount)

  def MountedVolumeJoin(self, subgroup=None):
    vols = self.volumes
    mounts = self.volume_mounts
    if subgroup:
      vols = getattr(vols, subgroup)
      mounts = getattr(mounts, subgroup)
    return {path: vols.get(vol) for path, vol in mounts.items()}


class EnvVarsAsDictionaryWrapper(k8s_object.ListAsReadOnlyDictionaryWrapper):
  """Wraps a list of env vars in a dict-like object.

  Additionally provides properties to access env vars of specific type in a
  mutable dict-like object.
  """

  def __init__(self, env_vars_to_wrap, env_var_class):
    """Wraps a list of env vars in a dict-like object.

    Args:
      env_vars_to_wrap: list[EnvVar], list of env vars to treat as a dict.
      env_var_class: type of the underlying EnvVar objects.
    """
    super(EnvVarsAsDictionaryWrapper, self).__init__(env_vars_to_wrap)
    self._env_vars = env_vars_to_wrap
    self._env_var_class = env_var_class

  @property
  def literals(self):
    """Mutable dict-like object for env vars with a string literal.

    Note that if neither value nor valueFrom is specified, the list entry will
    be treated as a literal empty string.

    Returns:
      A mutable, dict-like object for managing string literal env vars.
    """
    return k8s_object.ListAsDictionaryWrapper(
        self._env_vars,
        self._env_var_class,
        filter_func=lambda env_var: env_var.valueFrom is None)

  @property
  def secrets(self):
    """Mutable dict-like object for vars with a secret source type."""
    def _FilterSecretEnvVars(env_var):
      return (env_var.valueFrom is not None and
              env_var.valueFrom.secretKeyRef is not None)

    return k8s_object.ListAsDictionaryWrapper(
        self._env_vars,
        self._env_var_class,
        value_field='valueFrom',
        filter_func=_FilterSecretEnvVars)

  @property
  def config_maps(self):
    """Mutable dict-like object for vars with a config map source type."""
    def _FilterConfigMapEnvVars(env_var):
      return (env_var.valueFrom is not None and
              env_var.valueFrom.configMapKeyRef is not None)

    return k8s_object.ListAsDictionaryWrapper(
        self._env_vars,
        self._env_var_class,
        value_field='valueFrom',
        filter_func=_FilterConfigMapEnvVars)


class VolumesAsDictionaryWrapper(k8s_object.ListAsReadOnlyDictionaryWrapper):
  """Wraps a list of volumes in a dict-like object.

  Additionally provides properties to access volumes of specific type in a
  mutable dict-like object.
  """

  def __init__(self, volumes_to_wrap, volume_class):
    """Wraps a list of volumes in a dict-like object.

    Args:
      volumes_to_wrap: list[Volume], list of volumes to treat as a dict.
      volume_class: type of the underlying Volume objects.
    """
    super(VolumesAsDictionaryWrapper, self).__init__(volumes_to_wrap)
    self._volumes = volumes_to_wrap
    self._volume_class = volume_class

  @property
  def secrets(self):
    """Mutable dict-like object for volumes with a secret source type."""
    return k8s_object.ListAsDictionaryWrapper(
        self._volumes,
        self._volume_class,
        value_field='secret',
        filter_func=lambda volume: volume.secret is not None)

  @property
  def config_maps(self):
    """Mutable dict-like object for volumes with a config map source type."""
    return k8s_object.ListAsDictionaryWrapper(
        self._volumes,
        self._volume_class,
        value_field='configMap',
        filter_func=lambda volume: volume.configMap is not None)


class VolumeMountsAsDictionaryWrapper(k8s_object.ListAsDictionaryWrapper):
  """Wraps a list of volume mounts in a mutable dict-like object.

  Additionally provides properties to access mounts that are mounting volumes
  of specific type in a mutable dict-like object.
  """

  def __init__(self, volumes, mounts_to_wrap, mount_class):
    """Wraps a list of volume mounts in a mutable dict-like object.

    Forces readOnly=True on creation of new volume mounts.

    Args:
      volumes: associated VolumesAsDictionaryWrapper obj
      mounts_to_wrap: list[VolumeMount], list of mounts to treat as a dict.
      mount_class: type of the underlying VolumeMount objects.
    """
    super(VolumeMountsAsDictionaryWrapper, self).__init__(
        mounts_to_wrap,
        functools.partial(mount_class, readOnly=True),
        key_field='mountPath',
        value_field='name')
    self._volumes = volumes

  @property
  def secrets(self):
    """Mutable dict-like object for mounts whose volumes have a secret source type."""
    return k8s_object.ListAsDictionaryWrapper(
        self._m,
        self._item_class,
        key_field=self._key_field,
        value_field=self._value_field,
        filter_func=lambda mount: mount.name in self._volumes.secrets)

  @property
  def config_maps(self):
    """Mutable dict-like object for mounts whose volumes have a config map source type."""
    return k8s_object.ListAsDictionaryWrapper(
        self._m,
        self._item_class,
        key_field=self._key_field,
        value_field=self._value_field,
        filter_func=lambda mount: mount.name in self._volumes.config_maps)
