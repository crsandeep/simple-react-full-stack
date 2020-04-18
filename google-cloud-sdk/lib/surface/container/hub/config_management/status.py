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
"""The command to get the status of Config Management Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.hub.features import base as feature_base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties

NA = 'NA'


class ConfigmanagementFeatureState(object):
  """feature state class stores nomos status."""

  def __init__(self, clusterName):
    self.name = clusterName
    self.status = NA
    self.last_synced_token = NA
    self.last_synced = NA
    self.sync_branch = NA


class Status(base.ListCommand):
  r"""Prints the status of all clusters with Configuration Management installed.

  This command prints the status of Config Management Feature
  resource in Hub.

  ## EXAMPLES

  Prints the status of Config Management Feature:

    $ {command}

    Name             Status  Last_Synced_Token   Sync_Branch  Last_Synced_Time
    mamaged-cluster  SYNCED  2945500b7f          acme         2020-03-23
    11:12:31 -0700 PDT
  """

  FEATURE_NAME = 'configmanagement'
  FEATURE_DISPLAY_NAME = 'Anthos Config Management'

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat("""
    multi(nomos_status:format='table(
            name:label=Name,
            status:label=Status,
            last_synced_token:label="Last_Synced_Token",
            sync_branch:label="Sync_Branch",
            last_synced:label="Last_Synced_Time"
      )', nomos_errors:format=list)
    """)

  def Run(self, args):
    try:
      project_id = properties.VALUES.core.project.GetOrFail()
      name = 'projects/{0}/locations/global/features/{1}'.format(
          project_id, self.FEATURE_NAME)
      response = feature_base.GetFeature(name)
    except apitools_exceptions.HttpUnauthorizedError as e:
      raise exceptions.Error(
          'You are not authorized to see the status of {} '
          'Feature from project [{}]. Underlying error: {}'.format(
              self.FEATURE_DISPLAY_NAME, project_id, e))
    except apitools_exceptions.HttpNotFoundError as e:
      raise exceptions.Error(
          '{} Feature for project [{}] is not enabled'.format(
              self.FEATURE_DISPLAY_NAME, project_id))
    if response.featureState is None or response.featureState.detailsByMembership is None:
      return None
    membership_details = response.featureState.detailsByMembership
    nomos_status = []
    nomos_errors = []
    for md in membership_details.additionalProperties:
      name = os.path.basename(md.key)
      cluster = ConfigmanagementFeatureState(name)
      fs = md.value.configmanagementFeatureState
      # (b/153587485) Show FeatureState.code if it's not OK
      # as it indicates an unreachable cluster or a dated syncState.code
      if md.value.code is None:
        cluster.status = 'CODE_UNSPECIFIED'
      elif md.value.code.name != 'OK':
        cluster.status = md.value.code.name
      # (b/153566864) For cluster not being initialzed
      elif not (fs and fs.configSyncState and fs.configSyncState.syncState and
                fs.configSyncState.syncState.code):
        cluster.status = 'NOT_INSTALLED'
      else:
        cluster.status = fs.configSyncState.syncState.code
        if fs.configSyncState.syncState.syncToken:
          cluster.last_synced_token = fs.configSyncState.syncState.syncToken[:7]
        cluster.last_synced = fs.configSyncState.syncState.lastSync
        if fs.configSyncState.syncState.errors is not None:
          for error in fs.configSyncState.syncState.errors:
            nomos_errors.append({
                'cluster': name,
                'error': error.errorMessage
            })
        if (fs.membershipConfig and fs.membershipConfig.configSync and
            fs.membershipConfig.configSync.git):
          cluster.sync_branch = fs.membershipConfig.configSync.git.syncBranch
      nomos_status.append(cluster)
    return {'nomos_errors': nomos_errors, 'nomos_status': nomos_status}

