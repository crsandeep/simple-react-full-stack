# Lint as: python3
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
"""Certificate utilities for Privateca commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import random
import string

from googlecloudsdk.api_lib.privateca import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core.util import times


def GetCertificateBySerialNum(ca_ref, serial_num):
  """Obtains a certificate by serial num by filtering all certs in a CA.

  Args:
    ca_ref: The resource reference to the certificate authority.
    serial_num: The serial number to lookup the certificate by.

  Returns:
    The certificate message of the corresponding serial number. Ignores
    duplicate certificates.

  Raises:
    exceptions.InvalidArgumentError if there were no certificates with the
    specified ca and serial number.
  """
  cert_filter = 'certificate_description.subject_description.hex_serial_number:{}'.format(
      serial_num)
  client = base.GetClientInstance()
  messages = base.GetMessagesModule()

  response = client.projects_locations_certificateAuthorities_certificates.List(
      messages
      .PrivatecaProjectsLocationsCertificateAuthoritiesCertificatesListRequest(
          parent=ca_ref.RelativeName(), filter=cert_filter))

  if not response.certificates:
    raise exceptions.InvalidArgumentException(
        'serial number',
        'The serial number specified does not exist under the certificate authority [{}]]'
        .format(ca_ref.RelativeName()))

  return response.certificates[0]


def GenerateCertId():
  """Generate a certificate id with the date and two length 3 alphanum strings.

  E.G. YYYYMMDD-ABC-DEF.

  Returns:
    The generated certificate id string.
  """
  alphanum = string.ascii_uppercase + string.digits
  alphanum_rand1 = ''.join(random.choice(alphanum) for i in range(3))
  alphanum_rand2 = ''.join(random.choice(alphanum) for i in range(3))
  date_str = times.FormatDateTime(times.Now(), '%Y%m%d')
  return '{}-{}-{}'.format(date_str, alphanum_rand1, alphanum_rand2)
