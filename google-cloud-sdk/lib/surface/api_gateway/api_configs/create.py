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

"""`gcloud api-gateway api-configs create` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import time

from googlecloudsdk.api_lib.api_gateway import api_configs as api_configs_client
from googlecloudsdk.api_lib.api_gateway import apis as apis_client
from googlecloudsdk.api_lib.api_gateway import operations as operations_client
from googlecloudsdk.api_lib.endpoints import services_util as endpoints
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.api_gateway import common_flags
from googlecloudsdk.command_lib.api_gateway import operations_util
from googlecloudsdk.command_lib.api_gateway import resource_args
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log
from googlecloudsdk.core.util import http_encoding

MAX_SERVICE_CONFIG_ID_LENGTH = 50


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Add a new config to an API."""

  detailed_help = {
      'DESCRIPTION':
          """\
          {description}

          NOTE: If the specified API does not exist it will be created.""",
      'EXAMPLES':
          """\
        To create an API config for the API 'my-api' with an OpenAPI spec, run:

          $ {command} my-config --api=my-api --openapi-spec=path/to/openapi_spec.yaml
        """,
  }

  @staticmethod
  def Args(parser):
    base.ASYNC_FLAG.AddToParser(parser)
    common_flags.AddDisplayNameArg(parser)
    labels_util.AddCreateLabelsFlags(parser)
    resource_args.AddApiConfigResourceArg(parser, 'created', positional=True)
    common_flags.AddBackendAuthServiceAccountFlag(parser)

    group = parser.add_group(mutex=True,
                             required=True,
                             help='Configuration files for the API.')
    group.add_argument(
        '--openapi-spec',
        help=('The OpenAPI v2 specification containing service '
              'configuration information, and API specification for the gateway'
              '.'))
    group.add_argument(
        '--grpc-files',
        type=arg_parsers.ArgList(),
        metavar='FILE',
        help=('Files describing the GRPC service. Google Service Configuration '
              'files in JSON or YAML formats as well as Proto '
              'descriptors should be listed.'))

  def Run(self, args):
    apis = apis_client.ApiClient()
    api_configs = api_configs_client.ApiConfigClient()
    ops = operations_client.OperationsClient()

    api_config_ref = args.CONCEPTS.api_config.Parse()
    api_ref = api_config_ref.Parent()

    service_name = common_flags.ProcessApiRefToEndpointsService(api_ref)

    # Check if OP service exists with Api name, create if not, activate it
    if not endpoints.DoesServiceExist(service_name):
      endpoints.CreateService(service_name, api_ref.projectsId)

    # Check to see if Api exists, create if not
    if not apis.DoesExist(api_ref):
      res = apis.Create(api_ref, service_name)
      operations_util.PrintOperationResult(
          res.name, ops,
          wait_string='Waiting for API [{}] to be created'.format(
              api_ref.Name()))

    # Create OP ServiceConfig and Rollout

    # Creating a suffix to avoid name collisions on ServiceConfig IDs.
    suffix = '-' + str(int(time.time()))
    length = MAX_SERVICE_CONFIG_ID_LENGTH - len(suffix)
    config_id = api_config_ref.Name()[:length] + suffix

    if args.openapi_spec:
      service_config_id = self.__PushOpenApiServiceFile(
          args.openapi_spec,
          service_name,
          api_config_ref.projectsId,
          config_id=config_id)
    else:
      service_config_id = self.__PushGrpcConfigFiles(
          args.grpc_files,
          service_name,
          api_config_ref.projectsId,
          config_id=config_id)
    rollout = endpoints.CreateRollout(service_config_id, service_name)

    # Create ApiConfig object using the service config and rollout
    # Only piece affected by async right now
    resp = api_configs.Create(api_config_ref,
                              rollout['rolloutId'],
                              labels=args.labels,
                              display_name=args.display_name,
                              backend_auth=args.backend_auth_service_account)

    wait = 'Waiting for API Config [{}] to be created for API [{}]'.format(
        api_config_ref.Name(), api_ref.Name())

    return operations_util.PrintOperationResult(
        resp.name,
        ops,
        service=api_configs.service,
        wait_string=wait,
        is_async=args.async_)

  def __PushOpenApiServiceFile(self, open_api_spec, service_name, project_id,
                               config_id):
    """Creates a new ServiceConfig in Service Management from OpenAPI spec.

    Args:
      open_api_spec: Spec to be pushed to Service Management
      service_name: Name of the service to push configs to
      project_id: Project the service belongs to
      config_id: ID to assign to the new ServiceConfig

    Returns:
      ServiceConfig Id

    Raises:
      BadFileException: If there is something wrong with the files
    """
    messages = endpoints.GetMessagesModule()
    file_types = messages.ConfigFile.FileTypeValueValuesEnum
    config_contents = endpoints.ReadServiceConfigFile(open_api_spec)

    config_dict = self.__ValidJsonOrYaml(open_api_spec, config_contents)
    if config_dict:
      if 'swagger' in config_dict:
        # Always use YAML for OpenAPI because JSON is a subset of YAML.
        config_file = self.__MakeConfigFileMessage(config_contents,
                                                   open_api_spec,
                                                   file_types.OPEN_API_YAML)
      elif 'openapi' in config_dict:
        raise calliope_exceptions.BadFileException(
            'API Gateway does not currently support OpenAPI v3 configurations.')
      else:
        raise calliope_exceptions.BadFileException(
            'The file {} is not a valid OpenAPI v2 configuration file.'.format(
                open_api_spec))
    else:
      raise calliope_exceptions.BadFileException(
          'OpenAPI files should be of JSON or YAML format')

    return self.__PushServiceConfigFiles(
        [config_file], service_name, project_id, config_id)

  def __PushGrpcConfigFiles(self, files, service_name, project_id, config_id):
    """Creates a new ServiceConfig in SerivceManagement from gRPC files.

    Args:
      files: Files to be pushed to Service Management
      service_name: Name of the service to push configs to
      project_id: Project the service belongs to
      config_id: ID to assign to the new ServiceConfig

    Returns:
      ServiceConfig Id

    Raises:
      BadFileException: If there is something wrong with the files
    """
    messages = endpoints.GetMessagesModule()
    file_types = messages.ConfigFile.FileTypeValueValuesEnum
    # TODO(b/77867100): remove .proto support and deprecation warning.
    give_proto_deprecate_warning = False
    config_files = []

    for config_file in files:
      config_contents = endpoints.ReadServiceConfigFile(config_file)

      config_dict = self.__ValidJsonOrYaml(config_file, config_contents)
      if config_dict:
        if config_dict.get('type') == 'google.api.Service':
          config_files.append(
              self.__MakeConfigFileMessage(config_contents, config_file,
                                           file_types.SERVICE_CONFIG_YAML))
        elif 'name' in config_dict:
          # This is a special case. If we have been provided a Google Service
          # Configuration file which has a service 'name' field, but no 'type'
          # field, we have to assume that this is a normalized service config,
          # and can be uploaded via the CreateServiceConfig API. Therefore,
          # we can short circute the process here.
          if len(files) > 1:
            raise calliope_exceptions.BadFileException(
                ('Ambiguous input. Found normalized service configuration in '
                 'file [{0}], but received multiple input files. To upload '
                 'normalized service config, please provide it separately from '
                 'other input files to avoid ambiguity.'
                ).format(config_file))

          return self. __PushServiceConfigFiles(
              files, service_name, project_id, config_id, normalized=True)
        else:
          raise calliope_exceptions.BadFileException(
              'The file {} is not a valid api configuration file'.format(
                  config_file))
      elif endpoints.IsProtoDescriptor(config_file):
        config_files.append(
            self.__MakeConfigFileMessage(config_contents, config_file,
                                         file_types.FILE_DESCRIPTOR_SET_PROTO))
      elif endpoints.IsRawProto(config_file):
        give_proto_deprecate_warning = True
        config_files.append(
            self.__MakeConfigFileMessage(config_contents, config_file,
                                         file_types.PROTO_FILE))
      else:
        raise calliope_exceptions.BadFileException(
            ('Could not determine the content type of file [{0}]. Supported '
             'extensions are .json .yaml .yml .pb and .descriptor'
            ).format(config_file))

    if give_proto_deprecate_warning:
      log.warning(
          'Support for uploading uncompiled .proto files is deprecated and '
          'will soon be removed. Use compiled descriptor sets (.pb) instead.\n')

    return self.__PushServiceConfigFiles(
        config_files, service_name, project_id, config_id)

  def __ValidJsonOrYaml(self, file_name, file_contents):
    """Whether or not this is a valid json or yaml file.

    Args:
      file_name: Name of the file
      file_contents: data for the file

    Returns:
      Boolean for whether or not this is a JSON or YAML

    Raises:
      BadFileException: File appears to be json or yaml but cannot be parsed.
    """
    if endpoints.FilenameMatchesExtension(file_name,
                                          ['.json', '.yaml', '.yml']):
      config_dict = endpoints.LoadJsonOrYaml(file_contents)
      if config_dict:
        return config_dict
      else:
        raise calliope_exceptions.BadFileException(
            'Could not read JSON or YAML from config file '
            '[{0}].'.format(file_name))
    else:
      return False

  def __PushServiceConfigFiles(self, files, service_name, project_id, config_id,
                               normalized=False):
    """Creates a new ServiceConfig in Service Management.

    Args:
      files: Files to be pushed to Service Management
      service_name: Name of the service to push configs to
      project_id: Project the service belongs to
      config_id: ID to assign to the new ServiceConfig
      normalized: Whether or not this is a normalized google service

    Returns:
      ServiceConfig Id
    """
    if normalized:
      config_contents = endpoints.ReadServiceConfigFile(files[0])
      push_config_result = endpoints.PushNormalizedGoogleServiceConfig(
          service_name,
          project_id,
          endpoints.LoadJsonOrYaml(config_contents),
          config_id=config_id)
      service_config_id = push_config_result.id
    else:
      push_config_result = endpoints.PushMultipleServiceConfigFiles(
          service_name, files, False, config_id=config_id)
      service_config_id = (
          endpoints.GetServiceConfigIdFromSubmitConfigSourceResponse(
              push_config_result))

    return service_config_id

  def __MakeConfigFileMessage(self, file_contents, filename, file_type):
    """Constructs a ConfigFile message from a config file.

    Args:
      file_contents: The contents of the config file.
      filename: The full path to the config file.
      file_type: FileTypeValueValuesEnum describing the type of config file.

    Returns:
      The constructed ConfigFile message.
    """

    messages = endpoints.GetMessagesModule()

    file_types = messages.ConfigFile.FileTypeValueValuesEnum
    if file_type != file_types.FILE_DESCRIPTOR_SET_PROTO:
      # File is human-readable text, not binary; needs to be encoded.
      file_contents = http_encoding.Encode(file_contents)
    return messages.ConfigFile(
        fileContents=file_contents,
        filePath=os.path.basename(filename),
        fileType=file_type,
    )
