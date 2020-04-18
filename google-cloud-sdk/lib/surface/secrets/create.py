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
"""Create a new secret."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.secrets import api as secrets_api
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.secrets import args as secrets_args
from googlecloudsdk.command_lib.secrets import log as secrets_log
from googlecloudsdk.command_lib.secrets import util as secrets_util
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  r"""Create a new secret.

  Create a secret with the given name and creates a secret version with the
  given data, if any. If a secret already exists with the given name, this
  command will return an error.

  ## EXAMPLES

  Create a secret with an automatic replication policy without creating any
  versions:

    $ {command} my-secret --replication-policy=automatic

  Create a new secret named 'my-secret' with an automatic replication policy
  and data from a file:

    $ {command} my-secret --data-file=/tmp/secret
    --replication-policy=automatic

  Create a new secret named 'my-secret' in 'us-central1' with data from a file:

    $ {command} my-secret --data-file=/tmp/secret
    --replication-policy=user-managed \
        --locations=us-central1

  Create a new secret named 'my-secret' in 'us-central1' and 'us-east1' with
  the value "s3cr3t":

    $ echo "s3cr3t" | {command} my-secret --data-file=- \
        --replication-policy=user-managed --locations=us-central1,us-east1
  """

  EMPTY_DATA_FILE_MESSAGE = (
      'The value provided for --data-file is the empty string. This can happen '
      'if you pass or pipe a variable that is undefined. Please verify that '
      'the --data-file flag is not the empty string. If you are not providing '
      'secret data, omit the --data-file flag.')

  MISSING_POLICY_MESSAGE = (
      'The --replication-policy flag is required. Valid values are "automatic"'
      ' and "user-managed".')

  INVALID_POLICY_MESSAGE = (
      'The value provided for --replication-policy is invalid. Valid values '
      'are "automatic" and "user-managed".')

  INVALID_POLICY_PROP_MESSAGE = (
      'Cannot use the secrets/replication-policy property because its value is'
      ' invalid. Please either set it to a valid value ("automatic" or '
      '"user-managed") or override it for this command by using the '
      '--replication-policy flag.')

  MANAGED_BUT_NO_LOCATIONS_MESSAGE = (
      'If --replication-policy is user-managed then --locations must also be '
      'provided. Please set the desired storage regions in --locations or the '
      'secrets/locations property. For an automatic replication policy, please'
      ' set --replication-policy or the secrets/replication-policy property to'
      ' "automatic".')

  AUTOMATIC_AND_LOCATIONS_MESSAGE = (
      'If --replication-policy is "automatic" then --locations are not '
      'allowed. Please remove the --locations flag or set the '
      '--replication-policy to "user-managed".')

  AUTOMATIC_PROP_AND_LOCATIONS_MESSAGE = (
      'The secrets/replication-policy property is "automatic" and not '
      'overriden so --locations are not allowed. Please remove the --locations'
      ' flag or set the replication-policy to "user-managed".')

  AUTOMATIC_AND_LOCATIONS_PROP_MESSAGE = (
      'Cannot create a secret with an "automatic" replication policy if the '
      'secrets/locations property is set. Please either use a "user-managed" '
      'replication policy or unset secrets/locations.')

  @staticmethod
  def Args(parser):
    secrets_args.AddSecret(
        parser, purpose='to create', positional=True, required=True)
    secrets_args.AddLocations(parser, resource='secret')
    secrets_args.AddDataFile(parser)
    secrets_args.AddPolicy(parser)
    labels_util.AddCreateLabelsFlags(parser)

  def Run(self, args):
    messages = secrets_api.GetMessages(
        version=secrets_util.GetVersionFromReleasePath(self.ReleaseTrack()))
    secret_ref = args.CONCEPTS.secret.Parse()
    data = secrets_util.ReadFileOrStdin(args.data_file)
    labels = labels_util.ParseCreateArgs(args, messages.Secret.LabelsValue)
    replication_policy = args.replication_policy
    if not replication_policy:
      replication_policy = properties.VALUES.secrets.replication_policy.Get()

    if not replication_policy:
      raise exceptions.RequiredArgumentException('replication-policy',
                                                 self.MISSING_POLICY_MESSAGE)
    if replication_policy not in {'user-managed', 'automatic'}:
      if args.replication_policy:
        raise exceptions.InvalidArgumentException('replication-policy',
                                                  self.INVALID_POLICY_MESSAGE)
      raise exceptions.InvalidArgumentException(
          'replication-policy', self.INVALID_POLICY_PROP_MESSAGE)

    locations = args.locations
    if not locations:
      # if locations weren't given, try to get them from properties
      locations = properties.VALUES.secrets.locations.Get()
      if locations:
        locations = locations.split(',')
    if replication_policy == 'user-managed' and not locations:
      raise exceptions.RequiredArgumentException(
          'locations', self.MANAGED_BUT_NO_LOCATIONS_MESSAGE)
    if replication_policy == 'automatic':
      if args.locations:
        # check args.locations separately from locations because we have
        # different error messages depending on whether the user used the
        # --locations flag or the secrets/locations property
        if args.replication_policy:
          raise exceptions.InvalidArgumentException(
              'locations', self.AUTOMATIC_AND_LOCATIONS_MESSAGE)
        raise exceptions.InvalidArgumentException(
            'locations', self.AUTOMATIC_PROP_AND_LOCATIONS_MESSAGE)
      if locations:
        raise exceptions.InvalidArgumentException(
            'replication-policy', self.AUTOMATIC_AND_LOCATIONS_PROP_MESSAGE)
      locations = []

    # Differentiate between the flag being provided with an empty value and the
    # flag being omitted. See b/138796299 for info.
    if args.data_file == '':  # pylint: disable=g-explicit-bool-comparison
      raise exceptions.BadFileException(self.EMPTY_DATA_FILE_MESSAGE)
    # Create the secret
    response = secrets_api.Secrets(
        version=secrets_util.GetVersionFromReleasePath(
            self.ReleaseTrack())).Create(
                secret_ref,
                labels=labels,
                locations=locations,
                policy=replication_policy)

    if data:
      version = secrets_api.Secrets(
          version=secrets_util.GetVersionFromReleasePath(
              self.ReleaseTrack())).AddVersion(secret_ref, data)
      version_ref = secrets_args.ParseVersionRef(version.name)
      secrets_log.Versions().Created(version_ref)
    else:
      secrets_log.Secrets().Created(secret_ref)

    return response


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  r"""Create a new secret.

  Create a secret with the given name and creates a secret version with the
  given data, if any. If a secret already exists with the given name, this
  command will return an error.

  ## EXAMPLES

  Create a secret with an automatic replication policy without creating any
  versions:

    $ {command} my-secret --replication-policy=automatic

  Create a new secret named 'my-secret' with an automatic replication policy
  and data from a file:

    $ {command} my-secret --data-file=/tmp/secret
    --replication-policy=automatic

  Create a new secret named 'my-secret' in 'us-central1' with data from a file:

    $ {command} my-secret --data-file=/tmp/secret
    --replication-policy=user-managed \
        --locations=us-central1

  Create a new secret named 'my-secret' in 'us-central1' and 'us-east1' with
  the value "s3cr3t":

    $ echo "s3cr3t" | {command} my-secret --data-file=- \
        --replication-policy=user-managed --locations=us-central1,us-east1
  """

  @staticmethod
  def Args(parser):
    secrets_args.AddBetaSecret(
        parser, purpose='to create', positional=True, required=True)
    secrets_args.AddLocations(parser, resource='secret')
    secrets_args.AddDataFile(parser)
    secrets_args.AddPolicy(parser)
    labels_util.AddCreateLabelsFlags(parser)
