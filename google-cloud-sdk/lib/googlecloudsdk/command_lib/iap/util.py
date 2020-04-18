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

"""Utils for IAP commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.iap import util as iap_api
from googlecloudsdk.calliope import exceptions as calliope_exc
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.command_lib.iap import exceptions as iap_exc
from googlecloudsdk.core import properties


APP_ENGINE_RESOURCE_TYPE = 'app-engine'
BACKEND_SERVICES_RESOURCE_TYPE = 'backend-services'
WEB_RESOURCE_TYPE = 'iap_web'
COMPUTE_RESOURCE_TYPE = 'compute'
ORG_RESOURCE_TYPE = 'organization'
FOLDER_RESOURCE_TYPE = 'folder'
RESOURCE_TYPE_ENUM = (APP_ENGINE_RESOURCE_TYPE, BACKEND_SERVICES_RESOURCE_TYPE)
SETTING_RESOURCE_TYPE_ENUM = (APP_ENGINE_RESOURCE_TYPE, WEB_RESOURCE_TYPE,
                              COMPUTE_RESOURCE_TYPE, ORG_RESOURCE_TYPE,
                              FOLDER_RESOURCE_TYPE)


def AddIapIamResourceArgs(parser):
  """Adds flags for an IAP IAM resource.

  Args:
    parser: An argparse.ArgumentParser-like object. It is mocked out in order to
      capture some information, but behaves like an ArgumentParser.
  """
  group = parser.add_group()
  group.add_argument(
      '--resource-type',
      choices=RESOURCE_TYPE_ENUM,
      help='Resource type of the IAP IAM resource.')
  group.add_argument(
      '--service',
      help='Service name.')
  group.add_argument(
      '--version',
      help='Service version. Should only be specified with '
           '`--resource-type=app-engine`.')


def AddIapResourceArgs(parser):
  """Adds flags for an IAP resource.

  Args:
    parser: An argparse.ArgumentParser-like object. It is mocked out in order to
      capture some information, but behaves like an ArgumentParser.
  """
  group = parser.add_group()
  group.add_argument(
      '--resource-type',
      required=True,
      choices=RESOURCE_TYPE_ENUM,
      help='Resource type of the IAP resource.')
  group.add_argument(
      '--service',
      help='Service name. Required with `--resource-type=backend-services`.')


def AddIapSettingArg(parser):
  """Adds flags for an IAP settings resource.

  Args:
    parser: An argparse.ArgumentParser-like object. It is mocked out in order to
      capture some information, but behaves like an ArgumentParser.
  """
  group = parser.add_group()
  group.add_argument('--organization', help='Organization ID.')
  group.add_argument('--folder', help='Folder ID.')
  group.add_argument('--project', help='Project ID.')
  group.add_argument(
      '--resource-type',
      choices=SETTING_RESOURCE_TYPE_ENUM,
      help='Resource type of the IAP resource.')
  group.add_argument(
      '--service',
      help='Service name. Required when resource type is ``app-engine'', optional when resource type is ``compute''.'
  )
  group.add_argument(
      '--version',
      help='Version name. Optional when resource type is ``app-engine''.')


def AddOauthClientArgs(parser):
  """Adds OAuth client args.

  Args:
    parser: An argparse.ArgumentParser-like object. It is mocked out in order to
      capture some information, but behaves like an ArgumentParser.
  """
  group = parser.add_group()
  group.add_argument(
      '--oauth2-client-id',
      required=True,
      help='OAuth 2.0 client ID to use.')
  group.add_argument(
      '--oauth2-client-secret',
      required=True,
      help='OAuth 2.0 client secret to use.')


def AddAddIamPolicyBindingArgs(parser):
  # TODO(b/123070972) Add completers
  iam_util.AddArgsForAddIamPolicyBinding(
      parser,
      add_condition=True)


def AddRemoveIamPolicyBindingArgs(parser):
  # TODO(b/123070972) Add completers
  iam_util.AddArgsForRemoveIamPolicyBinding(
      parser,
      add_condition=True)


def AddIAMPolicyFileArg(parser):
  """Adds flags for an IAM policy file.

  Args:
    parser: An argparse.ArgumentParser-like object. It is mocked out in order to
      capture some information, but behaves like an ArgumentParser.
  """
  parser.add_argument(
      'policy_file', help='JSON or YAML file containing the IAM policy.')


def AddIapSettingFileArg(parser):
  """Add flags for the IAP setting file.

  Args:
    parser: An argparse.ArgumentParser-like object. It is mocked out in order to
      capture some information, but behaves like an ArgumentParser.
  """
  parser.add_argument(
      'setting_file',
      help="""JSON or YAML file containing the IAP resource settings.

       JSON example:
         {
           "access_settings" : {
             "oauth_settings" : {
                "login_hint" : {
                   "value": "test_hint"
                }
             },
             "gcip_settings" : {
                "tenant_ids": ["tenant1-p9puj", "tenant2-y8rxc"],
                "login_page_uri" : {
                   "value" : "https://test.com/?apiKey=abcd_efgh"
                }
             },
             "cors_settings": {
                "allow_http_options" : {
                   "value": true
                }
             }
          },
          "application_settings" : {
             "csm_settings" : {
               "rctoken_aud" : {
                  "value" : "test_aud"
               }
             }
          }
        }

       YAML example:
       accessSettings :
          oauthSettings:
            loginHint: test_hint
          gcipSettings:
            tenantIds:
            - tenant1-p9puj
            - tenant2-y8rxc
            loginPageUri: https://test.com/?apiKey=abcd_efgh
          corsSettings:
            allowHttpOptions: true
       applicationSettings:
          csmSettings:
            rctokenAud: test_aud""")


def ParseIapIamResource(release_track, args):
  """Parse an IAP IAM resource from the input arguments.

  Args:
    release_track: base.ReleaseTrack, release track of command.
    args: an argparse namespace. All the arguments that were provided to this
      command invocation.

  Raises:
    calliope_exc.InvalidArgumentException: if a provided argument does not apply
        to the specified resource type.
    iap_exc.InvalidIapIamResourceError: if an IapIamResource could not be parsed
        from the arguments.

  Returns:
    The specified IapIamResource
  """
  project = properties.VALUES.core.project.GetOrFail()
  if not args.resource_type:
    if args.service:
      raise calliope_exc.InvalidArgumentException(
          '--service',
          '`--service` cannot be specified without `--resource-type`.')
    if args.version:
      raise calliope_exc.InvalidArgumentException(
          '--version',
          '`--version` cannot be specified without `--resource-type`.')
    return iap_api.IAPWeb(
        release_track,
        project)
  elif args.resource_type == APP_ENGINE_RESOURCE_TYPE:
    if args.service and args.version:
      return iap_api.AppEngineServiceVersion(
          release_track,
          project,
          args.service,
          args.version)
    elif args.service:
      return iap_api.AppEngineService(
          release_track,
          project,
          args.service)
    if args.version:
      raise calliope_exc.InvalidArgumentException(
          '--version',
          '`--version` cannot be specified without `--service`.')
    return iap_api.AppEngineApplication(
        release_track,
        project)
  elif args.resource_type == BACKEND_SERVICES_RESOURCE_TYPE:
    if args.version:
      raise calliope_exc.InvalidArgumentException(
          '--version',
          '`--version` cannot be specified for '
          '`--resource-type=backend-services`.')
    if args.service:
      return iap_api.BackendService(
          release_track,
          project,
          args.service)
    return iap_api.BackendServices(
        release_track,
        project)

  # This shouldn't be reachable, based on the IAP IAM resource parsing logic.
  raise iap_exc.InvalidIapIamResourceError('Could not parse IAP IAM resource.')


def ParseIapResource(release_track, args):
  """Parse an IAP resource from the input arguments.

  Args:
    release_track: base.ReleaseTrack, release track of command.
    args: an argparse namespace. All the arguments that were provided to this
      command invocation.

  Raises:
    calliope_exc.InvalidArgumentException: if `--version` was specified with
        resource type 'backend-services'.
    iap_exc.InvalidIapIamResourceError: if an IapIamResource could not be parsed
        from the arguments.

  Returns:
    The specified IapIamResource
  """
  project = properties.VALUES.core.project.GetOrFail()
  if args.resource_type:
    if args.resource_type == APP_ENGINE_RESOURCE_TYPE:
      if args.service:
        raise calliope_exc.InvalidArgumentException(
            '--service',
            '`--service` cannot be specified for '
            '`--resource-type=app-engine`.')
      return iap_api.AppEngineApplication(
          release_track,
          project)
    elif args.resource_type == BACKEND_SERVICES_RESOURCE_TYPE:
      if not args.service:
        raise calliope_exc.RequiredArgumentException(
            '--service',
            '`--service` must be specified for '
            '`--resource-type=backend-services`.')
      return iap_api.BackendService(
          release_track,
          project,
          args.service)

  raise iap_exc.InvalidIapIamResourceError('Could not parse IAP resource.')


def ParseIapSettingsResource(release_track, args):
  """Parse an IAP setting resource from the input arguments.

  Args:
    release_track: base.ReleaseTrack, release track of command.
    args: an argparse namespace. All the arguments that were provided to this
      command invocation.

  Raises:
    calliope_exc.InvalidArgumentException: if `--version` was specified with
        resource type 'backend-services'.

  Returns:
    The specified IapSettingsResource
  """
  if args.organization:
    if args.resource_type:
      raise calliope_exc.InvalidArgumentException(
          '--resource-type',
          '`--resource-type` should not be specified at organization level')
    if args.project:
      raise calliope_exc.InvalidArgumentException(
          '--project',
          '`--project` should not be specified at organization level')
    return iap_api.IapSettingsResource(
        release_track, 'organizations/{0}'.format(args.organization))
  if args.folder:
    if args.resource_type:
      raise calliope_exc.InvalidArgumentException(
          '--resource-type',
          '`--resource-type` should not be specified at folder level')
    if args.project:
      raise calliope_exc.InvalidArgumentException(
          '--project', '`--project` should not be specified at folder level')
    return iap_api.IapSettingsResource(release_track,
                                       'folders/{0}'.format(args.folder))
  if args.project:
    if not args.resource_type:
      return iap_api.IapSettingsResource(release_track,
                                         'projects/{0}'.format(args.project))
    else:
      if args.resource_type == WEB_RESOURCE_TYPE:
        return iap_api.IapSettingsResource(
            release_track, 'projects/{0}/iap_web'.format(args.project))
      elif args.resource_type == APP_ENGINE_RESOURCE_TYPE:
        if not args.service:
          return iap_api.IapSettingsResource(
              release_track, 'projects/{0}/iap_web/appengine-{1}'.format(
                  args.project, args.project))
        else:
          if args.version:
            return iap_api.IapSettingsResource(
                release_track,
                'projects/{0}/iap_web/appengine-{1}/services/{2}/versions/{3}'
                .format(args.project, args.project, args.service, args.version))
          else:
            return iap_api.IapSettingsResource(
                release_track,
                'projects/{0}/iap_web/appengine-{1}/services/{2}'.format(
                    args.project, args.project, args.service))
      elif args.resource_type == COMPUTE_RESOURCE_TYPE:
        if args.service:
          return iap_api.IapSettingsResource(
              release_track, 'projects/{0}/iap_web/compute/services/{1}'.format(
                  args.project, args.service))
        else:
          return iap_api.IapSettingsResource(
              release_track,
              'projects/{0}/iap_web/compute'.format(args.project))
      else:
        raise iap_exc.InvalidIapIamResourceError(
            'Unsupported IAP settings resource type.')

  raise iap_exc.InvalidIapIamResourceError(
      'Could not parse IAP settings resource.')
