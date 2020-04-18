# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Command util functions for gcloud container commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container import api_adapter
from googlecloudsdk.api_lib.container import util
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import text


class Error(exceptions.Error):
  """Class for errors raised by container commands."""


class NodePoolError(Error):
  """Error when a node pool name doesn't match a node pool in the cluster."""


def _NodePoolFromCluster(cluster, node_pool_name):
  """Helper function to get node pool from a cluster, given its name."""
  for node_pool in cluster.nodePools:
    if node_pool.name == node_pool_name:
      # Node pools always have unique names.
      return node_pool
  raise NodePoolError(
      'No node pool found matching the name [{}].'.format(node_pool_name))


def _MasterUpgradeMessage(name, server_conf, cluster, new_version):
  """Returns the prompt message during a master upgrade.

  Args:
    name: str, the name of the cluster being upgraded.
    server_conf: the server config object.
    cluster: the cluster object.
    new_version: str, the name of the new version, if given.

  Raises:
    NodePoolError: if the node pool name can't be found in the cluster.

  Returns:
    str, a message about which nodes in the cluster will be upgraded and
        to which version.
  """
  if cluster:
    version_message = 'version [{}]'.format(cluster.currentMasterVersion)
  else:
    version_message = 'its current version'

  if not new_version and server_conf:
    new_version = server_conf.defaultClusterVersion

  if new_version:
    new_version_message = 'version [{}]'.format(new_version)
  else:
    new_version_message = 'the default cluster version'

  return ('Master of cluster [{}] will be upgraded from {} to {}.'.format(
      name, version_message, new_version_message))


def _NodeUpgradeMessage(name, cluster, node_pool_name, new_version,
                        concurrent_node_count):
  """Returns the prompt message during a node upgrade.

  Args:
    name: str, the name of the cluster being upgraded.
    cluster: the cluster object.
    node_pool_name: str, the name of the node pool if the upgrade is for a
      specific node pool.
    new_version: str, the name of the new version, if given.
    concurrent_node_count: int, the number of nodes to upgrade concurrently.

  Raises:
    NodePoolError: if the node pool name can't be found in the cluster.

  Returns:
    str, a message about which nodes in the cluster will be upgraded and
        to which version.
  """
  node_message = 'All nodes'
  current_version = None
  if node_pool_name:
    node_message = '{} in node pool [{}]'.format(node_message, node_pool_name)
    if cluster:
      current_version = _NodePoolFromCluster(cluster, node_pool_name).version
  elif cluster:
    node_message = '{} ({} {})'.format(
        node_message, cluster.currentNodeCount,
        text.Pluralize(cluster.currentNodeCount, 'node'))
    current_version = cluster.currentNodeVersion

  if current_version:
    version_message = 'version [{}]'.format(current_version)
  else:
    version_message = 'its current version'

  if not new_version and cluster:
    new_version = cluster.currentMasterVersion

  if new_version:
    new_version_message = 'version [{}]'.format(new_version)
  else:
    new_version_message = 'the master version'

  concurrent_message = ''
  if concurrent_node_count:
    concurrent_message = ' {} {} will be upgraded at a time.'.format(
        concurrent_node_count, text.Pluralize(concurrent_node_count, 'node'))

  return ('{} of cluster [{}] will be upgraded from {} to {}.{}'.format(
      node_message, name, version_message, new_version_message,
      concurrent_message))


def ClusterUpgradeMessage(name,
                          server_conf=None,
                          cluster=None,
                          master=False,
                          node_pool_name=None,
                          new_version=None,
                          concurrent_node_count=None):
  """Get a message to print during gcloud container clusters upgrade.

  Args:
    name: str, the name of the cluster being upgraded.
    server_conf: the server config object.
    cluster: the cluster object.
    master: bool, if the upgrade applies to the master version.
    node_pool_name: str, the name of the node pool if the upgrade is for a
      specific node pool.
    new_version: str, the name of the new version, if given.
    concurrent_node_count: int, the number of nodes to upgrade concurrently.

  Raises:
    NodePoolError: if the node pool name can't be found in the cluster.

  Returns:
    str, a message about which nodes in the cluster will be upgraded and
        to which version.
  """
  if master:
    upgrade_message = _MasterUpgradeMessage(name, server_conf, cluster,
                                            new_version)
  else:
    upgrade_message = _NodeUpgradeMessage(name, cluster, node_pool_name,
                                          new_version, concurrent_node_count)

  return ('{} This operation is long-running and will block other operations '
          'on the cluster (including delete) until it has run to completion.'
          .format(upgrade_message))


def GetZone(args, ignore_property=False, required=True):
  """Get a zone from argument or property.

  Args:
    args: an argparse namespace. All the arguments that were provided to this
      command invocation.
    ignore_property: bool, if true, will get location only from argument.
    required: bool, if true, lack of zone will cause raise an exception.

  Raises:
    MinimumArgumentException: if location if required and not provided.

  Returns:
    str, a zone selected by user.
  """
  zone = getattr(args, 'zone', None)

  if ignore_property:
    zone_property = None
  else:
    zone_property = properties.VALUES.compute.zone.Get()

  if required and not zone and not zone_property:
    raise calliope_exceptions.MinimumArgumentException(['--zone'],
                                                       'Please specify zone')

  return zone or zone_property


def GetZoneOrRegion(args, ignore_property=False, required=True):
  """Get a location (zone or region) from argument or property.

  Args:
    args: an argparse namespace. All the arguments that were provided to this
      command invocation.
    ignore_property: bool, if true, will get location only from argument.
    required: bool, if true, lack of zone will cause raise an exception.

  Raises:
    MinimumArgumentException: if location if required and not provided.
    ConflictingArgumentsException: if both --zone and --region arguments
        provided.

  Returns:
    str, a location selected by user.
  """
  zone = getattr(args, 'zone', None)
  region = getattr(args, 'region', None)

  if ignore_property:
    zone_property = None
  else:
    zone_property = properties.VALUES.compute.zone.Get()

  if zone and region:
    raise calliope_exceptions.ConflictingArgumentsException(
        '--zone', '--region')

  location = region or zone or zone_property
  if required and not location:
    raise calliope_exceptions.MinimumArgumentException(
        ['--zone', '--region'], 'Please specify location')

  return location


def GetAutoUpgrade(args):
  """Gets the value of node auto-upgrade."""
  if args.IsSpecified('enable_autoupgrade'):
    return args.enable_autoupgrade
  if getattr(args, 'enable_kubernetes_alpha', False):
    return None
  if args.enable_autoupgrade:
    log.warning(util.WARN_AUTOUPGRADE_ENABLED_BY_DEFAULT)
  # Return default value
  return args.enable_autoupgrade


def GetAutoRepair(args):
  """Gets the value of node auto-repair."""
  if args.IsSpecified('enable_autorepair'):
    return args.enable_autorepair
  if getattr(args, 'enable_kubernetes_alpha', False):
    return None
  # Node pools using COS support auto repairs, enable it for them by
  # default. Other node pools using (Ubuntu, custom images) don't support
  # node auto repairs, attempting to enable autorepair for them will result
  # in API call failing so don't do it.
  return (args.image_type or '').lower() in ['', 'cos', 'cos_containerd']


def ParseUpdateOptionsBase(args, locations):
  """Helper function to build ClusterUpdateOptions object from args.

  Args:
    args: an argparse namespace. All the arguments that were provided to this
      command invocation.
    locations: list of strings. Zones in which cluster has nodes.

  Returns:
    ClusterUpdateOptions, object with data used to update cluster.
  """
  return api_adapter.UpdateClusterOptions(
      monitoring_service=args.monitoring_service,
      logging_service=args.logging_service,
      enable_stackdriver_kubernetes=args.enable_stackdriver_kubernetes,
      disable_addons=args.disable_addons,
      enable_autoscaling=args.enable_autoscaling,
      enable_binauthz=args.enable_binauthz,
      min_nodes=args.min_nodes,
      max_nodes=args.max_nodes,
      node_pool=args.node_pool,
      locations=locations,
      enable_master_authorized_networks=args.enable_master_authorized_networks,
      master_authorized_networks=args.master_authorized_networks,
      workload_pool=args.workload_pool,
      disable_workload_identity=args.disable_workload_identity,
      database_encryption_key=args.database_encryption_key,
      disable_database_encryption=args.disable_database_encryption,
      enable_vertical_pod_autoscaling=args.enable_vertical_pod_autoscaling,
      enable_autoprovisioning=args.enable_autoprovisioning,
      autoprovisioning_config_file=args.autoprovisioning_config_file,
      autoprovisioning_service_account=args.autoprovisioning_service_account,
      autoprovisioning_scopes=args.autoprovisioning_scopes,
      autoprovisioning_locations=args.autoprovisioning_locations,
      autoprovisioning_max_surge_upgrade=getattr(
          args, 'autoprovisioning_max_surge_upgrade', None),
      autoprovisioning_max_unavailable_upgrade=getattr(
          args, 'autoprovisioning_max_unavailable_upgrade', None),
      enable_autoprovisioning_autorepair=getattr(
          args, 'enable_autoprovisioning_autorepair', None),
      enable_autoprovisioning_autoupgrade=getattr(
          args, 'enable_autoprovisioning_autoupgrade', None),
      autoprovisioning_min_cpu_platform=getattr(
          args, 'autoprovisioning_min_cpu_platform', None),
      min_cpu=args.min_cpu,
      max_cpu=args.max_cpu,
      min_memory=args.min_memory,
      max_memory=args.max_memory,
      min_accelerator=args.min_accelerator,
      max_accelerator=args.max_accelerator)
