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
"""Utility for interacting with `artifacts docker` command group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from apitools.base.py import exceptions as api_exceptions
from googlecloudsdk.api_lib.artifacts import exceptions as ar_exceptions
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.command_lib.artifacts import requests as ar_requests
from googlecloudsdk.command_lib.artifacts import util as ar_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io

ARTIFACTREGISTRY_API_NAME = "artifactregistry"
ARTIFACTREGISTRY_API_VERSION = "v1beta1"

_INVALID_IMAGE_PATH_ERROR = """Invalid Docker string.

A valid Docker repository has the format of
  LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY-ID

A valid image has the format of
  LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY-ID/IMAGE
"""

_INVALID_DEFAULT_DOCKER_STRING_ERROR = (
    """Fail to construct Docker string from config values:
core/project: {project}, artifacts/location: {location}, artifacts/repository: {repo}

A valid Docker repository has the format of
  LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY-ID

A valid image has the format of
  LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY-ID/IMAGE
""")

_INVALID_IMAGE_ERROR = """Invalid Docker image.

A valid container image has the format of
  LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY-ID/IMAGE

A valid container image that can be referenced by tag or digest, has the format of
  LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY-ID/IMAGE:tag
  LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY-ID/IMAGE@sha256:digest
"""

_INVALID_DOCKER_IMAGE_ERROR = """Invalid Docker image.

A valid container image can be referenced by tag or digest, has the format of
  LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY-ID/IMAGE:tag
  LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY-ID/IMAGE@sha256:digest
"""

_INVALID_DOCKER_TAG_ERROR = """Invalid Docker tag.

A valid Docker tag has the format of
  LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY-ID/IMAGE:tag
"""

DOCKER_REPO_REGEX = r"^(?P<location>.*)-docker.pkg.dev\/(?P<project>[^\/]+)\/(?P<repo>[^\/]+)"

DOCKER_IMG_BY_TAG_REGEX = r"^.*-docker.pkg.dev\/[^\/]+\/[^\/]+\/(?P<img>.*):(?P<tag>.*)"

DOCKER_IMG_BY_DIGEST_REGEX = r"^.*-docker.pkg.dev\/[^\/]+\/[^\/]+\/(?P<img>.*)@(?P<digest>sha256:.*)"

DOCKER_IMG_REGEX = r"^.*-docker.pkg.dev\/[^\/]+\/[^\/]+\/(?P<img>.*)"


def _GetDefaultResources():
  """Gets default config values for project, location, and repository."""
  project = properties.VALUES.core.project.Get()
  location = properties.VALUES.artifacts.location.Get()
  repo = properties.VALUES.artifacts.repository.Get()
  if not project or not location or not repo:
    raise ar_exceptions.InvalidInputValueError(
        _INVALID_DEFAULT_DOCKER_STRING_ERROR.format(**{
            "project": project,
            "location": location,
            "repo": repo,
        }))
  ar_util.ValidateLocation(location, project)
  return DockerRepo(project, location, repo)


def _ParseInput(input_str):
  """Parses user input into project, location, and repository values.

  Args:
    input_str: str, user input. Ex: us-docker.pkg.dev/my-proj/my-repo/my-img

  Raises:
    ar_exceptions.InvalidInputValueError if user input is invalid.
    ar_exceptions.UnsupportedLocationError if provided location is invalid.

  Returns:
    A DockerRepo.
  """
  matches = re.match(DOCKER_REPO_REGEX, input_str)
  if not matches:
    raise ar_exceptions.InvalidInputValueError()
  location = matches.group("location")
  project_id = matches.group("project")
  return DockerRepo(project_id, location, matches.group("repo"))


def _ParseDockerImagePath(img_path):
  """Validates and parses an image path into a DockerImage or a DockerRepo."""
  if not img_path:
    return _GetDefaultResources()

  resource_val_list = list(filter(None, img_path.split("/")))
  try:
    docker_repo = _ParseInput(img_path)
  except ar_exceptions.InvalidInputValueError:
    raise ar_exceptions.InvalidInputValueError(_INVALID_IMAGE_PATH_ERROR)

  ar_util.ValidateLocation(docker_repo.location, docker_repo.project)

  if len(resource_val_list) == 3:
    return docker_repo
  elif len(resource_val_list) > 3:
    return DockerImage(docker_repo, "/".join(resource_val_list[3:]))
  raise ar_exceptions.InvalidInputValueError(_INVALID_IMAGE_PATH_ERROR)


def _ParseDockerImage(img_str, err_msg):
  """Validates and parses an image string into a DockerImage.

  Args:
    img_str: str, User input docker formatted string.
    err_msg: str, Error message to return to user.

  Raises:
    ar_exceptions.InvalidInputValueError if user input is invalid.
    ar_exceptions.UnsupportedLocationError if provided location is invalid.

  Returns:
    A DockerImage, and a DockerTag or a DockerVersion.
  """
  try:
    docker_repo = _ParseInput(img_str)
  except ar_exceptions.InvalidInputValueError:
    raise ar_exceptions.InvalidInputValueError(_INVALID_DOCKER_IMAGE_ERROR)

  ar_util.ValidateLocation(docker_repo.location, docker_repo.project)

  img_by_digest_match = re.match(DOCKER_IMG_BY_DIGEST_REGEX, img_str)
  if img_by_digest_match:
    docker_img = DockerImage(docker_repo, img_by_digest_match.group("img"))
    return docker_img, DockerVersion(docker_img,
                                     img_by_digest_match.group("digest"))
  img_by_tag_match = re.match(DOCKER_IMG_BY_TAG_REGEX, img_str)
  if img_by_tag_match:
    docker_img = DockerImage(docker_repo, img_by_tag_match.group("img"))
    return docker_img, DockerTag(docker_img, img_by_tag_match.group("tag"))
  whole_img_match = re.match(DOCKER_IMG_REGEX, img_str)
  if whole_img_match:
    return DockerImage(docker_repo,
                       whole_img_match.group("img").strip("/")), None
  raise ar_exceptions.InvalidInputValueError(err_msg)


def _ParseDockerTag(tag):
  """Validates and parses a tag string.

  Args:
    tag: str, User input Docker tag string.

  Raises:
    ar_exceptions.InvalidInputValueError if user input is invalid.
    ar_exceptions.UnsupportedLocationError if provided location is invalid.

  Returns:
    A DockerImage and a DockerTag.
  """
  try:
    docker_repo = _ParseInput(tag)
  except ar_exceptions.InvalidInputValueError:
    raise ar_exceptions.InvalidInputValueError(_INVALID_DOCKER_TAG_ERROR)

  img_by_tag_match = re.match(DOCKER_IMG_BY_TAG_REGEX, tag)
  if img_by_tag_match:
    docker_img = DockerImage(docker_repo, img_by_tag_match.group("img"))
    return docker_img, DockerTag(docker_img, img_by_tag_match.group("tag"))
  else:
    raise ar_exceptions.InvalidInputValueError(_INVALID_DOCKER_TAG_ERROR)


def _GetDockerPackagesAndVersions(docker_repo, include_tags, is_nested=False):
  """Gets a list of packages with versions for a Docker repository."""
  client = ar_requests.GetClient()
  messages = ar_requests.GetMessages()
  img_list = []
  for pkg in ar_requests.ListPackages(client, messages,
                                      docker_repo.GetRepositoryName()):
    parts = pkg.name.split("/")
    if len(parts) != 8:
      raise ar_exceptions.ArtifactRegistryError(
          "Internal error. Corrupted package name: {}".format(pkg.name))
    img = DockerImage(DockerRepo(parts[1], parts[3], parts[5]), parts[7])
    img_list.extend(_GetDockerVersions(img, include_tags, is_nested))
  return img_list


def _GetDockerNestedVersions(docker_img, include_tags, is_nested=False):
  """Gets a list of versions for a Docker nested image."""
  prefix = docker_img.GetDockerString() + "/"
  return [
      ver for ver in _GetDockerPackagesAndVersions(docker_img.docker_repo,
                                                   include_tags, is_nested)
      if ver["package"].startswith(prefix)
  ]


def _GetDockerVersions(docker_img, include_tags, is_nested=False):
  """Gets a list of versions for a Docker image."""
  client = ar_requests.GetClient()
  messages = ar_requests.GetMessages()
  ver_view = (
      messages
      .ArtifactregistryProjectsLocationsRepositoriesPackagesVersionsListRequest
      .ViewValueValuesEnum.BASIC)
  if include_tags:
    ver_view = (
        messages.
        ArtifactregistryProjectsLocationsRepositoriesPackagesVersionsListRequest
        .ViewValueValuesEnum.FULL)
  ver_list = ar_requests.ListVersions(client, messages,
                                      docker_img.GetPackageName(), ver_view)

  # If there's no result, the package name might be part of a nested package.
  # E.g. us-west1-docker.pkg.dev/fake-project/docker-repo/nested1 in
  # us-west1-docker.pkg.dev/fake-project/docker-repo/nested1/nested2/test-image
  # Try to get the list of versions through the list of all packages.
  if not ver_list and not is_nested:
    return _GetDockerNestedVersions(docker_img, include_tags, is_nested=True)

  img_list = []
  for ver in ver_list:
    img_list.append({
        "package": docker_img.GetDockerString(),
        "tags": ", ".join([tag.name.split("/")[-1] for tag in ver.relatedTags]),
        "version": ver.name,
        "createTime": ver.createTime,
        "updateTime": ver.updateTime
    })
  return img_list


def _LogResourcesToDelete(docker_version, docker_tags):
  """Logs user visible messages on resources to be deleted."""
  log.status.Print("Digests:\n- " + docker_version.GetDockerString())
  if docker_tags:
    log.status.Print("\nTags:")
    for tag in docker_tags:
      log.status.Print("- " + tag.GetDockerString())


def _GetDockerVersionTags(client, messages, docker_version):
  """Gets a list of DockerTag associated with the given DockerVersion."""
  tags = ar_requests.ListVersionTags(client, messages,
                                     docker_version.GetPackageName(),
                                     docker_version.GetVersionName())
  return [
      DockerTag(docker_version.image,
                tag.name.split("/")[-1]) for tag in tags
  ]


def _ValidateDockerRepo(repo_name):
  repo = ar_requests.GetRepository(repo_name)
  messages = ar_requests.GetMessages()
  if repo.format != messages.Repository.FormatValueValuesEnum.DOCKER:
    raise ar_exceptions.InvalidInputValueError(
        "Invalid repository type {}. The `artifacts docker` command group can "
        "only be used on Docker repositories.".format(repo.format))


class DockerRepo(object):
  """Holder for a Docker repository.

  A valid Docker repository has the format of
  LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY-ID

  Properties:
    project: str, The name of cloud project.
    location: str, The location of the Docker resource.
    repo: str, The name of the repository.
  """

  def __init__(self, project_id, location_id, repo_id):
    self._project = project_id
    self._location = location_id
    self._repo = repo_id

  @property
  def project(self):
    return self._project

  @property
  def location(self):
    return self._location

  @property
  def repo(self):
    return self._repo

  def GetRepositoryName(self):
    return "projects/{}/locations/{}/repositories/{}".format(
        self.project, self.location, self.repo)


class DockerImage(object):
  """Holder for a Docker image resource.

  A valid image has the format of
  LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY-ID/IMAGE_PATH

  Properties:
    docker_repo: DockerRepo, The Docker repository.
    pkg: str, The name of the package.
  """

  def __init__(self, docker_repo, pkg_id):
    self._docker_repo = docker_repo
    self._pkg = pkg_id

  @property
  def docker_repo(self):
    return self._docker_repo

  @property
  def pkg(self):
    return self._pkg

  def GetPackageName(self):
    return "{}/packages/{}".format(self.docker_repo.GetRepositoryName(),
                                   self.pkg.replace("/", "%2F"))

  def GetDockerString(self):
    return "{}-docker.pkg.dev/{}/{}/{}".format(self.docker_repo.location,
                                               self.docker_repo.project,
                                               self.docker_repo.repo,
                                               self.pkg.replace("%2F", "/"))


class DockerTag(object):
  """Holder for a Docker tag.

  A valid Docker tag has the format of
  LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY-ID/IMAGE:tag

  Properties:
    image: DockerImage, The DockerImage containing the tag.
    tag: str, The name of the Docker tag.
  """

  def __init__(self, docker_img, tag_id):
    self._image = docker_img
    self._tag = tag_id

  @property
  def image(self):
    return self._image

  @property
  def tag(self):
    return self._tag

  def GetTagName(self):
    return "{}/tags/{}".format(self.image.GetPackageName(), self.tag)

  def GetPackageName(self):
    return self.image.GetPackageName()

  def GetDockerString(self):
    return "{}:{}".format(self.image.GetDockerString(), self.tag)


class DockerVersion(object):
  """Holder for a Docker version.

  A valid Docker version has the format of
  LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY-ID/IMAGE@sha256:digest

  Properties:
    image: DockerImage, The DockerImage containing the tag.
    digest: str, The name of the Docker digest.
  """

  def __init__(self, docker_img, digest):
    self._image = docker_img
    self._digest = digest

  @property
  def image(self):
    return self._image

  @property
  def digest(self):
    return self._digest

  def GetVersionName(self):
    return "{}/versions/{}".format(self.image.GetPackageName(), self.digest)

  def GetPackageName(self):
    return self.image.GetPackageName()

  def GetDockerString(self):
    return "{}@{}".format(self.image.GetDockerString(), self.digest)


def GetDockerImages(args):
  """Gets Docker images."""
  resource = _ParseDockerImagePath(args.IMAGE_PATH)
  if isinstance(resource, DockerRepo):
    _ValidateDockerRepo(resource.GetRepositoryName())
    log.status.Print(
        "Listing items under project {}, location {}, repository {}.\n".format(
            resource.project, resource.location, resource.repo))
    return _GetDockerPackagesAndVersions(resource, args.include_tags)
  elif isinstance(resource, DockerImage):
    _ValidateDockerRepo(resource.docker_repo.GetRepositoryName())
    log.status.Print(
        "Listing items under project {}, location {}, repository {}.\n".format(
            resource.docker_repo.project, resource.docker_repo.location,
            resource.docker_repo.repo))
    return _GetDockerVersions(resource, args.include_tags)
  return []


def WaitForOperation(operation, message):
  """Waits for the given google.longrunning.Operation to complete.

  Args:
    operation: The operation to poll.
    message: String to display for default progress_tracker.

  Raises:
    apitools.base.py.HttpError: if the request returns an HTTP error
  """
  op_service = ar_requests.GetClient().projects_locations_operations
  op_resource = resources.REGISTRY.ParseRelativeName(
      operation.name,
      collection="artifactregistry.projects.locations.operations")
  poller = waiter.CloudOperationPollerNoResources(op_service)
  waiter.WaitFor(poller, op_resource, message)


def DeleteDockerImage(args):
  """Deletes a Docker digest or image.

  If input is an image, delete the image along with its resources.

  If input is an image identified by digest, delete the digest.
  If input is an image identified by tag, delete the digest and the tag.
  If --delete-tags is specified, delete all tags associated with the image
  digest.

  Args:
    args: user input arguments.

  Returns:
    The long-running operation from DeletePackage API call.
  """
  image, version_or_tag = _ParseDockerImage(args.IMAGE, _INVALID_IMAGE_ERROR)
  _ValidateDockerRepo(image.docker_repo.GetRepositoryName())
  client = ar_requests.GetClient()
  messages = ar_requests.GetMessages()
  if not version_or_tag:
    console_io.PromptContinue(
        message="\nThis operation will delete all tags and images for " +
        image.GetDockerString() + ".",
        cancel_on_no=True)
    return ar_requests.DeletePackage(client, messages, image.GetPackageName())

  else:
    tags_to_delete = []
    docker_version = version_or_tag
    if isinstance(version_or_tag, DockerTag):
      docker_version = DockerVersion(
          version_or_tag.image,
          ar_requests.GetVersionFromTag(client, messages,
                                        version_or_tag.GetTagName()))
      tags_to_delete.append(version_or_tag)
    existing_tags = _GetDockerVersionTags(client, messages, docker_version)
    if args.delete_tags:
      tags_to_delete.extend(existing_tags)

    if len(existing_tags) != len(tags_to_delete):
      raise ar_exceptions.ArtifactRegistryError(
          "Cannot delete image {} because it is tagged. "
          "Existing tags are:\n- {}".format(
              args.IMAGE,
              "\n- ".join(tag.GetDockerString() for tag in existing_tags)))

    _LogResourcesToDelete(docker_version, tags_to_delete)
    console_io.PromptContinue(
        message="\nThis operation will delete the above resources.",
        cancel_on_no=True)

    for tag in tags_to_delete:
      ar_requests.DeleteTag(client, messages, tag.GetTagName())
    return ar_requests.DeleteVersion(client, messages,
                                     docker_version.GetVersionName())


def AddDockerTag(args):
  """Adds a Docker tag."""
  src_image, version_or_tag = _ParseDockerImage(args.DOCKER_IMAGE,
                                                _INVALID_DOCKER_IMAGE_ERROR)
  if version_or_tag is None:
    raise ar_exceptions.InvalidInputValueError(_INVALID_DOCKER_IMAGE_ERROR)

  dest_image, tag = _ParseDockerTag(args.DOCKER_TAG)

  if src_image.GetPackageName() != dest_image.GetPackageName():
    raise ar_exceptions.InvalidInputValueError(
        "Image {}\ndoes not match image {}".format(
            src_image.GetDockerString(), dest_image.GetDockerString()))

  _ValidateDockerRepo(src_image.docker_repo.GetRepositoryName())

  client = ar_requests.GetClient()
  messages = ar_requests.GetMessages()
  docker_version = version_or_tag
  if isinstance(version_or_tag, DockerTag):
    docker_version = DockerVersion(
        version_or_tag.image,
        ar_requests.GetVersionFromTag(client, messages,
                                      version_or_tag.GetTagName()))

  try:
    ar_requests.GetTag(client, messages, tag.GetTagName())
  except api_exceptions.HttpNotFoundError:
    ar_requests.CreateDockerTag(client, messages, tag, docker_version)
  else:
    ar_requests.DeleteTag(client, messages, tag.GetTagName())
    ar_requests.CreateDockerTag(client, messages, tag, docker_version)

  log.status.Print("Added tag [{}] to image [{}].".format(
      tag.GetDockerString(), args.DOCKER_IMAGE))


def DeleteDockerTag(args):
  """Deletes a Docker tag."""
  img, tag = _ParseDockerTag(args.DOCKER_TAG)

  ar_util.ValidateLocation(img.docker_repo.location, img.docker_repo.project)
  _ValidateDockerRepo(img.docker_repo.GetRepositoryName())

  console_io.PromptContinue(
      message="You are about to delete tag [{}]".format(tag.GetDockerString()),
      cancel_on_no=True)
  ar_requests.DeleteTag(ar_requests.GetClient(), ar_requests.GetMessages(),
                        tag.GetTagName())
  log.status.Print("Deleted tag [{}].".format(tag.GetDockerString()))


def ListDockerTags(args):
  """Lists Docker tags."""
  resource = _ParseDockerImagePath(args.IMAGE_PATH)

  client = ar_requests.GetClient()
  messages = ar_requests.GetMessages()
  img_list = []
  if isinstance(resource, DockerRepo):
    _ValidateDockerRepo(resource.GetRepositoryName())
    log.status.Print(
        "Listing items under project {}, location {}, repository {}.\n".format(
            resource.project, resource.location, resource.repo))
    for pkg in ar_requests.ListPackages(client, messages,
                                        resource.GetRepositoryName()):
      img_list.append(DockerImage(resource, pkg.name.split("/")[-1]))
  elif isinstance(resource, DockerImage):
    _ValidateDockerRepo(resource.docker_repo.GetRepositoryName())
    log.status.Print(
        "Listing items under project {}, location {}, repository {}.\n".format(
            resource.docker_repo.project, resource.docker_repo.location,
            resource.docker_repo.repo))
    img_list.append(resource)

  tag_list = []
  for img in img_list:
    for tag in ar_requests.ListTags(client, messages, img.GetPackageName()):
      tag_list.append({
          "tag": tag.name,
          "image": img.GetDockerString(),
          "version": tag.version,
      })
  return tag_list
