# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Create cluster command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.compute import metadata_utils
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.api_lib.container import api_adapter
from googlecloudsdk.api_lib.container import kubeconfig as kconfig
from googlecloudsdk.api_lib.container import util
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.container import constants
from googlecloudsdk.command_lib.container import container_command_util as cmd_util
from googlecloudsdk.command_lib.container import flags
from googlecloudsdk.command_lib.container import messages
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


def _AddAdditionalZonesFlag(parser, deprecated=True):
  action = None
  if deprecated:
    action = actions.DeprecationAction(
        'additional-zones',
        warn='This flag is deprecated. '
        'Use --node-locations=PRIMARY_ZONE,[ZONE,...] instead.')
  parser.add_argument(
      '--additional-zones',
      type=arg_parsers.ArgList(min_length=1),
      action=action,
      metavar='ZONE',
      help="""\
The set of additional zones in which the specified node footprint should be
replicated. All zones must be in the same region as the cluster's primary zone.
If additional-zones is not specified, all nodes will be in the cluster's primary
zone.

Note that `NUM_NODES` nodes will be created in each zone, such that if you
specify `--num-nodes=4` and choose one additional zone, 8 nodes will be created.

Multiple locations can be specified, separated by commas. For example:

  $ {command} example-cluster --zone us-central1-a --additional-zones us-central1-b,us-central1-c
""")


def _Args(parser):
  """Register flags for this command.

  Args:
    parser: An argparse.ArgumentParser-like object. It is mocked out in order to
      capture some information, but behaves like an ArgumentParser.
  """
  parser.add_argument(
      'name',
      help="""\
The name of the cluster to create.

The name may contain only lowercase alphanumerics and '-', must start with a
letter and end with an alphanumeric, and must be no longer than 40
characters.
""")
  # Timeout in seconds for operation
  parser.add_argument(
      '--timeout',
      type=int,
      default=3600,
      hidden=True,
      help='Timeout (seconds) for waiting on the operation to complete.')
  flags.AddAsyncFlag(parser)
  parser.add_argument(
      '--num-nodes',
      type=arg_parsers.BoundedInt(1),
      help='The number of nodes to be created in each of the cluster\'s zones.',
      default=3)
  flags.AddMachineTypeFlag(parser)
  parser.add_argument(
      '--subnetwork',
      help="""\
The Google Compute Engine subnetwork
(https://cloud.google.com/compute/docs/subnetworks) to which the cluster is
connected. The subnetwork must belong to the network specified by --network.

Cannot be used with the "--create-subnetwork" option.
""")
  parser.add_argument(
      '--network',
      help='The Compute Engine Network that the cluster will connect to. '
      'Google Kubernetes Engine will use this network when creating routes '
      'and firewalls for the clusters. Defaults to the \'default\' network.')
  parser.add_argument(
      '--cluster-ipv4-cidr',
      help='The IP address range for the pods in this cluster in CIDR '
      'notation (e.g. 10.0.0.0/14).  Prior to Kubernetes version 1.7.0 '
      'this must be a subset of 10.0.0.0/8; however, starting with version '
      '1.7.0 can be any RFC 1918 IP range.')
  parser.add_argument(
      '--enable-cloud-logging',
      action=actions.DeprecationAction(
          '--enable-cloud-logging',
          warn='From 1.14, legacy Stackdriver GKE logging is deprecated. Thus, '
          'flag `--enable-cloud-logging` is also deprecated. Please use '
          '`--enable-stackdriver-kubernetes` instead, to migrate to new '
          'Stackdriver Kubernetes Engine monitoring and logging. For more '
          'details, please read: '
          'https://cloud.google.com/monitoring/kubernetes-engine/migration.',
          action='store_true'),
      help='Automatically send logs from the cluster to the Google Cloud '
      'Logging API. This flag is deprecated, use '
      '`--enable-stackdriver-kubernetes` instead.')
  parser.add_argument(
      '--enable-cloud-monitoring',
      action=actions.DeprecationAction(
          '--enable-cloud-monitoring',
          warn='From 1.14, legacy Stackdriver GKE monitoring is deprecated. '
          'Thus, flag `--enable-cloud-monitoring` is also deprecated. Please '
          'use `--enable-stackdriver-kubernetes` instead, to migrate to new '
          'Stackdriver Kubernetes Engine monitoring and logging. For more '
          'details, please read: '
          'https://cloud.google.com/monitoring/kubernetes-engine/migration.',
          action='store_true'),
      help='Automatically send metrics from pods in the cluster to the Google '
      'Cloud Monitoring API. VM metrics will be collected by Google Compute '
      'Engine regardless of this setting. This flag is deprecated, use '
      '`--enable-stackdriver-kubernetes` instead.')
  parser.add_argument(
      '--disk-size',
      type=arg_parsers.BinarySize(lower_bound='10GB'),
      help='Size for node VM boot disks. Defaults to 100GB.')
  flags.AddBasicAuthFlags(parser)
  parser.add_argument(
      '--max-nodes-per-pool',
      type=arg_parsers.BoundedInt(100, api_adapter.MAX_NODES_PER_POOL),
      help='The maximum number of nodes to allocate per default initial node '
      'pool. Kubernetes Engine will automatically create enough nodes pools '
      'such that each node pool contains less than '
      '--max-nodes-per-pool nodes. Defaults to {nodes} nodes, but can be set '
      'as low as 100 nodes per pool on initial create.'.format(
          nodes=api_adapter.MAX_NODES_PER_POOL))
  flags.AddImageTypeFlag(parser, 'cluster')
  flags.AddImageFlag(parser, hidden=True)
  flags.AddImageProjectFlag(parser, hidden=True)
  flags.AddImageFamilyFlag(parser, hidden=True)
  flags.AddNodeLabelsFlag(parser)
  flags.AddTagsFlag(
      parser, """\
Applies the given Compute Engine tags (comma separated) on all nodes in the new
node-pool. Example:

  $ {command} example-cluster --tags=tag1,tag2

New nodes, including ones created by resize or recreate, will have these tags
on the Compute Engine API instance object and can be used in firewall rules.
See https://cloud.google.com/sdk/gcloud/reference/compute/firewall-rules/create
for examples.
""")
  parser.display_info.AddFormat(util.CLUSTERS_FORMAT)
  flags.AddIssueClientCertificateFlag(parser)
  flags.AddAcceleratorArgs(parser)
  flags.AddDiskTypeFlag(parser)
  flags.AddMetadataFlags(parser)
  flags.AddDatabaseEncryptionFlag(parser)
  flags.AddShieldedInstanceFlags(parser)
  flags.AddEnableShieldedNodesFlags(parser)


def ValidateBasicAuthFlags(args):
  """Validates flags associated with basic auth.

  Overwrites username if enable_basic_auth is specified; checks that password is
  set if username is non-empty.

  Args:
    args: an argparse namespace. All the arguments that were provided to this
      command invocation.

  Raises:
    util.Error, if username is non-empty and password is not set.
  """
  if args.IsSpecified('enable_basic_auth'):
    if not args.enable_basic_auth:
      args.username = ''
    # `enable_basic_auth == true` is a no-op defaults are resoved server-side
    # based on the version of the cluster. For versions before 1.12, this is
    # 'admin', otherwise '' (disabled).
  if not args.username and args.IsSpecified('password'):
    raise util.Error(constants.USERNAME_PASSWORD_ERROR_MSG)


def ParseCreateOptionsBase(args):
  """Parses the flags provided with the cluster creation command."""
  if args.IsSpecified('addons') and api_adapter.DASHBOARD in args.addons:
    log.warning(
        'The `KubernetesDashboard` addon is deprecated, and will be removed as '
        'an option for new clusters starting in 1.15. It is recommended to use '
        'the Cloud Console to manage and monitor your Kubernetes clusters, '
        'workloads and applications. See: '
        'https://cloud.google.com/kubernetes-engine/docs/concepts/dashboards')

  flags.MungeBasicAuthFlags(args)

  if args.IsSpecified('issue_client_certificate') and not (
      args.IsSpecified('enable_basic_auth') or args.IsSpecified('username')):
    log.warning('If `--issue-client-certificate` is specified but '
                '`--enable-basic-auth` or `--username` is not, our API will '
                'treat that as `--no-enable-basic-auth`.')

  flags.WarnForUnspecifiedIpAllocationPolicy(args)
  enable_autorepair = cmd_util.GetAutoRepair(args)
  flags.WarnForNodeModification(args, enable_autorepair)
  metadata = metadata_utils.ConstructMetadataDict(args.metadata,
                                                  args.metadata_from_file)

  return api_adapter.CreateClusterOptions(
      accelerators=args.accelerator,
      additional_zones=args.additional_zones,
      addons=args.addons,
      cluster_ipv4_cidr=args.cluster_ipv4_cidr,
      cluster_secondary_range_name=args.cluster_secondary_range_name,
      cluster_version=args.cluster_version,
      node_version=args.node_version,
      create_subnetwork=args.create_subnetwork,
      disk_type=args.disk_type,
      enable_autorepair=enable_autorepair,
      enable_autoscaling=args.enable_autoscaling,
      enable_autoupgrade=cmd_util.GetAutoUpgrade(args),
      enable_binauthz=args.enable_binauthz,
      enable_stackdriver_kubernetes=args.enable_stackdriver_kubernetes if args.IsSpecified('enable_stackdriver_kubernetes') else None,
      enable_cloud_logging=args.enable_cloud_logging if args.IsSpecified('enable_cloud_logging') else None,
      enable_cloud_monitoring=args.enable_cloud_monitoring if args.IsSpecified('enable_cloud_monitoring') else None,
      enable_ip_alias=args.enable_ip_alias,
      enable_intra_node_visibility=args.enable_intra_node_visibility,
      enable_kubernetes_alpha=args.enable_kubernetes_alpha,
      enable_cloud_run_alpha=args.enable_cloud_run_alpha if args.IsSpecified('enable_cloud_run_alpha') else None,
      enable_legacy_authorization=args.enable_legacy_authorization,
      enable_master_authorized_networks=args.enable_master_authorized_networks,
      enable_network_policy=args.enable_network_policy,
      enable_private_nodes=args.enable_private_nodes,
      enable_private_endpoint=args.enable_private_endpoint,
      image_type=args.image_type,
      image=args.image,
      image_project=args.image_project,
      image_family=args.image_family,
      issue_client_certificate=args.issue_client_certificate,
      labels=args.labels,
      local_ssd_count=args.local_ssd_count,
      maintenance_window=args.maintenance_window,
      maintenance_window_start=args.maintenance_window_start,
      maintenance_window_end=args.maintenance_window_end,
      maintenance_window_recurrence=args.maintenance_window_recurrence,
      master_authorized_networks=args.master_authorized_networks,
      master_ipv4_cidr=args.master_ipv4_cidr,
      max_nodes=args.max_nodes,
      max_nodes_per_pool=args.max_nodes_per_pool,
      min_cpu_platform=args.min_cpu_platform,
      min_nodes=args.min_nodes,
      network=args.network,
      node_disk_size_gb=utils.BytesToGb(args.disk_size),
      node_labels=args.node_labels,
      node_locations=args.node_locations,
      node_machine_type=args.machine_type,
      node_taints=args.node_taints,
      num_nodes=args.num_nodes,
      password=args.password,
      preemptible=args.preemptible,
      scopes=args.scopes,
      service_account=args.service_account,
      services_ipv4_cidr=args.services_ipv4_cidr,
      services_secondary_range_name=args.services_secondary_range_name,
      subnetwork=args.subnetwork,
      tags=args.tags,
      user=args.username,
      metadata=metadata,
      default_max_pods_per_node=args.default_max_pods_per_node,
      max_pods_per_node=args.max_pods_per_node,
      enable_tpu=args.enable_tpu,
      tpu_ipv4_cidr=args.tpu_ipv4_cidr,
      resource_usage_bigquery_dataset=args.resource_usage_bigquery_dataset,
      enable_network_egress_metering=args.enable_network_egress_metering,
      enable_resource_consumption_metering=\
          args.enable_resource_consumption_metering,
      database_encryption_key=args.database_encryption_key,
      workload_pool=args.workload_pool,
      workload_metadata=args.workload_metadata,
      workload_metadata_from_node=args.workload_metadata_from_node,
      enable_vertical_pod_autoscaling=args.enable_vertical_pod_autoscaling,
      enable_autoprovisioning=args.enable_autoprovisioning,
      autoprovisioning_config_file=args.autoprovisioning_config_file,
      autoprovisioning_service_account=args.autoprovisioning_service_account,
      autoprovisioning_scopes=args.autoprovisioning_scopes,
      autoprovisioning_locations=args.autoprovisioning_locations,
      autoprovisioning_max_surge_upgrade=getattr(args, 'autoprovisioning_max_surge_upgrade', None),
      autoprovisioning_max_unavailable_upgrade=getattr(args, 'autoprovisioning_max_unavailable_upgrade', None),
      enable_autoprovisioning_autorepair=getattr(args, 'enable_autoprovisioning_autorepair', None),
      enable_autoprovisioning_autoupgrade=getattr(args, 'enable_autoprovisioning_autoupgrade', None),
      autoprovisioning_min_cpu_platform=getattr(args, 'autoprovisioning_min_cpu_platform', None),
      min_cpu=args.min_cpu,
      max_cpu=args.max_cpu,
      min_memory=args.min_memory,
      max_memory=args.max_memory,
      min_accelerator=args.min_accelerator,
      max_accelerator=args.max_accelerator,
      shielded_secure_boot=args.shielded_secure_boot,
      shielded_integrity_monitoring=args.shielded_integrity_monitoring,
      reservation_affinity=getattr(args, 'reservation_affinity', None),
      reservation=getattr(args, 'reservation', None),
      enable_shielded_nodes=args.enable_shielded_nodes,
      max_surge_upgrade=args.max_surge_upgrade,
      max_unavailable_upgrade=args.max_unavailable_upgrade)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a cluster for running containers."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
          To create a cluster with the default configuration, run:

            $ {command} sample-cluster
          """,
  }

  @staticmethod
  def Args(parser):
    _Args(parser)
    _AddAdditionalZonesFlag(parser, deprecated=True)
    flags.AddNodeLocationsFlag(parser)
    flags.AddAddonsFlags(parser)
    flags.AddClusterAutoscalingFlags(parser)
    flags.AddMaxPodsPerNodeFlag(parser)
    flags.AddEnableAutoRepairFlag(parser, for_create=True)
    flags.AddEnableBinAuthzFlag(parser)
    flags.AddEnableKubernetesAlphaFlag(parser)
    flags.AddEnableCloudRunAlphaFlag(parser)
    flags.AddEnableStackdriverKubernetesFlag(parser)
    flags.AddEnableLegacyAuthorizationFlag(parser)
    flags.AddIPAliasFlags(parser)
    flags.AddLabelsFlag(parser)
    flags.AddLocalSSDFlag(parser)
    flags.AddMaintenanceWindowGroup(parser)
    flags.AddMasterAuthorizedNetworksFlags(parser)
    flags.AddMinCpuPlatformFlag(parser)
    flags.AddNetworkPolicyFlags(parser)
    flags.AddNodeTaintsFlag(parser)
    flags.AddPreemptibleFlag(parser)
    flags.AddClusterNodeIdentityFlags(parser)
    flags.AddPrivateClusterFlags(parser, with_deprecated=False)
    flags.AddClusterVersionFlag(parser)
    flags.AddNodeVersionFlag(parser)
    flags.AddEnableAutoUpgradeFlag(parser, default=True)
    flags.AddEnableIntraNodeVisibilityFlag(parser)
    flags.AddTpuFlags(parser, hidden=False)
    flags.AddAutoprovisioningFlags(
        parser, hidden=False, for_create=True, ga=True)
    flags.AddResourceUsageExportFlags(parser)
    flags.AddVerticalPodAutoscalingFlag(parser)
    flags.AddWorkloadIdentityFlags(parser)
    flags.AddWorkloadMetadataFlag(parser)
    flags.AddReservationAffinityFlags(parser)
    flags.AddSurgeUpgradeFlag(parser)
    flags.AddMaxUnavailableUpgradeFlag(parser)

  def ParseCreateOptions(self, args):
    return ParseCreateOptionsBase(args)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Cluster message for the successfully created cluster.

    Raises:
      util.Error, if creation failed.
    """
    if args.async_ and not args.IsSpecified('format'):
      args.format = util.OPERATIONS_FORMAT

    util.CheckKubectlInstalled()

    adapter = self.context['api_adapter']
    location_get = self.context['location_get']
    location = location_get(args)

    cluster_ref = adapter.ParseCluster(args.name, location)
    options = self.ParseCreateOptions(args)

    if options.private_cluster and not (
        options.enable_master_authorized_networks or
        options.master_authorized_networks):
      log.warning(
          '`--private-cluster` makes the master inaccessible from '
          'cluster-external IP addresses, by design. To allow limited '
          'access to the master, see the `--master-authorized-networks` flags '
          'and our documentation on setting up private clusters: '
          'https://cloud.google.com'
          '/kubernetes-engine/docs/how-to/private-clusters')

    if not options.enable_shielded_nodes:
      log.warning(
          'Starting with version 1.18, clusters will have shielded GKE nodes by default.'
      )

    if options.enable_ip_alias:
      log.warning(
          'The Pod address range limits the maximum size of the cluster. '
          'Please refer to https://cloud.google.com/kubernetes-engine/docs/how-to/flexible-pod-cidr to learn how to optimize IP address allocation.'
      )
    else:
      max_node_number = util.CalculateMaxNodeNumberByPodRange(
          options.cluster_ipv4_cidr)
      if max_node_number > 0:
        log.warning(
            'Your Pod address range (`--cluster-ipv4-cidr`) can accommodate at most %d node(s). '
            % max_node_number)

    if options.enable_kubernetes_alpha:
      console_io.PromptContinue(
          message=constants.KUBERNETES_ALPHA_PROMPT,
          throw_if_unattended=True,
          cancel_on_no=True)

    if options.enable_autorepair is not None:
      log.status.Print(
          messages.AutoUpdateUpgradeRepairMessage(options.enable_autorepair,
                                                  'autorepair'))

    if options.accelerators is not None:
      log.status.Print(constants.KUBERNETES_GPU_LIMITATION_MSG)

    operation = None
    try:
      operation_ref = adapter.CreateCluster(cluster_ref, options)
      if args.async_:
        return adapter.GetCluster(cluster_ref)

      operation = adapter.WaitForOperation(
          operation_ref,
          'Creating cluster {0} in {1}'.format(cluster_ref.clusterId,
                                               cluster_ref.zone),
          timeout_s=args.timeout)
      cluster = adapter.GetCluster(cluster_ref)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error, util.HTTP_ERROR_FORMAT)

    log.CreatedResource(cluster_ref)
    cluster_url = util.GenerateClusterUrl(cluster_ref)
    log.status.Print('To inspect the contents of your cluster, go to: ' +
                     cluster_url)
    if operation.detail:
      # Non-empty detail on a DONE create operation should be surfaced as
      # a warning to end user.
      log.warning(operation.detail)

    try:
      util.ClusterConfig.Persist(cluster, cluster_ref.projectId)
    except kconfig.MissingEnvVarError as error:
      log.warning(error)

    return [cluster]


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create a cluster for running containers."""

  @staticmethod
  def Args(parser):
    _Args(parser)
    group = parser.add_mutually_exclusive_group()
    _AddAdditionalZonesFlag(group, deprecated=True)
    flags.AddNodeLocationsFlag(group)
    flags.AddBetaAddonsFlags(parser)
    flags.AddBootDiskKmsKeyFlag(parser)
    flags.AddClusterAutoscalingFlags(parser)
    flags.AddMaxPodsPerNodeFlag(parser)
    flags.AddEnableAutoRepairFlag(parser, for_create=True)
    flags.AddEnableBinAuthzFlag(parser)
    flags.AddEnableKubernetesAlphaFlag(parser)
    flags.AddEnableLoggingMonitoringSystemOnlyFlag(parser)
    flags.AddEnableCloudRunAlphaFlag(parser)
    flags.AddEnableLegacyAuthorizationFlag(parser)
    flags.AddIPAliasFlags(parser)
    flags.AddIstioConfigFlag(parser)
    flags.AddLabelsFlag(parser)
    flags.AddLocalSSDFlag(parser)
    flags.AddMaintenanceWindowGroup(parser)
    flags.AddMasterAuthorizedNetworksFlags(parser)
    flags.AddMinCpuPlatformFlag(parser)
    flags.AddNetworkPolicyFlags(parser)
    flags.AddNodeTaintsFlag(parser)
    flags.AddPreemptibleFlag(parser)
    flags.AddPodSecurityPolicyFlag(parser)
    flags.AddAllowRouteOverlapFlag(parser)
    flags.AddClusterNodeIdentityFlags(parser)
    flags.AddPrivateClusterFlags(parser, with_deprecated=True)
    flags.AddEnableStackdriverKubernetesFlag(parser)
    flags.AddTpuFlags(parser, hidden=False, enable_tpu_service_networking=True)
    flags.AddAutoprovisioningFlags(parser, hidden=False, for_create=True)
    flags.AddAutoscalingProfilesFlag(parser)
    flags.AddVerticalPodAutoscalingFlag(parser)
    flags.AddResourceUsageExportFlags(parser)
    flags.AddAuthenticatorSecurityGroupFlags(parser)
    flags.AddEnableIntraNodeVisibilityFlag(parser)
    flags.AddWorkloadIdentityFlags(parser, use_workload_pool=False)
    flags.AddWorkloadMetadataFlag(parser, use_mode=False)
    flags.AddEnableAutoUpgradeFlag(parser, default=True)
    flags.AddSurgeUpgradeFlag(parser, default=1)
    flags.AddMaxUnavailableUpgradeFlag(parser, is_create=True)
    flags.AddReservationAffinityFlags(parser)
    flags.AddMasterGlobalAccessFlag(parser)
    flags.AddEnableGvnicFlag(parser)
    _AddReleaseChannelGroup(parser)

  def ParseCreateOptions(self, args):
    ops = ParseCreateOptionsBase(args)
    flags.WarnForNodeVersionAutoUpgrade(args)
    flags.ValidateSurgeUpgradeSettings(args)
    ops.boot_disk_kms_key = args.boot_disk_kms_key
    ops.min_cpu_platform = args.min_cpu_platform
    ops.enable_pod_security_policy = args.enable_pod_security_policy
    ops.allow_route_overlap = args.allow_route_overlap
    ops.private_cluster = args.private_cluster
    ops.istio_config = args.istio_config
    ops.enable_vertical_pod_autoscaling = args.enable_vertical_pod_autoscaling
    ops.security_group = args.security_group
    ops.identity_namespace = args.identity_namespace
    flags.ValidateIstioConfigCreateArgs(args.istio_config, args.addons)
    ops.release_channel = args.release_channel
    ops.max_surge_upgrade = args.max_surge_upgrade
    ops.max_unavailable_upgrade = args.max_unavailable_upgrade
    ops.autoscaling_profile = args.autoscaling_profile
    ops.enable_tpu_service_networking = args.enable_tpu_service_networking
    ops.enable_logging_monitoring_system_only = args.enable_logging_monitoring_system_only
    ops.enable_master_global_access = args.enable_master_global_access
    ops.enable_gvnic = args.enable_gvnic
    return ops


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(Create):
  """Create a cluster for running containers."""

  @staticmethod
  def Args(parser):
    _Args(parser)
    group = parser.add_mutually_exclusive_group()
    _AddAdditionalZonesFlag(group, deprecated=True)
    flags.AddNodeLocationsFlag(group)
    flags.AddAlphaAddonsFlags(parser)
    flags.AddBootDiskKmsKeyFlag(parser)
    flags.AddClusterAutoscalingFlags(parser)
    flags.AddMaxPodsPerNodeFlag(parser)
    flags.AddEnableAutoRepairFlag(parser, for_create=True)
    flags.AddEnableBinAuthzFlag(parser)
    flags.AddEnableKubernetesAlphaFlag(parser)
    flags.AddEnableCloudRunAlphaFlag(parser)
    flags.AddEnableLegacyAuthorizationFlag(parser)
    flags.AddIPAliasFlags(parser)
    flags.AddIstioConfigFlag(parser)
    flags.AddLabelsFlag(parser)
    flags.AddLocalSSDAndLocalSSDVolumeConfigsFlag(parser)
    flags.AddMaintenanceWindowGroup(parser)
    flags.AddMasterAuthorizedNetworksFlags(parser)
    flags.AddMinCpuPlatformFlag(parser)
    flags.AddNetworkPolicyFlags(parser)
    flags.AddILBSubsettingFlags(parser)
    flags.AddAutoprovisioningFlags(parser, hidden=False, for_create=True)
    flags.AddAutoscalingProfilesFlag(parser)
    flags.AddNodeTaintsFlag(parser)
    flags.AddPreemptibleFlag(parser)
    flags.AddPodSecurityPolicyFlag(parser)
    flags.AddAllowRouteOverlapFlag(parser)
    flags.AddPrivateClusterFlags(parser, with_deprecated=True)
    flags.AddClusterNodeIdentityFlags(parser)
    flags.AddTpuFlags(parser, hidden=False, enable_tpu_service_networking=True)
    flags.AddEnableStackdriverKubernetesFlag(parser)
    flags.AddEnableLoggingMonitoringSystemOnlyFlag(parser)
    flags.AddWorkloadIdentityFlags(parser, use_workload_pool=False)
    flags.AddWorkloadMetadataFlag(parser, use_mode=False)
    flags.AddResourceUsageExportFlags(parser)
    flags.AddAuthenticatorSecurityGroupFlags(parser)
    flags.AddVerticalPodAutoscalingFlag(parser)
    flags.AddSecurityProfileForCreateFlags(parser)
    flags.AddInitialNodePoolNameArg(parser, hidden=False)
    flags.AddEnablePrivateIpv6AccessFlag(parser, hidden=True)
    flags.AddEnableIntraNodeVisibilityFlag(parser)
    flags.AddDisableDefaultSnatFlag(parser, for_cluster_create=True)
    _AddReleaseChannelGroup(parser)
    flags.AddEnableAutoUpgradeFlag(parser, default=True)
    flags.AddSurgeUpgradeFlag(parser, default=1)
    flags.AddMaxUnavailableUpgradeFlag(parser, is_create=True)
    flags.AddLinuxSysctlFlags(parser)
    flags.AddNodeConfigFlag(parser)
    flags.AddCostManagementConfigFlag(parser)
    flags.AddReservationAffinityFlags(parser)
    flags.AddDatapathProviderFlag(parser)
    flags.AddMasterGlobalAccessFlag(parser)
    flags.AddEnableGvnicFlag(parser)

  def ParseCreateOptions(self, args):
    ops = ParseCreateOptionsBase(args)
    flags.WarnForNodeVersionAutoUpgrade(args)
    flags.ValidateSurgeUpgradeSettings(args)
    ops.boot_disk_kms_key = args.boot_disk_kms_key
    ops.autoscaling_profile = args.autoscaling_profile
    ops.local_ssd_volume_configs = args.local_ssd_volumes
    ops.enable_pod_security_policy = args.enable_pod_security_policy
    ops.allow_route_overlap = args.allow_route_overlap
    ops.private_cluster = args.private_cluster
    ops.enable_private_nodes = args.enable_private_nodes
    ops.enable_private_endpoint = args.enable_private_endpoint
    ops.master_ipv4_cidr = args.master_ipv4_cidr
    ops.enable_tpu_service_networking = args.enable_tpu_service_networking
    ops.istio_config = args.istio_config
    ops.identity_namespace = args.identity_namespace
    ops.security_group = args.security_group
    flags.ValidateIstioConfigCreateArgs(args.istio_config, args.addons)
    ops.enable_vertical_pod_autoscaling = args.enable_vertical_pod_autoscaling
    ops.security_profile = args.security_profile
    ops.security_profile_runtime_rules = args.security_profile_runtime_rules
    ops.node_pool_name = args.node_pool_name
    ops.enable_network_egress_metering = args.enable_network_egress_metering
    ops.enable_resource_consumption_metering = args.enable_resource_consumption_metering
    ops.enable_private_ipv6_access = args.enable_private_ipv6_access
    ops.release_channel = args.release_channel
    ops.max_surge_upgrade = args.max_surge_upgrade
    ops.max_unavailable_upgrade = args.max_unavailable_upgrade
    ops.linux_sysctls = args.linux_sysctls
    ops.enable_l4_ilb_subsetting = args.enable_l4_ilb_subsetting
    ops.disable_default_snat = args.disable_default_snat
    ops.node_config = args.node_config
    ops.enable_cost_management = args.enable_cost_management
    ops.enable_logging_monitoring_system_only = args.enable_logging_monitoring_system_only
    ops.datapath_provider = args.datapath_provider
    ops.enable_master_global_access = args.enable_master_global_access
    ops.enable_gvnic = args.enable_gvnic
    return ops


def _AddReleaseChannelGroup(parser):
  """Add flag group for release channels."""
  versioning_groups = parser.add_mutually_exclusive_group("""\
--release-channel cannot be specified if Custom Version Flags
(--cluster-version or --node-version) are used.
""")
  flags.AddReleaseChannelFlag(versioning_groups)
  custom_version_group = versioning_groups.add_group("""\
Custom Version Flags:
""")
  flags.AddClusterVersionFlag(custom_version_group)
  flags.AddNodeVersionFlag(custom_version_group)
