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
"""Import URL maps command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.url_maps import flags
from googlecloudsdk.command_lib.compute.url_maps import url_maps_utils
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core import yaml_validator
from googlecloudsdk.core.console import console_io


def _DetailedHelp():
  return {
      'brief':
          'Import a URL map.',
      'DESCRIPTION':
          """\
          Imports a URL map's configuration to a file.
          """,
      'EXAMPLES':
          """\
          A URL map can be imported by running:

            $ {command} NAME --source=<path-to-file>
          """
  }


def _GetApiVersion(release_track):
  """Returns the API version based on the release track."""
  if release_track == base.ReleaseTrack.ALPHA:
    return 'alpha'
  elif release_track == base.ReleaseTrack.BETA:
    return 'beta'
  return 'v1'


def _GetSchemaPath(release_track, for_help=False):
  """Returns the resource schema path."""
  return export_util.GetSchemaPath(
      'compute', _GetApiVersion(release_track), 'UrlMap', for_help=for_help)


def _SendPatchRequest(client, url_map_ref, replacement):
  """Sends URL Map patch request."""
  if url_map_ref.Collection() == 'compute.regionUrlMaps':
    return client.apitools_client.regionUrlMaps.Patch(
        client.messages.ComputeRegionUrlMapsPatchRequest(
            project=url_map_ref.project,
            region=url_map_ref.region,
            urlMap=url_map_ref.Name(),
            urlMapResource=replacement))

  return client.apitools_client.urlMaps.Patch(
      client.messages.ComputeUrlMapsPatchRequest(
          project=url_map_ref.project,
          urlMap=url_map_ref.Name(),
          urlMapResource=replacement))


def _SendInsertRequest(client, url_map_ref, url_map):
  """Sends URL Map insert request."""
  if url_map_ref.Collection() == 'compute.regionUrlMaps':
    return client.apitools_client.regionUrlMaps.Insert(
        client.messages.ComputeRegionUrlMapsInsertRequest(
            project=url_map_ref.project,
            region=url_map_ref.region,
            urlMap=url_map))

  return client.apitools_client.urlMaps.Insert(
      client.messages.ComputeUrlMapsInsertRequest(
          project=url_map_ref.project, urlMap=url_map))


def _Run(args, holder, url_map_arg, release_track):
  """Issues requests necessary to import URL maps."""
  client = holder.client

  url_map_ref = url_map_arg.ResolveAsResource(
      args,
      holder.resources,
      default_scope=compute_scope.ScopeEnum.GLOBAL,
      scope_lister=compute_flags.GetDefaultScopeLister(client))

  data = console_io.ReadFromFileOrStdin(args.source or '-', binary=False)

  try:
    url_map = export_util.Import(
        message_type=client.messages.UrlMap,
        stream=data,
        schema_path=_GetSchemaPath(release_track))
  except yaml_validator.ValidationError as e:
    raise exceptions.ToolException(e.message)

  # Get existing URL map.
  try:
    url_map_old = url_maps_utils.SendGetRequest(client, url_map_ref)
  except apitools_exceptions.HttpError as error:
    if error.status_code != 404:
      raise error
    # Url Map does not exist, create a new one.
    return _SendInsertRequest(client, url_map_ref, url_map)

  # No change, do not send requests to server.
  if url_map_old == url_map:
    return

  console_io.PromptContinue(
      message=('Url Map [{0}] will be overwritten.').format(url_map_ref.Name()),
      cancel_on_no=True)

  # Populate id and fingerprint fields. These two fields are manually
  # removed from the schema files.
  url_map.id = url_map_old.id
  url_map.fingerprint = url_map_old.fingerprint

  return _SendPatchRequest(client, url_map_ref, url_map)


@base.ReleaseTracks(base.ReleaseTrack.GA,
                    base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class Import(base.UpdateCommand):
  """Import a URL map."""

  _include_l7_internal_load_balancing = True

  detailed_help = _DetailedHelp()
  URL_MAP_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.URL_MAP_ARG = flags.UrlMapArgument(
        include_l7_internal_load_balancing=cls
        ._include_l7_internal_load_balancing)
    cls.URL_MAP_ARG.AddArgument(parser, operation_type='import')
    export_util.AddImportFlags(
        parser, _GetSchemaPath(cls.ReleaseTrack(), for_help=True))

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    return _Run(args, holder, self.URL_MAP_ARG, self.ReleaseTrack())
