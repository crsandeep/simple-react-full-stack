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
"""Wraps an Events Trigger message, making fields more convenient."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.protorpclite import protojson
from googlecloudsdk.api_lib.run import k8s_object


# TODO(b/141719436): Don't hardcode v1alpha1 version
_SERVICE_API_VERSION = 'serving.knative.dev/v1alpha1'
_SERVICE_KIND = 'Service'

EVENT_TYPE_FIELD = 'type'
# k8s OwnerReference serialized to a json string
DEPENDENCY_ANNOTATION_FIELD = 'knative.dev/dependency'
# Annotation to indicate that the namespace should be labeled, which in
# will create the broker "default" if it does not already exist.
# The value for this field should only be "enabled" and it should only be set
# if the trigger's broker is named "default".
_INJECTION_ANNOTATION_FIELD = 'knative-eventing-injection'
_INJECTION_BROKER_NAME = 'default'
# Field placed on both the trigger and source (as a CEOverrdie) to link the
# resources so the trigger only consumes events from that source
SOURCE_TRIGGER_LINK_FIELD = 'knsourcetrigger'


class Trigger(k8s_object.KubernetesObject):
  """Wraps an Events Trigger message, making fields more convenient."""

  API_CATEGORY = 'eventing.knative.dev'
  KIND = 'Trigger'
  READY_CONDITION = 'Ready'
  TERMINAL_CONDITIONS = {
      READY_CONDITION,
  }
  FIELD_BLACKLIST = []

  @property
  def dependency(self):
    """The knative dependency annotation.

    Returns:
      ObjectReference of the dependency annotation if one exists, else None.
    """
    if DEPENDENCY_ANNOTATION_FIELD not in self.annotations:
      return None
    return protojson.decode_message(
        self._messages.ObjectReference,
        self.annotations[DEPENDENCY_ANNOTATION_FIELD])

  @dependency.setter
  def dependency(self, k8s_obj):
    """Set the knative dependency annotation by passing a k8s_object.KubernetesObject."""
    self.annotations[DEPENDENCY_ANNOTATION_FIELD] = protojson.encode_message(
        k8s_obj.AsObjectReference())

  @property
  def broker(self):
    return self._m.spec.broker

  @broker.setter
  def broker(self, value):
    if value == _INJECTION_BROKER_NAME:
      self.annotations[_INJECTION_ANNOTATION_FIELD] = 'enabled'
    self._m.spec.broker = value

  @property
  def subscriber(self):
    # TODO(b/147249685): Support ref + relative uri case
    if self._m.spec.subscriber.uri:
      return self._m.spec.subscriber.uri
    return self._m.spec.subscriber.ref.name

  @subscriber.setter
  def subscriber(self, service_name):
    """Set the subscriber to a Cloud Run service."""
    self._m.spec.subscriber.ref.apiVersion = _SERVICE_API_VERSION
    self._m.spec.subscriber.ref.kind = _SERVICE_KIND
    self._m.spec.subscriber.ref.name = service_name

  @property
  def filter_attributes(self):
    return k8s_object.ListAsDictionaryWrapper(
        self._m.spec.filter.attributes.additionalProperties,
        self._messages.TriggerFilter.AttributesValue.AdditionalProperty,
        key_field='key',
        value_field='value')
