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
"""Import backend service command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.backend_services import backend_services_utils
from googlecloudsdk.command_lib.compute.backend_services import flags
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core import yaml_validator
from googlecloudsdk.core.console import console_io


DETAILED_HELP = {
    'DESCRIPTION':
        """\
        Imports a backend service's configuration to a file.
        This configuration can be imported at a later time.
        """,
    'EXAMPLES':
        """\
        A backend service can be imported by running:

          $ {command} NAME --source=<path-to-file> --global
        """
}


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class Import(base.UpdateCommand):
  """Import a backend service.

  If the specified backend service already exists, it will be overwritten.
  Otherwise, a new backend service will be created.
  To edit a backend service you can export the backend service to a file,
  edit its configuration, and then import the new configuration.
  """

  detailed_help = DETAILED_HELP

  @classmethod
  def GetApiVersion(cls):
    """Returns the API version based on the release track."""
    if cls.ReleaseTrack() == base.ReleaseTrack.ALPHA:
      return 'alpha'
    elif cls.ReleaseTrack() == base.ReleaseTrack.BETA:
      return 'beta'
    return 'v1'

  @classmethod
  def GetSchemaPath(cls, for_help=False):
    """Returns the resource schema path."""
    return export_util.GetSchemaPath(
        'compute', cls.GetApiVersion(), 'BackendService', for_help=for_help)

  @classmethod
  def Args(cls, parser):
    flags.GLOBAL_REGIONAL_BACKEND_SERVICE_ARG.AddArgument(
        parser, operation_type='import')
    export_util.AddImportFlags(parser, cls.GetSchemaPath(for_help=True))

  def SendPatchRequest(self, client, backend_service_ref, replacement):
    """Send Backend Services patch request."""
    if backend_service_ref.Collection() == 'compute.regionBackendServices':
      return client.apitools_client.regionBackendServices.Patch(
          client.messages.ComputeRegionBackendServicesPatchRequest(
              project=backend_service_ref.project,
              region=backend_service_ref.region,
              backendService=backend_service_ref.Name(),
              backendServiceResource=replacement))

    return client.apitools_client.backendServices.Patch(
        client.messages.ComputeBackendServicesPatchRequest(
            project=backend_service_ref.project,
            backendService=backend_service_ref.Name(),
            backendServiceResource=replacement))

  def SendInsertRequest(self, client, backend_service_ref, backend_service):
    """Send Backend Services insert request."""
    if backend_service_ref.Collection() == 'compute.regionBackendServices':
      return client.apitools_client.regionBackendServices.Insert(
          client.messages.ComputeRegionBackendServicesInsertRequest(
              project=backend_service_ref.project,
              region=backend_service_ref.region,
              backendService=backend_service))

    return client.apitools_client.backendServices.Insert(
        client.messages.ComputeBackendServicesInsertRequest(
            project=backend_service_ref.project,
            backendService=backend_service))

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    backend_service_ref = (
        flags.GLOBAL_REGIONAL_BACKEND_SERVICE_ARG.ResolveAsResource(
            args,
            holder.resources,
            scope_lister=compute_flags.GetDefaultScopeLister(client)))

    data = console_io.ReadFromFileOrStdin(args.source or '-', binary=False)

    try:
      backend_service = export_util.Import(
          message_type=client.messages.BackendService,
          stream=data,
          schema_path=self.GetSchemaPath())
    except yaml_validator.ValidationError as e:
      raise exceptions.ToolException(e.message)

    # Get existing backend service.
    try:
      backend_service_old = backend_services_utils.SendGetRequest(
          client, backend_service_ref)
    except apitools_exceptions.HttpError as error:
      if error.status_code != 404:
        raise error
      # Backend service does not exist, create a new one.
      return self.SendInsertRequest(client, backend_service_ref,
                                    backend_service)

    # No change, do not send requests to server.
    if backend_service_old == backend_service:
      return

    console_io.PromptContinue(
        message=('Backend Service [{0}] will be overwritten.').format(
            backend_service_ref.Name()),
        cancel_on_no=True)

    # populate id and fingerprint fields. These two fields are manually
    # removed from the schema files.
    backend_service.id = backend_service_old.id
    backend_service.fingerprint = backend_service_old.fingerprint

    # Unspecified fields are assumed to be cleared.
    cleared_fields = []
    if hasattr(backend_service, 'securitySettings') is None:
      cleared_fields.append('securitySettings')
    if hasattr(backend_service, 'localityLbPolicy') is None:
      cleared_fields.append('localityLbPolicy')
    if hasattr(backend_service, 'circuitBreakers') is None:
      cleared_fields.append('circuitBreakers')
    if hasattr(backend_service, 'consistentHash') is None:
      cleared_fields.append('consistentHash')
    if hasattr(backend_service, 'outlierDetection') is None:
      cleared_fields.append('outlierDetection')

    with client.apitools_client.IncludeFields(cleared_fields):
      return self.SendPatchRequest(client, backend_service_ref, backend_service)
