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
"""Create public advertised prefix command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import public_advertised_prefixes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.public_advertised_prefixes import flags
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  r"""Creates a Google Compute Engine public advertised prefix.

  ## EXAMPLES

  To create a public advertised prefix:

    $ {command} my-public-advertised-prefix --range=120.120.10.0/24 \
      --dns-verification-ip=120.120.10.15
  """

  @staticmethod
  def Args(parser):
    flags.MakePublicAdvertisedPrefixesArg().AddArgument(parser)
    flags.AddCreatePapArgsToParser(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    pap_client = public_advertised_prefixes.PublicAdvertisedPrefixesClient(
        holder.client, holder.client.messages, holder.resources)
    pap_ref = flags.MakePublicAdvertisedPrefixesArg().ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client))

    result = pap_client.Create(
        pap_ref,
        ip_cidr_range=args.range,
        dns_verification_ip=args.dns_verification_ip,
        description=args.description)
    log.CreatedResource(pap_ref.Name(), 'public advertised prefix')
    return result
