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
"""services api-keys create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.services import apikeys
from googlecloudsdk.api_lib.services import services_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.services import common_flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties

OP_BASE_CMD = 'gcloud services operations '
OP_WAIT_CMD = OP_BASE_CMD + 'wait {0}'


class Create(base.CreateCommand):
  r"""Create an API key.

    ## EXAMPLES

    To create a key with display name and allowed ips specified:
    $ {command} --display-name="test name" \
        --allowed-ips=2620:15c:2c4:203:2776:1f90:6b3b:217,104.133.8.78

    To create a key with allowed referrers restriction:
    $ {command} \
        --allowed-referrers="https://www.example.com/*,http://sub.example.com/*"

    To create a key with allowed ios app bundle ids:
    $ {command} --allowed-bundle-ids=my.app

    To create a key with allowed android application:
    $ {command} \
        --allowed-application=sha1_fingerprint=foo1,package_name=bar.foo \
        --allowed-application=sha1_fingerprint=foo2,package_name=foo.bar

    To create a key with allowed api targets (service name only):
    $ {command} \
        --api-target=service=bar.service.com \
        --api-target=service=foo.service.com

    To create a keys with allowed api targets (service and methods are
    specified):

    $ {command} --flags-file=my-flags.yaml

        The content of 'my-flags.yaml' is as following:

        ```
          - --api-target:
              service:
                - "foo.service.com"
          - --api-target:
              service:
                - "bar.service.com"
              methods:
                - "foomethod"
                - "barmethod"
        ```
  """

  @staticmethod
  def Args(parser):
    common_flags.display_name_flag(parser=parser, suffix='to create')
    common_flags.add_key_create_args(parser)
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    """Run command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      None
    """
    project_id = properties.VALUES.core.project.GetOrFail()

    client = apikeys.GetClientInstance()
    messages = client.MESSAGES_MODULE

    key_proto = messages.V2alpha1ApiKey(
        restrictions=messages.V2alpha1Restrictions())
    if args.IsSpecified('display_name'):
      key_proto.displayName = args.display_name
    if args.IsSpecified('allowed_referrers'):
      key_proto.restrictions.browserKeyRestrictions = messages.V2alpha1BrowserKeyRestrictions(
          allowedReferrers=args.allowed_referrers)
    elif args.IsSpecified('allowed_ips'):
      key_proto.restrictions.serverKeyRestrictions = messages.V2alpha1ServerKeyRestrictions(
          allowedIps=args.allowed_ips)
    elif args.IsSpecified('allowed_bundle_ids'):
      key_proto.restrictions.iosKeyRestrictions = messages.V2alpha1IosKeyRestrictions(
          allowedBundleIds=args.allowed_bundle_ids)
    elif args.IsSpecified('allowed_application'):
      key_proto.restrictions.androidKeyRestrictions = messages.V2alpha1AndroidKeyRestrictions(
          allowedApplications=apikeys.GetAllowedAndroidApplications(
              args, messages))
    if args.IsSpecified('api_target'):
      key_proto.restrictions.apiTargets = apikeys.GetApiTargets(args, messages)
    request = messages.ApikeysProjectsKeysCreateRequest(
        parent=apikeys.GetParentResourceName(project_id),
        v2alpha1ApiKey=key_proto)
    op = client.projects_keys.Create(request)
    if not op.done:
      if args.async_:
        cmd = OP_WAIT_CMD.format(op.name)
        log.status.Print('Asynchronous operation is in progress... '
                         'Use the following command to wait for its '
                         'completion:\n {0}'.format(cmd))
        return op
      op = services_util.WaitOperation(op.name, apikeys.GetOperation)
    services_util.PrintOperationWithResponse(op)
