# -*- coding: utf-8 -*- #
# Copyright 2020 Google Inc. All Rights Reserved.
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
"""`gcloud service-directory endpoints update` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.service_directory import endpoints
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.service_directory import flags
from googlecloudsdk.command_lib.service_directory import resource_args
from googlecloudsdk.command_lib.service_directory import util
from googlecloudsdk.core import log

_RESOURCE_TYPE = 'endpoint'
_ENDPOINT_METADATA_LIMIT = 512


class Update(base.UpdateCommand):
  """Update an endpoint."""

  detailed_help = {
      'EXAMPLES':
          """\
          To update a Service Directory endpoint, run:

            $ {command} my-endpoint --service=my-service --namespace=my-namespace --location=us-east1 --address=1.2.3.4 --port=5 --metadata=a=b,c=d
          """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddEndpointResourceArg(parser, 'to update.')
    flags.AddAddressFlag(parser)
    flags.AddPortFlag(parser)
    flags.AddMetadataFlag(parser, _RESOURCE_TYPE, _ENDPOINT_METADATA_LIMIT)

  def Run(self, args):
    client = endpoints.EndpointsClient()
    endpoint_ref = args.CONCEPTS.endpoint.Parse()
    metadata = util.ParseMetadataArg(args.metadata, _RESOURCE_TYPE)
    log.UpdatedResource(endpoint_ref.endpointsId, _RESOURCE_TYPE)

    return client.Update(endpoint_ref, args.address, args.port, metadata)
