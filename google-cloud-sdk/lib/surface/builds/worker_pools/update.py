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
"""Update worker pool command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.api_lib.cloudbuild import workerpool_config
from googlecloudsdk.api_lib.compute import utils as compute_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.cloudbuild import workerpool_flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


class Update(base.UpdateCommand):
  """Update a workerpool used by Google Cloud Build.

  Update a worker pool used by Google Cloud Build.
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
    """
    parser = workerpool_flags.AddWorkerpoolUpdateArgs(parser)
    parser.display_info.AddFormat("""
          table(
            name,
            createTime.date('%Y-%m-%dT%H:%M:%S%Oz', undefined='-'),
            state
          )
        """)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """

    client = cloudbuild_util.GetClientInstanceAlpha()
    messages = cloudbuild_util.GetMessagesModuleAlpha()

    parent = properties.VALUES.core.project.Get(required=True)

    # Get the workerpool proto from either the flags or the specified file.
    wp = messages.WorkerPool()
    if args.config_from_file is not None:
      wp = workerpool_config.LoadWorkerpoolConfigFromPath(
          args.config_from_file, messages)
    else:
      wp.name = args.WORKER_POOL
      if args.region is not None:
        wp.region = args.region
      if args.peered_network is not None:
        network_config = messages.NetworkConfig()
        network_config.peeredNetwork = args.peered_network
        wp.networkConfig = network_config
      worker_config = messages.WorkerConfig()
      if args.worker_machine_type is not None:
        worker_config.machineType = args.worker_machine_type
      if args.worker_disk_size is not None:
        worker_config.diskSizeGb = compute_utils.BytesToGb(
            args.worker_disk_size)
      wp.workerConfig = worker_config

    # Get the workerpool ref
    wp_resource = resources.REGISTRY.Parse(
        None,
        collection='cloudbuild.projects.workerPools',
        api_version='v1alpha2',
        params={
            'projectsId': parent,
            'workerPoolsId': wp.name,
        })

    update_mask = cloudbuild_util.MessageToFieldPaths(wp)
    req = messages.CloudbuildProjectsWorkerPoolsPatchRequest(
        name=wp_resource.RelativeName(),
        workerPool=wp,
        updateMask=','.join(update_mask))
    # Send the Update request
    updated_wp = client.projects_workerPools.Patch(req)

    log.UpdatedResource(wp_resource)

    # Format the workerpool name for display
    try:
      updated_wp.name = cloudbuild_util.WorkerPoolShortName(updated_wp.name)
    except ValueError:
      pass  # Must be an old version.

    return updated_wp
