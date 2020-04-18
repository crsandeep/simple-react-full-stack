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
"""Wraps a Serverless Service message, making fields more convenient."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.run import configuration
from googlecloudsdk.api_lib.run import k8s_object
from googlecloudsdk.api_lib.run import revision
from googlecloudsdk.api_lib.run import traffic


ENDPOINT_VISIBILITY = 'serving.knative.dev/visibility'
CLUSTER_LOCAL = 'cluster-local'


class Service(k8s_object.KubernetesObject):
  """Wraps a Serverless Service message, making fields more convenient.

  Setting properties on a Service (where possible) writes through to the
  nested Kubernetes-style fields.
  """
  API_CATEGORY = 'serving.knative.dev'
  KIND = 'Service'
  # Field names that are present in Cloud Run messages, but should not be
  # initialized because they are here for legacy reasons.
  FIELD_BLACKLIST = ['manual', 'release', 'runLatest', 'pinned', 'container']

  @classmethod
  def New(cls, client, namespace):
    """Produces a new Service object.

    Args:
      client: The Cloud Run API client.
      namespace: str, The serving namespace.

    Returns:
      A new Service object to be deployed.
    """
    ret = super(Service, cls).New(client, namespace)
    ret.template.spec.containers = [client.MESSAGES_MODULE.Container()]
    return ret

  @property
  def configuration(self):
    """Configuration (configuration.Configuration) of the service, if any."""
    ret = None
    if hasattr(self._m.spec, 'pinned'):
      options = (self._m.spec.pinned, self._m.spec.runLatest)
      ret = next((o.configuration for o in options if o is not None), None)
    if ret:
      return configuration.Configuration.SpecOnly(ret, self._messages)
    return None

  @property
  def template(self):
    if self.configuration:
      return self.configuration.template
    else:
      ret = revision.Revision.Template(
          self.spec.template, self.MessagesModule())
      if not ret.metadata:
        ret.metadata = k8s_object.MakeMeta(self.MessagesModule())
      return ret

  @property
  def template_annotations(self):
    self.AssertFullObject()
    return k8s_object.AnnotationsFromMetadata(
        self._messages, self.template.metadata)

  @property
  def revision_labels(self):
    return self.template.labels

  @property
  def revision_name(self):
    return self.template.name

  @revision_name.setter
  def revision_name(self, value):
    self.template.name = value

  @property
  def latest_created_revision(self):
    return self.status.latestCreatedRevisionName

  @property
  def latest_ready_revision(self):
    return self.status.latestReadyRevisionName

  @property
  def serving_revisions(self):
    return [t.revisionName for t in self.status.traffic if t.percent]

  def _ShouldIncludeInLatestPercent(self, target):
    """Returns True if the target's percent is part of the latest percent."""
    is_latest_by_name = (
        self.status.latestReadyRevisionName and
        target.revisionName == self.status.latestReadyRevisionName)
    return target.percent and (target.latestRevision or is_latest_by_name)

  @property
  def latest_percent_traffic(self):
    """The percent of traffic the latest ready revision is serving."""
    return sum(
        target.percent
        for target in self.status.traffic
        if self._ShouldIncludeInLatestPercent(target))

  @property
  def domain(self):
    return self._m.status.url or self._m.status.domain

  @domain.setter
  def domain(self, domain):
    self._m.status.url = self._m.status.domain = domain

  def ReadySymbolAndColor(self):
    if (self.ready is False and  # pylint: disable=g-bool-id-comparison
        self.latest_ready_revision and
        self.latest_created_revision != self.latest_ready_revision):
      return '!', 'yellow'
    return super(Service, self).ReadySymbolAndColor()

  @property
  def last_modifier(self):
    return self.annotations.get(u'serving.knative.dev/lastModifier')

  @property
  def spec_traffic(self):
    self.AssertFullObject()
    return traffic.TrafficTargets(self._messages, self.spec.traffic)

  @property
  def status_traffic(self):
    self.AssertFullObject()
    return traffic.TrafficTargets(self._messages, self.status.traffic)

  @property
  def vpc_connector(self):
    return self.annotations.get(u'run.googleapis.com/vpc-access-connector')

  def UserImage(self):
    """Human-readable "what's deployed"."""
    user_image = self.annotations.get(revision.USER_IMAGE_ANNOTATION)
    return self.template.UserImage(user_image)
