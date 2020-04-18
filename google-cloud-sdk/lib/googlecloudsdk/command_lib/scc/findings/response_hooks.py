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
"""Declarative Response Hooks for Cloud SCC's Finding responses."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


def ExtractSecurityMarksFromResponse(response, args):
  """Returns security marks from finding response."""
  del args
  list_finding_response = list(response)
  assert len(list_finding_response) == 1, (
      "ListFindingResponse must only return one finding since it is "
      "filtered by Finding Name.")
  for finding_result in list_finding_response:
    return finding_result.finding.securityMarks
