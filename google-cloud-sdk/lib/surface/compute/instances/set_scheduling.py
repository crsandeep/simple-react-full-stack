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
"""Command for setting scheduling for virtual machine instances."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import instance_utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.instances import flags
from googlecloudsdk.command_lib.compute.sole_tenancy import flags as sole_tenancy_flags
from googlecloudsdk.command_lib.compute.sole_tenancy import util as sole_tenancy_util


@base.ReleaseTracks(base.ReleaseTrack.GA)
class SetSchedulingInstances(base.SilentCommand):
  """Set scheduling options for Google Compute Engine virtual machines.

    *${command}* is used to configure scheduling options for Google Compute
  Engine virtual machines.
  """

  detailed_help = {
      'EXAMPLES':
          """
  To set instance to be terminated during maintenance, run:

    $ {command} example-instance  --maintenance-policy=TERMINATE --zone=us-central1-b
  """
  }

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        '--restart-on-failure',
        action=arg_parsers.StoreTrueFalseAction,
        help="""\
        The instances will be restarted if they are terminated by Compute
        Engine.  This does not affect terminations performed by the user.
        """)

    flags.AddMaintenancePolicyArgs(parser)
    sole_tenancy_flags.AddNodeAffinityFlagToParser(parser, is_update=True)
    flags.INSTANCE_ARG.AddArgument(parser)

  def _Run(self, args, support_min_node_cpu=False):
    """Issues request necessary for setting scheduling options."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    instance_ref = flags.INSTANCE_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=flags.GetInstanceZoneScopeLister(client))

    scheduling_options = client.messages.Scheduling()

    scheduling_options.automaticRestart = args.restart_on_failure

    cleared_fields = []

    if support_min_node_cpu:
      if args.IsSpecified('min_node_cpu'):
        scheduling_options.minNodeCpus = int(args.min_node_cpu)
      elif args.IsSpecified('clear_min_node_cpu'):
        scheduling_options.minNodeCpus = None
        cleared_fields.append('minNodeCpus')

    if args.IsSpecified('maintenance_policy'):
      scheduling_options.onHostMaintenance = (
          client.messages.Scheduling.OnHostMaintenanceValueValuesEnum(
              args.maintenance_policy))

    if instance_utils.IsAnySpecified(args, 'node', 'node_affinity_file',
                                     'node_group'):
      affinities = sole_tenancy_util.GetSchedulingNodeAffinityListFromArgs(
          args, client.messages)
      scheduling_options.nodeAffinities = affinities
    elif args.IsSpecified('clear_node_affinities'):
      scheduling_options.nodeAffinities = []
      cleared_fields.append('nodeAffinities')

    with holder.client.apitools_client.IncludeFields(cleared_fields):
      request = client.messages.ComputeInstancesSetSchedulingRequest(
          instance=instance_ref.Name(),
          project=instance_ref.project,
          scheduling=scheduling_options,
          zone=instance_ref.zone)

      return client.MakeRequests([(client.apitools_client.instances,
                                   'SetScheduling', request)])

  def Run(self, args):
    return self._Run(args)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class SetSchedulingInstancesBeta(SetSchedulingInstances):
  """Set scheduling options for Google Compute Engine virtual machines.

    *${command}* is used to configure scheduling options for Google Compute
  Engine virtual machines.
  """

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        '--restart-on-failure',
        action=arg_parsers.StoreTrueFalseAction,
        help="""\
        The instances will be restarted if they are terminated by Compute
        Engine.  This does not affect terminations performed by the user.
        """)
    flags.AddMaintenancePolicyArgs(parser)
    sole_tenancy_flags.AddNodeAffinityFlagToParser(parser, is_update=True)
    flags.INSTANCE_ARG.AddArgument(parser)
    flags.AddMinNodeCpuArg(parser, is_update=True)

  def Run(self, args):
    return self._Run(args, support_min_node_cpu=True)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class SetSchedulingInstancesAlpha(SetSchedulingInstancesBeta):
  """Set scheduling options for Google Compute Engine virtual machines.

    *${command}* is used to configure scheduling options for Google Compute
  Engine virtual machines.
  """

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        '--restart-on-failure',
        action=arg_parsers.StoreTrueFalseAction,
        help="""\
        The instances will be restarted if they are terminated by Compute
        Engine.  This does not affect terminations performed by the user.
        """)

    # Deprecated in Alpha
    flags.AddMaintenancePolicyArgs(parser, deprecate=True)
    sole_tenancy_flags.AddNodeAffinityFlagToParser(parser, is_update=True)
    flags.INSTANCE_ARG.AddArgument(parser)
    flags.AddMinNodeCpuArg(parser, is_update=True)
