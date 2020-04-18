# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Export image command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import daisy_utils
from googlecloudsdk.api_lib.compute import image_utils
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.images import flags
from googlecloudsdk.core import properties

_OUTPUT_FILTER = ['[Daisy', '[image-export', '  image', 'ERROR']


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Export(base.CreateCommand):
  """Export a Google Compute Engine image."""

  @staticmethod
  def Args(parser):
    image_group = parser.add_mutually_exclusive_group(required=True)

    image_group.add_argument(
        '--image',
        help='The name of the disk image to export.',
    )
    image_group.add_argument(
        '--image-family',
        help=('The family of the disk image to be exported. When a family '
              'is used instead of an image, the latest non-deprecated image '
              'associated with that family is used.'),
    )
    image_utils.AddImageProjectFlag(parser)

    flags.compute_flags.AddZoneFlag(
        parser, 'image', 'export',
        explanation='The zone to use when exporting the image.')

    parser.add_argument(
        '--destination-uri',
        required=True,
        help=('The Google Cloud Storage URI destination for '
              'the exported virtual disk file.'),
    )

    # Export format can take more values than what we list here in the help.
    # However, we don't want to suggest formats that will likely never be used,
    # so we list common ones here, but don't prevent others from being used.
    parser.add_argument(
        '--export-format',
        help=('Specify the format to export to, such as '
              '`vmdk`, `vhdx`, `vpc`, or `qcow2`.'),
    )

    parser.add_argument(
        '--network',
        help=('The name of the network in your project to use for the image '
              'export. The network must have access to Google Cloud Storage. '
              'If not specified, the network named `default` is used.'),
    )

    parser.add_argument(
        '--subnet',
        help=('Name of the subnetwork in your project to use for the image '
              'export. If the network resource is in legacy mode, do not '
              'provide this property. If the network is in auto subnet mode, '
              'providing the subnetwork is optional. If the network is in '
              'custom subnet mode, then this field should be specified.'),
    )

    daisy_utils.AddCommonDaisyArgs(parser)

    parser.display_info.AddCacheUpdater(flags.ImagesCompleter)

  def Run(self, args):
    tags = ['gce-daisy-image-export']
    export_args = []
    daisy_utils.AppendNetworkAndSubnetArgs(args, export_args)

    daisy_utils.AppendArg(export_args, 'zone',
                          properties.VALUES.compute.zone.Get())
    daisy_utils.AppendArg(export_args, 'scratch_bucket_gcs_path',
                          'gs://{0}/'.format(self._GetDaisyBucket(args)))
    daisy_utils.AppendArg(export_args, 'timeout',
                          '{}s'.format(daisy_utils.GetDaisyTimeout(args)))

    daisy_utils.AppendArg(export_args, 'client_id', 'gcloud')
    source_image = self._GetSourceImage(args.image, args.image_family,
                                        args.image_project)
    daisy_utils.AppendArg(export_args, 'source_image', source_image)
    daisy_utils.AppendArg(export_args, 'destination_uri', args.destination_uri)
    if args.export_format:
      daisy_utils.AppendArg(export_args, 'format', args.export_format.lower())

    return self._RunImageExport(args, export_args, tags, _OUTPUT_FILTER)

  def _RunImageExport(self, args, export_args, tags, output_filter):
    return daisy_utils.RunImageExport(args, export_args, tags, _OUTPUT_FILTER)

  def _GetSourceImage(self, image, image_family, image_project):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    resources = holder.resources
    project = properties.VALUES.core.project.GetOrFail()
    image_expander = image_utils.ImageExpander(client, resources)
    image = image_expander.ExpandImageFlag(
        user_project=project, image=image, image_family=image_family,
        image_project=image_project, return_image_resource=False)
    image_ref = resources.Parse(image[0], collection='compute.images')
    return image_ref.RelativeName()

  @staticmethod
  def _GetDaisyBucket(args):
    storage_client = storage_api.StorageClient()
    bucket_location = storage_client.GetBucketLocationForFile(
        args.destination_uri)
    bucket_name = daisy_utils.GetDaisyBucketName(bucket_location)
    storage_client.CreateBucketIfNotExists(bucket_name,
                                           location=bucket_location)
    return bucket_name


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ExportBeta(Export):
  """Export a Google Compute Engine image for Beta release track."""

  @classmethod
  def Args(cls, parser):
    super(ExportBeta, cls).Args(parser)
    daisy_utils.AddExtraCommonDaisyArgs(parser)

  def _RunImageExport(self, args, export_args, tags, output_filter):
    return daisy_utils.RunImageExport(args, export_args, tags, _OUTPUT_FILTER,
                                      args.docker_image_tag)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ExportAlpha(ExportBeta):
  """Export a Google Compute Engine image for Alpha release track."""


Export.detailed_help = {
    'brief':
        'Export a Compute Engine image',
    'DESCRIPTION':
        """\
        *{command}* exports virtual disk images from Compute Engine.

        By default, images are exported in the Compute Engine format,
        which is a 'disk.raw' file that is tarred and gzipped.

        The `--export-format` flag exports the image to a format supported
        by QEMU using qemu-img. Valid formats include 'vmdk', 'vhdx', 'vpc',
        'vdi', and 'qcow2'.
        """,
    'EXAMPLES':
        """\
        To export a VMDK file 'my-image' from a project 'my-project' to a
        Cloud Storage bucket 'my-bucket', run:

          $ {command} --image=my-image --destination-uri=gs://my-bucket/my-image.vmdk --image=my-image --format=vmdk --project=my-project
    """
}
