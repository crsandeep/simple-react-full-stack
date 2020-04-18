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
"""Command for deleting a service."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import itertools

from googlecloudsdk.api_lib.events import iam_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.events import eventflow_operations
from googlecloudsdk.command_lib.events import exceptions
from googlecloudsdk.command_lib.events import flags
from googlecloudsdk.command_lib.iam import iam_util as core_iam_util
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import flags as serverless_flags
from googlecloudsdk.core import log
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io


_CONTROL_PLANE_SECRET_NAME = 'google-cloud-key'
# These permissions are needed at a minimum for all Source kinds
_CONTROL_PLANE_SECRET_MIN_REQUIRED_ROLES = frozenset(['roles/pubsub.editor'])
# Roles needed per source kind. Taken from the table at:
# https://github.com/google/knative-gcp/blob/a473d5cd7d668697140e630e46425df747b80bef/docs/install/README.md
_CONTROL_PLANE_SECRET_PER_SOURCE_ROLES = {
    'CloudPubSubSource': ['roles/pubsub.editor'],
    'CloudStorageSource': ['roles/storage.admin'],
    'CloudSchedulerSource': ['roles/cloudscheduler.admin'],
    'CloudAuditLogsSource': [
        'roles/pubsub.admin', 'roles/logging.configWriter',
        'roles/logging.privateLogViewer'
    ]
}
_CONTROL_PLANE_SECRET_OPTIONAL_ROLES = frozenset(
    itertools.chain.from_iterable(
        _CONTROL_PLANE_SECRET_PER_SOURCE_ROLES.values()))
_CONTROL_PLANE_NAMESPACE = 'cloud-run-events'

# As an alternative to the more fine-grained permissions above, we allow this
# service accounts with this role which should give it all necessary current and
# future permissions.
_OWNER_ROLE = 'roles/owner'


class Init(base.Command):
  """Initialize a cluster for eventing."""

  detailed_help = {
      'DESCRIPTION': """
          {description}
          Creates a new key for the provided service account.
          This command is only available with Cloud Run for Anthos.
          """,
      'EXAMPLES': """
          To initialize a cluster:

              $ {command}
          """,
  }

  @staticmethod
  def CommonArgs(parser):
    """Defines arguments common to all release tracks."""
    # TODO(b/147151675): Make service account optional and create if missing.
    flags.AddServiceAccountFlag(parser)

  @staticmethod
  def Args(parser):
    Init.CommonArgs(parser)

  def Run(self, args):
    """Executes when the user runs the delete command."""
    if serverless_flags.GetPlatform() == serverless_flags.PLATFORM_MANAGED:
      raise exceptions.UnsupportedArgumentError(
          'This command is only available with Cloud Run for Anthos.')

    conn_context = connection_context.GetConnectionContext(
        args, serverless_flags.Product.EVENTS, self.ReleaseTrack())

    service_account_ref = resources.REGISTRY.Parse(
        args.service_account,
        params={'projectsId': '-'},
        collection=core_iam_util.SERVICE_ACCOUNTS_COLLECTION)
    secret_ref = resources.REGISTRY.Parse(
        _CONTROL_PLANE_SECRET_NAME,
        params={'namespacesId': _CONTROL_PLANE_NAMESPACE},
        collection='run.api.v1.namespaces.secrets',
        api_version='v1')

    # Validate the service account has the necessary roles
    roles = iam_util.GetProjectRolesForServiceAccount(service_account_ref)
    if _OWNER_ROLE in roles:
      # This role is enough to cover everything we need. Nothing more to check.
      pass
    elif _CONTROL_PLANE_SECRET_MIN_REQUIRED_ROLES.issubset(roles):
      # We have the minimum necessary permissions to continue.
      # Check if there's additional permissions the user may want to add.
      missing_optional_roles = _CONTROL_PLANE_SECRET_OPTIONAL_ROLES - roles
      if missing_optional_roles:
        optional_roles_msg = '\n'.join([
            '- {}: {}'.format(s, ', '.join(r))
            for s, r in _CONTROL_PLANE_SECRET_PER_SOURCE_ROLES.items()
        ])
        log.warning('The service account has the minimum necessary project '
                    'permissions, but certain source kinds may require '
                    'additional permissions to use. Consider adding missing '
                    'roles to the service account if you plan to '
                    'use event types from these source kinds. '
                    'Necessary roles per source kind:\n{}\n'.format(
                        optional_roles_msg))
    else:
      # Missing the minimum necessary permissions.
      missing_roles = _CONTROL_PLANE_SECRET_MIN_REQUIRED_ROLES - roles
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

    command_string = 'gcloud '
    if self.ReleaseTrack() != base.ReleaseTrack.GA:
      command_string += self.ReleaseTrack().prefix + ' '
    command_string += 'events brokers create'
    log.status.Print('Initialized cluster [{}] for Cloud Run eventing with '
                     'key [{}] for service account [{}]. '
                     'Next, create a broker in the namespace(s) you plan to '
                     'use via `{}`.'.format(
                         args.CONCEPTS.cluster.Parse().Name(),
                         key_ref.Name(),
                         service_account_ref.Name(),
                         command_string))
