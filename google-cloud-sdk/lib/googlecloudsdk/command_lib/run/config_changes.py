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
"""Class for representing various changes to a Configuration."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import abc
import copy

from googlecloudsdk.api_lib.run import k8s_object
from googlecloudsdk.api_lib.run import revision
from googlecloudsdk.api_lib.run import service
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import name_generator
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.util.args import repeated

import six


class ConfigChanger(six.with_metaclass(abc.ABCMeta, object)):
  """An abstract class representing configuration changes."""

  @abc.abstractmethod
  def Adjust(self, resource):
    """Adjust the given Service configuration.

    Args:
      resource: the k8s_object to adjust.

    Returns:
      A k8s_object that reflects applying the requested update.
      May be resource after a mutation or a different object.
    """
    return resource


class LabelChanges(ConfigChanger):
  """Represents the user intent to modify metadata labels."""

  def __init__(self, diff):
    self._diff = diff

  def Adjust(self, resource):
    # Currently assumes all "system"-owned labels are applied by the control
    # plane and it's ok for us to clear them on the client.
    update_result = self._diff.Apply(
        k8s_object.Meta(resource.MessagesModule()).LabelsValue,
        resource.metadata.labels)
    maybe_new_labels = update_result.GetOrNone()
    if maybe_new_labels:
      resource.metadata.labels = maybe_new_labels
      # Service labels are the source of truth and *overwrite* revision labels.
      # See run-labels-prd for deets.
      # However, we need to preserve the nonce if there is one.
      nonce = resource.template.labels.get(revision.NONCE_LABEL)
      resource.template.metadata.labels = copy.deepcopy(maybe_new_labels)
      if nonce:
        resource.template.labels[revision.NONCE_LABEL] = nonce
    return resource


class ReplaceServiceChange(ConfigChanger):
  """Represents the user intent to replace the service."""

  def __init__(self, new_service):
    self._service = new_service

  def Adjust(self, resource):
    """Returns a replacement for resource.

    The returned service is the service provided to the constructor. If
    resource.metadata.resourceVersion is not empty to None returned service
    has metadata.resourceVersion set to this value.

    Args:
      resource: service.Service, The service to adjust.
    """
    if resource.metadata.resourceVersion:
      self._service.metadata.resourceVersion = resource.metadata.resourceVersion
      # Knative will complain if you try to edit (incl remove) serving annots.
      # So replicate them here.
      for k, v in resource.annotations.items():
        if k.startswith(k8s_object.SERVING_GROUP):
          self._service.annotations[k] = v
    return self._service


class EndpointVisibilityChange(LabelChanges):
  """Represents the user intent to modify the endpoint visibility."""

  def __init__(self, endpoint_visibility):
    """Determine label changes for modifying endpoint visibility.

    Args:
      endpoint_visibility: bool, True if Cloud Run on GKE service should only be
        addressable from within the cluster. False if it should be publicly
        addressable.
    """
    if endpoint_visibility:
      diff = labels_util.Diff(
          additions={service.ENDPOINT_VISIBILITY: service.CLUSTER_LOCAL})
    else:
      diff = labels_util.Diff(subtractions=[service.ENDPOINT_VISIBILITY])
    super(EndpointVisibilityChange, self).__init__(diff)


class SetTemplateAnnotationChange(ConfigChanger):
  """Represents the user intent to set a template annotation."""

  def __init__(self, key, value):
    self._key = key
    self._value = value

  def Adjust(self, resource):
    annotations = k8s_object.AnnotationsFromMetadata(
        resource.MessagesModule(), resource.template.metadata)
    annotations[self._key] = self._value
    return resource


class DeleteTemplateAnnotationChange(ConfigChanger):
  """Represents the user intent to delete a template annotation."""

  def __init__(self, key):
    self._key = key

  def Adjust(self, resource):
    annotations = k8s_object.AnnotationsFromMetadata(
        resource.MessagesModule(), resource.template.metadata)
    if self._key in annotations:
      del annotations[self._key]
    return resource


class VpcConnectorChange(ConfigChanger):
  """Sets a VPC connector annotation on the service."""

  def __init__(self, connector_name):
    self._connector_name = connector_name

  def Adjust(self, resource):
    annotations = k8s_object.AnnotationsFromMetadata(resource.MessagesModule(),
                                                     resource.template.metadata)
    annotations['run.googleapis.com/vpc-access-connector'] = (
        self._connector_name)
    return resource


class ClearVpcConnectorChange(ConfigChanger):
  """Clears a VPC connector annotation on the service."""

  def Adjust(self, resource):
    annotations = k8s_object.AnnotationsFromMetadata(resource.MessagesModule(),
                                                     resource.template.metadata)
    if 'run.googleapis.com/vpc-access-connector' in annotations:
      del annotations['run.googleapis.com/vpc-access-connector']
    return resource


class ImageChange(ConfigChanger):
  """A Cloud Run container deployment."""

  deployment_type = 'container'

  def __init__(self, image):
    self.image = image

  def Adjust(self, resource):
    resource.annotations[revision.USER_IMAGE_ANNOTATION] = (
        self.image)
    resource.template.annotations[revision.USER_IMAGE_ANNOTATION] = (
        self.image)
    resource.template.image = self.image
    return resource


class EnvVarLiteralChanges(ConfigChanger):
  """Represents the user intent to modify environment variables string literals."""

  def __init__(self, env_vars_to_update=None,
               env_vars_to_remove=None, clear_others=False):
    """Initialize a new EnvVarLiteralChanges object.

    Args:
      env_vars_to_update: {str, str}, Update env var names and values.
      env_vars_to_remove: [str], List of env vars to remove.
      clear_others: bool, If true, clear all non-updated env vars.
    """
    self._to_update = None
    self._to_remove = None
    self._clear_others = clear_others
    if env_vars_to_update:
      self._to_update = {k.strip(): v for k, v in env_vars_to_update.items()}
    if env_vars_to_remove:
      self._to_remove = [k.lstrip() for k in env_vars_to_remove]

  def Adjust(self, resource):
    """Mutates the given config's env vars to match the desired changes.

    Args:
      resource: k8s_object to adjust

    Returns:
      The adjusted resource

    Raises:
      ConfigurationError if there's an attempt to replace the source of an
        existing environment variable whose source is of a different type
        (e.g. env var's secret source can't be replaced with a config map
        source).
    """
    if self._clear_others:
      resource.template.env_vars.literals.clear()
    elif self._to_remove:
      for env_var in self._to_remove:
        if env_var in resource.template.env_vars.literals:
          del resource.template.env_vars.literals[env_var]

    if self._to_update:
      try:
        resource.template.env_vars.literals.update(self._to_update)
      except KeyError as e:
        raise exceptions.ConfigurationError(
            'Cannot update environment variable [{}] to string literal '
            'because it has already been set with a different type.'.format(
                e.args[0]))
    return resource


class EnvVarSourceChanges(ConfigChanger):
  """Represents the user intent to modify environment variables sources."""

  def __init__(self, env_vars_to_update=None,
               env_vars_to_remove=None, clear_others=False):
    """Initialize a new EnvVarSourceChanges object.

    Args:
      env_vars_to_update: {str, str}, Update env var names and values.
      env_vars_to_remove: [str], List of env vars to remove.
      clear_others: bool, If true, clear all non-updated env vars.

    Raises:
      ConfigurationError if a key hasn't been provided for a source.
    """
    self._to_update = None
    self._to_remove = None
    self._clear_others = clear_others
    if env_vars_to_update:
      self._to_update = {}
      for k, v in env_vars_to_update.items():
        name = k.strip()
        # Split the given values into 2 parts:
        #    [env var source name, source data item key]
        value = v.split(':', 1)
        if len(value) < 2:
          raise exceptions.ConfigurationError(
              'Missing required item key for environment variable [{}].'
              .format(name))
        self._to_update[name] = value
    if env_vars_to_remove:
      self._to_remove = [k.lstrip() for k in env_vars_to_remove]

  @abc.abstractmethod
  def _MakeEnvVarSource(self, messages, name, key):
    """Returns an instance of an EnvVarSource."""

  @abc.abstractmethod
  def _GetEnvVars(self, resource):
    """Returns a k8s_object.ListAsDictionaryWrapper to manage env vars with a source."""

  def Adjust(self, resource):
    """Mutates the given config's env vars to match the desired changes.

    Args:
      resource: k8s_object to adjust

    Returns:
      The adjusted resource

    Raises:
      ConfigurationError if there's an attempt to replace the source of an
        existing environment variable whose source is of a different type
        (e.g. env var's secret source can't be replaced with a config map
        source).
    """
    env_vars = self._GetEnvVars(resource)

    if self._clear_others:
      env_vars.clear()
    elif self._to_remove:
      for env_var in self._to_remove:
        if env_var in env_vars:
          del env_vars[env_var]

    if self._to_update:
      for name, (source_name, source_key) in self._to_update.items():
        try:
          env_vars[name] = self._MakeEnvVarSource(
              resource.MessagesModule(), source_name, source_key)
        except KeyError:
          raise exceptions.ConfigurationError(
              'Cannot update environment variable [{}] to the given type '
              'because it has already been set with a different type.'.format(
                  name))
    return resource


class SecretEnvVarChanges(EnvVarSourceChanges):
  """Represents the user intent to modify environment variable secrets."""

  def _MakeEnvVarSource(self, messages, name, key):
    return messages.EnvVarSource(
        secretKeyRef=messages.SecretKeySelector(
            name=name,
            key=key))

  def _GetEnvVars(self, resource):
    return resource.template.env_vars.secrets


class ConfigMapEnvVarChanges(EnvVarSourceChanges):
  """Represents the user intent to modify environment variable config maps."""

  def _MakeEnvVarSource(self, messages, name, key):
    return messages.EnvVarSource(
        configMapKeyRef=messages.ConfigMapKeySelector(
            name=name,
            key=key))

  def _GetEnvVars(self, resource):
    return resource.template.env_vars.config_maps


class ResourceChanges(ConfigChanger):
  """Represents the user intent to update resource limits."""

  def __init__(self, memory=None, cpu=None):
    self._memory = memory
    self._cpu = cpu

  def Adjust(self, resource):
    """Mutates the given config's resource limits to match what's desired."""
    if self._memory is not None:
      resource.template.resource_limits['memory'] = self._memory
    if self._cpu is not None:
      resource.template.resource_limits['cpu'] = self._cpu
    return resource


class CloudSQLChanges(ConfigChanger):
  """Represents the intent to update the Cloug SQL instances."""

  def __init__(self, project, region, args):
    """Initializes the intent to update the Cloud SQL instances.

    Args:
      project: Project to use as the default project for Cloud SQL instances.
      region: Region to use as the default region for Cloud SQL instances
      args: Args to the command.
    """
    self._project = project
    self._region = region
    self._args = args

  # Here we are a proxy through to the actual args to set some extra augmented
  # information on each one, so each cloudsql instance gets the region and
  # project.
  @property
  def add_cloudsql_instances(self):
    return self._AugmentArgs('add_cloudsql_instances')

  @property
  def remove_cloudsql_instances(self):
    return self._AugmentArgs('remove_cloudsql_instances')

  @property
  def set_cloudsql_instances(self):
    return self._AugmentArgs('set_cloudsql_instances')

  @property
  def clear_cloudsql_instances(self):
    return getattr(self._args, 'clear_cloudsql_instances', None)

  def _AugmentArgs(self, arg_name):
    val = getattr(self._args, arg_name, None)
    if val is None:
      return None
    return [self._Augment(i) for i in val]

  def Adjust(self, resource):
    def GetCurrentInstances():
      annotation_val = resource.template.annotations.get(
          revision.CLOUDSQL_ANNOTATION)
      if annotation_val:
        return annotation_val.split(',')
      return []

    instances = repeated.ParsePrimitiveArgs(
        self, 'cloudsql-instances', GetCurrentInstances)
    if instances is not None:
      resource.template.annotations[
          revision.CLOUDSQL_ANNOTATION] = ','.join(instances)
    return resource

  def _Augment(self, instance_str):
    instance = instance_str.split(':')
    if len(instance) == 3:
      ret = tuple(instance)
    elif len(instance) == 1:
      if not self._project:
        raise exceptions.CloudSQLError(
            'To specify a Cloud SQL instance by plain name, you must specify a '
            'project.')
      if not self._region:
        raise exceptions.CloudSQLError(
            'To specify a Cloud SQL instance by plain name, you must be '
            'deploying to a managed Cloud Run region.')
      ret = self._project, self._region, instance[0]
    else:
      raise exceptions.CloudSQLError(
          'Malformed CloudSQL instance string: {}'.format(
              instance_str))
    return ':'.join(ret)


class ConcurrencyChanges(ConfigChanger):
  """Represents the user intent to update concurrency preference."""

  def __init__(self, concurrency):
    self._concurrency = None if concurrency == 'default' else int(concurrency)

  def Adjust(self, resource):
    """Mutates the given config's resource limits to match what's desired."""
    resource.template.concurrency = self._concurrency
    return resource


class TimeoutChanges(ConfigChanger):
  """Represents the user intent to update request duration."""

  def __init__(self, timeout):
    self._timeout = timeout

  def Adjust(self, resource):
    """Mutates the given config's timeout to match what's desired."""
    resource.template.timeout = self._timeout
    return resource


class ServiceAccountChanges(ConfigChanger):
  """Represents the user intent to change service account for the revision."""

  def __init__(self, service_account):
    self._service_account = service_account

  def Adjust(self, resource):
    """Mutates the given config's service account to match what's desired."""
    resource.template.service_account = self._service_account
    return resource


class RevisionNameChanges(ConfigChanger):
  """Represents the user intent to change revision name."""

  def __init__(self, revision_suffix):
    self._revision_suffix = revision_suffix

  def Adjust(self, resource):
    """Mutates the given config's revision name to match what's desired."""
    resource.template.name = '{}-{}'.format(resource.name,
                                            self._revision_suffix)
    return resource


def _GenerateVolumeName(prefix):
  """Randomly generated name with the given prefix."""
  return name_generator.GenerateName(sections=3, separator='-', prefix=prefix)


class VolumeChanges(ConfigChanger):
  """Represents the user intent to modify volumes and mounts."""

  def __init__(self,
               mounts_to_update=None,
               mounts_to_remove=None,
               clear_others=False):
    """Initialize a new VolumeChanges object.

    Args:
      mounts_to_update: {str, str}, Update mount path and volume fields.
      mounts_to_remove: [str], List of mount paths to remove.
      clear_others: bool, If true, clear all non-updated volumes and mounts of
        the given [volume_type].
    """
    self._to_update = None
    self._to_remove = None
    self._clear_others = clear_others
    if mounts_to_update:
      self._to_update = {}
      for k, v in mounts_to_update.items():
        # Split the given values into 2 parts:
        #    [volume source name, data item key]
        update_value = v.split(':', 1)
        # Pad with None if no data item key specified
        if len(update_value) < 2:
          update_value.append(None)
        self._to_update[k.strip()] = update_value
    if mounts_to_remove:
      self._to_remove = [k.lstrip() for k in mounts_to_remove]

  @abc.abstractmethod
  def _MakeVolumeSource(self, messages, name, key=None):
    """Returns an instance of a volume source."""

  @abc.abstractmethod
  def _GetVolumes(self, resource):
    """Returns a k8s_object.ListAsDictionaryWrapper to manage volumes."""

  @abc.abstractmethod
  def _GetVolumeMounts(self, resource):
    """Returns a k8s_object.ListAsDictionaryWrapper to manage volume mounts."""

  def Adjust(self, resource):
    """Mutates the given config's volumes to match the desired changes.

    Args:
      resource: k8s_object to adjust

    Returns:
      The adjusted resource

    Raises:
      ConfigurationError if there's an attempt to replace the volume a mount
        points to whose existing volume has a source of a different type than
        the new volume (e.g. mount that points to a volume with a secret source
        can't be replaced with a volume that has a config map source).
    """
    volume_mounts = self._GetVolumeMounts(resource)
    volumes = self._GetVolumes(resource)

    if self._clear_others:
      volume_mounts.clear()
    elif self._to_remove:
      for path in self._to_remove:
        if path in volume_mounts:
          del volume_mounts[path]

    if self._to_update:
      for path, (source_name, source_key) in self._to_update.items():
        # Generate unique volume name so that volume source configurations
        # can be unique (e.g. different items) even if the source name matches
        volume_name = None
        while volume_name is None or volume_name in resource.template.volumes:
          volume_name = _GenerateVolumeName(source_name)

        # Set the mount and volume
        try:
          volume_mounts[path] = volume_name
        except KeyError:
          raise exceptions.ConfigurationError(
              'Cannot update mount [{}] because its mounted volume '
              'is of a different source type.'.format(path))
        volumes[volume_name] = self._MakeVolumeSource(
            resource.MessagesModule(), source_name, source_key)

    # Delete all volumes no longer being mounted
    for volume in list(volumes):
      if volume not in volume_mounts.values():
        del volumes[volume]

    return resource


class SecretVolumeChanges(VolumeChanges):
  """Represents the user intent to change volumes with secret source types."""

  def _MakeVolumeSource(self, messages, name, key=None):
    source = messages.SecretVolumeSource(secretName=name)
    if key is not None:
      source.items.append(messages.KeyToPath(key=key, path=key))
    return source

  def _GetVolumes(self, resource):
    return resource.template.volumes.secrets

  def _GetVolumeMounts(self, resource):
    return resource.template.volume_mounts.secrets


class ConfigMapVolumeChanges(VolumeChanges):
  """Represents the user intent to change volumes with config map source types."""

  def _MakeVolumeSource(self, messages, name, key=None):
    source = messages.ConfigMapVolumeSource(name=name)
    if key is not None:
      source.items.append(messages.KeyToPath(key=key, path=key))
    return source

  def _GetVolumes(self, resource):
    return resource.template.volumes.config_maps

  def _GetVolumeMounts(self, resource):
    return resource.template.volume_mounts.config_maps


class NoTrafficChange(ConfigChanger):
  """Represents the user intent to block traffic for a new revision."""

  def Adjust(self, resource):
    """Removes LATEST from the services traffic assignments."""
    if resource.configuration:
      raise exceptions.UnsupportedOperationError(
          'This service is using an old version of Cloud Run for Anthos '
          'that does not support traffic features. Please upgrade to 0.8 '
          'or later.')

    if not resource.generation:
      raise exceptions.ConfigurationError(
          '--no-traffic not supported when creating a new service.')

    resource.spec_traffic.ZeroLatestTraffic(
        resource.status.latestReadyRevisionName)
    return resource


class TrafficChanges(ConfigChanger):
  """Represents the user intent to change a service's traffic assignments."""

  def __init__(self, new_percentages, tags_to_update=None, tags_to_remove=None,
               clear_other_tags=False):
    self._new_percentages = new_percentages
    self._tags_to_update = tags_to_update or {}
    self._tags_to_remove = tags_to_remove or []
    self._clear_other_tags = clear_other_tags

  def Adjust(self, resource):
    """Mutates the given service's traffic assignments."""
    if self._tags_to_update or self._tags_to_remove or self._clear_other_tags:
      resource.spec_traffic.UpdateTags(self._tags_to_update,
                                       self._tags_to_remove,
                                       self._clear_other_tags)
    if self._new_percentages:
      resource.spec_traffic.UpdateTraffic(self._new_percentages)
    return resource


class ContainerCommandChange(ConfigChanger):
  """Represents the user intent to change the 'command' for the container."""

  def __init__(self, command):
    self._commands = command

  def Adjust(self, resource):
    resource.template.container.command = self._commands
    return resource


class ContainerArgsChange(ConfigChanger):
  """Represents the user intent to change the 'args' for the container."""

  def __init__(self, args):
    self._args = args

  def Adjust(self, resource):
    resource.template.container.args = self._args
    return resource


_HTTP2_NAME = 'h2c'
_DEFAULT_PORT = 8080


class ContainerPortChange(ConfigChanger):
  """Represents the user intent to change the port name and/or number."""

  def __init__(self, port=None, use_http2=None):
    """Initialize a ContainerPortChange.

    Args:
      port: str, the port number to set the port to, "default" to unset the
        containerPort field, or None to not modify the port number.
      use_http2: bool, True to set the port name for http/2, False to unset it,
        or None to not modify the port name.
    """
    self._port = port
    self._http2 = use_http2

  def Adjust(self, resource):
    """Modify an existing ContainerPort or create a new one."""
    port_msg = (
        resource.template.container.ports[0]
        if resource.template.container.ports else
        resource.MessagesModule().ContainerPort())
    # Set port to given value or clear field
    if self._port == 'default':
      port_msg.reset('containerPort')
    elif self._port is not None:
      port_msg.containerPort = int(self._port)
    # Set name for http/2 or clear field
    if self._http2:
      port_msg.name = _HTTP2_NAME
    elif self._http2 is not None:
      port_msg.reset('name')
    # A port number must be specified
    if port_msg.name and not port_msg.containerPort:
      port_msg.containerPort = _DEFAULT_PORT

    # Use the ContainerPort iff it's not empty
    if port_msg.containerPort:
      resource.template.container.ports = [port_msg]
    else:
      resource.template.container.reset('ports')
    return resource
