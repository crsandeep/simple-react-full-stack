# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Command for updating env vars and other configuration info."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.run import service
from googlecloudsdk.api_lib.util import messages as messages_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.projects import util as projects_util
from googlecloudsdk.command_lib.run import config_changes
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import pretty_print
from googlecloudsdk.command_lib.run import resource_args
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.command_lib.run import stages
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import progress_tracker
from surface.run import deploy


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Replace(base.Command):
  """Creates or replaces a service from a YAML Service specification."""

  detailed_help = {
      'DESCRIPTION':
          """\
          {description}
          """,
      'EXAMPLES':
          """\
          To replace the specification for myservice

              $ {command} myservice.yaml

         """,
  }

  @staticmethod
  def Args(parser):

    # Flags specific to connecting to a cluster
    cluster_group = flags.GetClusterArgGroup(parser)
    namespace_presentation = presentation_specs.ResourcePresentationSpec(
        '--namespace',
        resource_args.GetNamespaceResourceSpec(),
        'Namespace to replace service.',
        required=True,
        prefixes=False)
    concept_parsers.ConceptParser(
        [namespace_presentation]).AddToParser(cluster_group)

    # Flags not specific to any platform
    flags.AddAsyncFlag(parser)
    parser.add_argument(
        'FILE',
        action='store',
        type=arg_parsers.YAMLFileContents(),
        help='The absolute path to the YAML file with a Knative '
        'service definition for the service to update or deploy.')

  def Run(self, args):
    """Create or Update service from YAML."""
    conn_context = connection_context.GetConnectionContext(
        args, flags.Product.RUN, self.ReleaseTrack())

    with serverless_operations.Connect(conn_context) as client:
      new_service = service.Service(
          messages_util.DictToMessageWithErrorCheck(
              args.FILE, client.messages_module.Service),
          client.messages_module)

      # If managed, namespace must match project (or will default to project if
      # not specified).
      # If not managed, namespace simply must not conflict if specified in
      # multiple places (or will default to "default" if not specified).
      namespace = args.CONCEPTS.namespace.Parse().Name()  # From flag or default
      if new_service.metadata.namespace is not None:
        if (args.IsSpecified('namespace') and
            namespace != new_service.metadata.namespace):
          raise exceptions.ConfigurationError(
              'Namespace specified in file does not match passed flag.')
        namespace = new_service.metadata.namespace
        if flags.GetPlatform() == flags.PLATFORM_MANAGED:
          project = properties.VALUES.core.project.Get()
          project_number = projects_util.GetProjectNumber(project)
          if namespace != project and namespace != str(project_number):
            raise exceptions.ConfigurationError(
                'Namespace must be project ID [{}] or quoted number [{}] for '
                'Cloud Run (fully managed).'.format(project, project_number))
      new_service.metadata.namespace = namespace

      changes = [config_changes.ReplaceServiceChange(new_service)]
      service_ref = resources.REGISTRY.Parse(
          new_service.metadata.name,
          params={'namespacesId': new_service.metadata.namespace},
          collection='run.namespaces.services')
      original_service = client.GetService(service_ref)

      pretty_print.Info(deploy.GetStartDeployMessage(conn_context, service_ref))

      deployment_stages = stages.ServiceStages()
      header = (
          'Deploying...' if original_service else 'Deploying new service...')
      with progress_tracker.StagedProgressTracker(
          header,
          deployment_stages,
          failure_message='Deployment failed',
          suppress_output=args.async_) as tracker:
        client.ReleaseService(
            service_ref,
            changes,
            tracker,
            asyn=args.async_,
            allow_unauthenticated=None,
            for_replace=True)
      if args.async_:
        pretty_print.Success(
            'Service [{{bold}}{serv}{{reset}}] is deploying '
            'asynchronously.'.format(serv=service_ref.servicesId))
      else:
        pretty_print.Success(deploy.GetSuccessMessageForSynchronousDeploy(
            client, service_ref))
