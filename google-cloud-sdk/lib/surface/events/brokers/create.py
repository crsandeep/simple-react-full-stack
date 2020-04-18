# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Command for creating a broker."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.events import iam_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.events import eventflow_operations
from googlecloudsdk.command_lib.events import exceptions
from googlecloudsdk.command_lib.events import flags
from googlecloudsdk.command_lib.events import resource_args
from googlecloudsdk.command_lib.iam import iam_util as core_iam_util
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import flags as serverless_flags
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import log
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io


_DEFAULT_BROKER_NAME = 'default'

_DATA_PLANE_SECRET_NAME = 'google-cloud-key'
# These permissions are needed at a minimum for all Source kinds
_DATA_PLANE_SECRET_MIN_REQUIRED_ROLES = frozenset(['roles/pubsub.editor'])

# As an alternative to the more fine-grained permissions above, we allow this
# service accounts with this role which should give it all necessary current and
# future permissions.
_OWNER_ROLE = 'roles/owner'

_INJECTION_LABELS = {'knative-eventing-injection': 'enabled'}


class Create(base.Command):
  """Create a broker to initialize a namespace for eventing."""

  detailed_help = {
      'DESCRIPTION': """
          {description}
          Creates a new broker for the given namespace.
          Currently, you can only create a broker named "default".
          This command is only available with Cloud Run for Anthos.
          """,
      'EXAMPLES': """
          To create a broker, run:

              $ {command} create default
          """,
  }

  @staticmethod
  def CommonArgs(parser):
    """Defines arguments common to all release tracks."""
    # TODO(b/147151675): Make service account optional and create if missing.
    flags.AddServiceAccountFlag(parser)
    flags.AddBrokerArg(parser)
    namespace_presentation = presentation_specs.ResourcePresentationSpec(
        '--namespace',
        resource_args.GetCoreNamespaceResourceSpec(),
        'Namespace to create the Broker in.',
        required=True,
        prefixes=False)
    concept_parsers.ConceptParser(
        [namespace_presentation]).AddToParser(parser)

  @staticmethod
  def Args(parser):
    Create.CommonArgs(parser)

  def Run(self, args):
    """Executes when the user runs the delete command."""
    if serverless_flags.GetPlatform() == serverless_flags.PLATFORM_MANAGED:
      raise exceptions.UnsupportedArgumentError(
          'This command is only available with Cloud Run for Anthos.')

    if args.BROKER != _DEFAULT_BROKER_NAME:
      raise exceptions.UnsupportedArgumentError(
          'Only brokers named "default" may be created.')

    conn_context = connection_context.GetConnectionContext(
        args, serverless_flags.Product.EVENTS, self.ReleaseTrack())

    service_account_ref = resources.REGISTRY.Parse(
        args.service_account,
        params={'projectsId': '-'},
        collection=core_iam_util.SERVICE_ACCOUNTS_COLLECTION)
    namespace_ref = args.CONCEPTS.namespace.Parse()
    secret_ref = resources.REGISTRY.Parse(
        _DATA_PLANE_SECRET_NAME,
        params={'namespacesId': namespace_ref.Name()},
        collection='run.api.v1.namespaces.secrets',
        api_version='v1')

    # Validate the service account has the necessary roles
    roles = iam_util.GetProjectRolesForServiceAccount(service_account_ref)
    if not (_OWNER_ROLE in roles or
            _DATA_PLANE_SECRET_MIN_REQUIRED_ROLES.issubset(roles)):
      missing_roles = _DATA_PLANE_SECRET_MIN_REQUIRED_ROLES - roles
      raise exceptions.ServiceAccountMissingRequiredPermissions(
          'Service account [{}] does not have necessary role(s): {}'.format(
              service_account_ref.Name(), ', '.join(missing_roles)))

    with eventflow_operations.Connect(conn_context) as client:
      if console_io.CanPrompt():
        console_io.PromptContinue(
            message='This will create a new key for the provided '
            'service account.',
            cancel_on_no=True)
      _, key_ref = client.CreateOrReplaceServiceAccountSecret(
          secret_ref, service_account_ref)
      client.UpdateNamespaceWithLabels(namespace_ref, _INJECTION_LABELS)

    log.status.Print('Created broker [{}] in namespace [{}] with '
                     'key [{}] for service account [{}].'.format(
                         args.BROKER, namespace_ref.Name(), key_ref.Name(),
                         service_account_ref.Name()))
