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
"""Common utility functions for Image Version validation."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.composer import environments_util as environments_api_util
from googlecloudsdk.api_lib.composer import image_versions_util as image_version_api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.composer import util as command_util

# Names of possible aliases that can be used within image version strings.
LATEST = 'latest'

# Set of possible image version aliases
ALIASES = {LATEST}

# Envs must be running at least this version of Composer to be upgradeable.
MIN_UPGRADEABLE_COMPOSER_VER = '1.0.0'


class InvalidImageVersionError(command_util.Error):
  """Class for errors raised when an invalid image version is encountered."""


class _ImageVersionItem(object):
  """Class used to dissect and analyze image version components and strings."""

  def __init__(self, image_ver=None, composer_ver=None, airflow_ver=None):
    if image_ver is not None:
      iv_parts = image_ver.split('-', 4)
      self.composer_ver = iv_parts[1]
      self.airflow_ver = iv_parts[3]

    if composer_ver is not None:
      self.composer_ver = composer_ver

    if airflow_ver is not None:
      self.airflow_ver = airflow_ver

    # Determines the state of aliases
    self.composer_contains_alias = self.composer_ver in ALIASES

    self.airflow_contains_alias = self.airflow_ver in ALIASES

    self.contains_alias = (
        self.composer_contains_alias or self.airflow_contains_alias)

  def GetImageVersionString(self):
    return 'composer-{}-airflow-{}'.format(self.composer_ver, self.airflow_ver)


def ListImageVersionUpgrades(env_ref, release_track=base.ReleaseTrack.GA):
  """List of available image version upgrades for provided env_ref."""
  env_details = environments_api_util.Get(env_ref, release_track)
  proj_location_ref = env_ref.Parent()
  cur_image_version_id = env_details.config.softwareConfig.imageVersion
  cur_python_version = env_details.config.softwareConfig.pythonVersion

  return _BuildUpgradeCandidateList(proj_location_ref, cur_image_version_id,
                                    cur_python_version, release_track)


def IsValidImageVersionUpgrade(env_ref,
                               image_version_id,
                               release_track=base.ReleaseTrack.GA):
  """Checks if image version candidate is a valid upgrade for environment."""

  # Checks for the use of an alias and confirms that a valid airflow upgrade has
  # been requested.
  cand_image_ver = _ImageVersionItem(image_ver=image_version_id)
  if cand_image_ver.composer_contains_alias:
    env_details = environments_api_util.Get(env_ref, release_track)
    cur_image_ver = _ImageVersionItem(
        image_ver=env_details.config.softwareConfig.imageVersion)
    if _IsAirflowVersionUpgradeCompatible(cur_image_ver.airflow_ver,
                                          cand_image_ver.airflow_ver):
      return True
  else:
    # Checks if supplied image_version_id matches an eligible env upgrade.
    valid_image_versions = ListImageVersionUpgrades(env_ref, release_track)
    return any(True for version in valid_image_versions
               if version.imageVersionId.startswith(image_version_id))


def ImageVersionFromAirflowVersion(airflow_version):
  """Converts airflow-version string into a image-version string."""
  return _ImageVersionItem(
      composer_ver='latest',
      airflow_ver=airflow_version).GetImageVersionString()


def CompareVersions(v1, v2):
  """Compares semantic version strings.

  Args:
    v1: first semantic version string
    v2: second semantic version string

  Returns:
    Value >= 1 when v1 is greater; Value <= -1 when v2 is greater; otherwise 0.
  """
  v1, v2 = _VersionStrToList(v1), _VersionStrToList(v2)
  if v1[0] - v2[0] != 0:
    return v1[0] - v2[0]
  if v1[1] - v2[1] != 0:
    return v1[1] - v2[1]
  return v1[2] - v2[2]


def _BuildUpgradeCandidateList(location_ref,
                               image_version_id,
                               python_version,
                               release_track=base.ReleaseTrack.GA):
  """Builds a list of eligible image version upgrades."""
  image_version_service = image_version_api_util.ImageVersionService(
      release_track)
  image_version_item = _ImageVersionItem(image_version_id)

  available_upgrades = []
  # Checks if current composer version meets minimum threshold.
  if (CompareVersions(MIN_UPGRADEABLE_COMPOSER_VER,
                      image_version_item.composer_ver) <= 0):
    # If so, builds list of eligible upgrades.
    for version in image_version_service.List(location_ref):
      if (_ValidateCandidateImageVersionId(image_version_id,
                                           version.imageVersionId) and
          python_version in version.supportedPythonVersions):
        available_upgrades.append(version)
  else:
    raise InvalidImageVersionError(
        'This environment does not support upgrades.')

  return available_upgrades


def _ValidateCandidateImageVersionId(current_image_version_id,
                                     candidate_image_version_id):
  """Determines if candidate version is a valid upgrade from current version."""
  if current_image_version_id == candidate_image_version_id:
    return False

  parsed_curr = _ImageVersionItem(image_ver=current_image_version_id)
  parsed_cand = _ImageVersionItem(image_ver=candidate_image_version_id)

  # Checks Composer versions.
  if (not parsed_cand.composer_contains_alias and
      not _IsComposerVersionUpgradeCompatible(parsed_curr.composer_ver,
                                              parsed_cand.composer_ver)):
    return False

  # Checks Airflow versions.
  if (not parsed_cand.airflow_contains_alias and
      not _IsAirflowVersionUpgradeCompatible(parsed_curr.airflow_ver,
                                             parsed_cand.airflow_ver)):
    return False

  return True


def _VersionStrToList(version_str):
  """Splits version_str into a list of three items (ie MAJOR, MINOR, PATCH)."""
  return [int(v) for v in version_str.split('.', 3)]


def _IsAirflowVersionUpgradeCompatible(cur_version, candidate_version):
  """Validates Airflow version candidate is greater than or equal to current.

  Airflow upgrades support MAJOR, MINOR, and PATCH-level upgrades.

  Args:
    cur_version: current 'a.b.c' Airflow version
    candidate_version: candidate 'x.y.z' Airflow version

  Returns:
    boolean value whether Airflow candidate is valid
  """
  return CompareVersions(cur_version, candidate_version) <= 0


def _IsComposerVersionUpgradeCompatible(cur_version, candidate_version):
  """Validates Composer version candidate is greater than or equal to current.

  Composer upgrades support MINOR and PATCH-level upgrades.

  Args:
    cur_version: current 'a.b.c' Composer version
    candidate_version: candidate 'a.y.z' Composer version

  Returns:
    boolean value whether Composer candidate is valid
  """
  curr_parts = _VersionStrToList(cur_version)
  cand_parts = _VersionStrToList(candidate_version)

  if (curr_parts[0] == cand_parts[0] and
      CompareVersions(cur_version, candidate_version) <= 0):
    return True

  return False
