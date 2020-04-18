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

"""Shared resource flags for Cloud Run commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import abc
import os
import re

from googlecloudsdk.api_lib.run import global_methods
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io


class PromptFallthrough(deps.Fallthrough):
  """Fall through to reading from an interactive prompt."""

  def __init__(self, hint):
    super(PromptFallthrough, self).__init__(function=None, hint=hint)

  @abc.abstractmethod
  def _Prompt(self, parsed_args):
    pass

  def _Call(self, parsed_args):
    if not console_io.CanPrompt():
      return None
    return self._Prompt(parsed_args)


def GenerateServiceName(image):
  """Produce a valid default service name.

  Converts a file path or image path into a reasonable default service name by
  stripping file path delimeters, image tags, and image hashes.
  For example, the image name 'gcr.io/myproject/myimage:latest' would produce
  the service name 'myimage'.

  Args:
    image: str, The container path.

  Returns:
    A valid Cloud Run service name.
  """
  base_name = os.path.basename(image.rstrip(os.sep))
  base_name = base_name.split(':')[0]  # Discard image tag if present.
  base_name = base_name.split('@')[0]  # Disacard image hash if present.
  # Remove non-supported special characters.
  return re.sub(r'[^a-zA-Z0-9-]', '', base_name).strip('-').lower()


class ServicePromptFallthrough(PromptFallthrough):
  """Fall through to reading the service name from an interactive prompt."""

  def __init__(self):
    super(ServicePromptFallthrough, self).__init__(
        'specify the service name from an interactive prompt')

  def _Prompt(self, parsed_args):
    image = None
    if hasattr(parsed_args, 'image'):
      image = parsed_args.image
    message = 'Service name'
    if image:
      default_name = GenerateServiceName(image)
      service_name = console_io.PromptWithDefault(
          message=message, default=default_name)
    else:
      service_name = console_io.PromptResponse(message='{}: '.format(message))
    return service_name


class DefaultFallthrough(deps.Fallthrough):
  """Use the namespace "default".

  For Knative only.

  For Cloud Run, raises an ArgumentError if project not set.
  """

  def __init__(self):
    super(DefaultFallthrough, self).__init__(
        function=None,
        hint='For Cloud Run on Kubernetes Engine, defaults to "default". '
        'Otherwise, defaults to project ID.')

  def _Call(self, parsed_args):
    if (flags.GetPlatform() == flags.PLATFORM_GKE or
        flags.GetPlatform() == flags.PLATFORM_KUBERNETES):
      return 'default'
    elif not (getattr(parsed_args, 'project', None) or
              properties.VALUES.core.project.Get()):
      # HACK: Compensate for how "namespace" is actually "project" in Cloud Run
      # by providing an error message explicitly early here.
      raise flags.ArgumentError(
          'The [project] resource is not properly specified. '
          'Please specify the argument [--project] on the command line or '
          'set the property [core/project].')
    return None


def NamespaceAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='namespace',
      help_text='Specific to Cloud Run for Anthos: '
      'Kubernetes namespace for the {resource}.',
      fallthroughs=[
          deps.PropertyFallthrough(properties.VALUES.run.namespace),
          DefaultFallthrough(),
          deps.ArgFallthrough('project'),
          deps.PropertyFallthrough(properties.VALUES.core.project),
      ])


def ServiceAttributeConfig(prompt=False):
  """Attribute config with fallthrough prompt only if requested."""
  if prompt:
    fallthroughs = [ServicePromptFallthrough()]
  else:
    fallthroughs = []
  return concepts.ResourceParameterAttributeConfig(
      name='service',
      help_text='Service for the {resource}.',
      fallthroughs=fallthroughs)


def ConfigurationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='configuration',
      help_text='Configuration for the {resource}.')


def RouteAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='route',
      help_text='Route for the {resource}.')


def RevisionAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='revision',
      help_text='Revision for the {resource}.')


def DomainAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='domain',
      help_text='Name of the domain to be mapped to.')


class ClusterPromptFallthrough(PromptFallthrough):
  """Fall through to reading the cluster name from an interactive prompt."""

  def __init__(self):
    super(ClusterPromptFallthrough, self).__init__(
        'specify the cluster from a list of available clusters')

  def _Prompt(self, parsed_args):
    """Fallthrough to reading the cluster name from an interactive prompt.

    Only prompt for cluster name if the user-specified platform is GKE.

    Args:
      parsed_args: Namespace, the args namespace.

    Returns:
      A cluster name string
    """
    if flags.GetPlatform() == flags.PLATFORM_GKE:
      cluster_location = (
          getattr(parsed_args, 'cluster_location', None) or
          properties.VALUES.run.cluster_location.Get())
      cluster_location_msg = ' in [{}]'.format(
          cluster_location) if cluster_location else ''

      clusters = global_methods.ListClusters(cluster_location)
      if not clusters:
        raise exceptions.ConfigurationError(
            'No compatible clusters found{}. '
            'Ensure your cluster has Cloud Run enabled.'.format(
                cluster_location_msg))

      def _GetClusterDescription(cluster):
        """Description of cluster for prompt."""
        if cluster_location:
          return cluster.name
        return '{} in {}'.format(cluster.name, cluster.zone)

      cluster_descs = [_GetClusterDescription(c) for c in clusters]

      idx = console_io.PromptChoice(
          cluster_descs,
          message='GKE cluster{}:'.format(cluster_location_msg),
          cancel_option=True)
      cluster = clusters[idx]

      if cluster_location:
        cluster_result = cluster.name
        location_help_text = ''
      else:
        cluster_ref = flags.GetClusterRef(cluster)
        cluster_result = cluster_ref.SelfLink()
        location_help_text = (
            ' && gcloud config set run/cluster_location {}'.format(
                cluster.zone))
      log.status.Print(
          'To make this the default cluster, run '
          '`gcloud config set run/cluster {cluster}'
          '{location}`.\n'.format(
              cluster=cluster.name,
              location=location_help_text))
      return cluster_result


def ClusterAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='cluster',
      help_text='Name of the Kubernetes Engine cluster to use. '
      'Alternatively, set the property [run/cluster].',
      fallthroughs=[
          deps.PropertyFallthrough(properties.VALUES.run.cluster),
          ClusterPromptFallthrough()
      ])


class ClusterLocationPromptFallthrough(PromptFallthrough):
  """Fall through to reading the cluster name from an interactive prompt."""

  def __init__(self):
    super(ClusterLocationPromptFallthrough, self).__init__(
        'specify the cluster location from a list of available zones')

  def _Prompt(self, parsed_args):
    """Fallthrough to reading the cluster location from an interactive prompt.

    Only prompt for cluster location if the user-specified platform is GKE
    and if cluster name is already defined.

    Args:
      parsed_args: Namespace, the args namespace.

    Returns:
      A cluster location string
    """
    cluster_name = (
        getattr(parsed_args, 'cluster', None) or
        properties.VALUES.run.cluster.Get())
    if flags.GetPlatform() == flags.PLATFORM_GKE and cluster_name:
      clusters = [
          c for c in global_methods.ListClusters() if c.name == cluster_name
      ]
      if not clusters:
        raise exceptions.ConfigurationError(
            'No cluster locations found for cluster [{}]. '
            'Ensure your clusters have Cloud Run enabled.'
            .format(cluster_name))
      cluster_locations = [c.zone for c in clusters]
      idx = console_io.PromptChoice(
          cluster_locations,
          message='GKE cluster location for [{}]:'.format(
              cluster_name),
          cancel_option=True)
      location = cluster_locations[idx]
      log.status.Print(
          'To make this the default cluster location, run '
          '`gcloud config set run/cluster_location {}`.\n'.format(location))
      return location


def ClusterLocationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='location',
      help_text='Zone in which the {resource} is located. '
      'Alternatively, set the property [run/cluster_location].',
      fallthroughs=[
          deps.PropertyFallthrough(properties.VALUES.run.cluster_location),
          ClusterLocationPromptFallthrough()
      ])


def GetClusterResourceSpec():
  return concepts.ResourceSpec(
      'container.projects.zones.clusters',
      projectId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      zone=ClusterLocationAttributeConfig(),
      clusterId=ClusterAttributeConfig(),
      resource_name='cluster')


def GetServiceResourceSpec(prompt=False):
  return concepts.ResourceSpec(
      'run.namespaces.services',
      namespacesId=NamespaceAttributeConfig(),
      servicesId=ServiceAttributeConfig(prompt),
      resource_name='service')


def GetConfigurationResourceSpec():
  return concepts.ResourceSpec(
      'run.namespaces.configurations',
      namespacesId=NamespaceAttributeConfig(),
      configurationsId=ConfigurationAttributeConfig(),
      resource_name='configuration')


def GetRouteResourceSpec():
  return concepts.ResourceSpec(
      'run.namespaces.routes',
      namespacesId=NamespaceAttributeConfig(),
      routesId=RouteAttributeConfig(),
      resource_name='route')


def GetRevisionResourceSpec():
  return concepts.ResourceSpec(
      'run.namespaces.revisions',
      namespacesId=NamespaceAttributeConfig(),
      revisionsId=RevisionAttributeConfig(),
      resource_name='revision')


def GetDomainMappingResourceSpec():
  return concepts.ResourceSpec(
      'run.namespaces.domainmappings',
      namespacesId=NamespaceAttributeConfig(),
      domainmappingsId=DomainAttributeConfig(),
      resource_name='DomainMapping')


def GetNamespaceResourceSpec():
  """Returns a resource spec for the namespace."""
  # TODO(b/150322097): Remove this when the api has been split.
  # This try/except block is needed because the v1alpha1 and v1 run apis
  # have different collection names for the namespaces.
  try:
    return concepts.ResourceSpec(
        'run.namespaces',
        namespacesId=NamespaceAttributeConfig(),
        resource_name='namespace')
  except resources.InvalidCollectionException:
    return concepts.ResourceSpec(
        'run.api.v1.namespaces',
        namespacesId=NamespaceAttributeConfig(),
        resource_name='namespace')


CLUSTER_PRESENTATION = presentation_specs.ResourcePresentationSpec(
    '--cluster',
    GetClusterResourceSpec(),
    'Kubernetes Engine cluster to connect to.',
    required=False,
    prefixes=True)
