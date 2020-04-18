# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Command for labels update to images."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.images import flags as images_flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION':
        '*{command}* updates labels for a Google Compute image.',
    'EXAMPLES':
        """\
      To update labels ``k0'' and ``k1'' and remove labels with key ``k3'', run:

        $ {command} example-image --update-labels=k0=value1,k1=value2 --remove-labels=k3

        k0 and k1 will be added as new labels if not already present.

      Labels can be used to identify the image and to filter them like:

        $ {parent_command} list --filter='labels.k1:value2'

      To list only the labels when describing a resource, use --format:

        $ {parent_command} describe example-image --format='default(labels)'

    """,
}


def _Args(cls, parser, patch_enable=False):
  """Set Args based on Release Track."""
  cls.DISK_IMAGE_ARG = images_flags.MakeDiskImageArg(plural=False)
  cls.DISK_IMAGE_ARG.AddArgument(parser, operation_type='update')
  labels_util.AddUpdateLabelsFlags(parser)

  if patch_enable:
    parser.add_argument(
        '--description',
        help=('An optional text description for the image being created.'))

    parser.add_argument(
        '--family',
        help=('Family of the image. When creating an instance or disk, '
              'specifying a family will cause the latest non-deprecated image '
              'in the family to be used.')
    )


@base.ReleaseTracks(base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update a Google Compute Engine image."""

  DISK_IMAGE_ARG = None
  detailed_help = DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    _Args(cls, parser, False)

  def Run(self, args):
    return self._Run(args, False)

  def _Run(self, args, patch_enable=False):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = holder.client.messages

    image_ref = self.DISK_IMAGE_ARG.ResolveAsResource(
        args, holder.resources,
        scope_lister=flags.GetDefaultScopeLister(client))

    requests = []
    result = None

    # check if need to update labels
    if patch_enable:
      # Throws a different error message.
      labels_diff = labels_util.Diff.FromUpdateArgs(args)
    else:
      labels_diff = labels_util.GetAndValidateOpsFromArgs(args)

    if labels_diff.MayHaveUpdates():
      image = holder.client.apitools_client.images.Get(
          messages.ComputeImagesGetRequest(**image_ref.AsDict()))
      labels_update = labels_diff.Apply(
          messages.GlobalSetLabelsRequest.LabelsValue, image.labels)

      if labels_update.needs_update:
        request = messages.ComputeImagesSetLabelsRequest(
            project=image_ref.project,
            resource=image_ref.image,
            globalSetLabelsRequest=
            messages.GlobalSetLabelsRequest(
                labelFingerprint=image.labelFingerprint,
                labels=labels_update.labels))

        requests.append((client.apitools_client.images, 'SetLabels', request))

    if patch_enable:
      should_patch = False
      image_resource = messages.Image()

      if args.IsSpecified('family'):
        image_resource.family = args.family
        should_patch = True

      if args.IsSpecified('description'):
        image_resource.description = args.description
        should_patch = True

      if should_patch:
        request = messages.ComputeImagesPatchRequest(
            project=image_ref.project,
            imageResource=image_resource,
            image=image_ref.Name())
        requests.append((client.apitools_client.images, 'Patch', request))

    errors_to_collect = []
    result = client.BatchRequests(requests, errors_to_collect)
    if errors_to_collect:
      raise exceptions.MultiError(errors_to_collect)
    if result:
      log.status.Print('Updated [{0}].'.format(image_ref))

    return result


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(Update):
  """Update Google Compute Engine images."""

  @classmethod
  def Args(cls, parser):
    _Args(cls, parser, patch_enable=True)

  def Run(self, args):
    return self._Run(args, patch_enable=True)
