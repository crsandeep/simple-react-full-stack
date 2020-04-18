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
"""Allows you to write surfaces in terms of logical Eventflow operations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import contextlib
import datetime
import functools
import random

from apitools.base.py import exceptions as api_exceptions
from googlecloudsdk.api_lib.events import custom_resource_definition
from googlecloudsdk.api_lib.events import iam_util
from googlecloudsdk.api_lib.events import metric_names
from googlecloudsdk.api_lib.events import source
from googlecloudsdk.api_lib.events import trigger
from googlecloudsdk.api_lib.run import secret
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import apis_internal
from googlecloudsdk.command_lib.events import exceptions
from googlecloudsdk.command_lib.events import stages
from googlecloudsdk.command_lib.events import util
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.apis import registry
from googlecloudsdk.core import metrics
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


_EVENT_SOURCES_LABEL_SELECTOR = 'duck.knative.dev/source=true'

_METADATA_LABELS_FIELD = 'metadata.labels'

_SERVICE_ACCOUNT_KEY_COLLECTION = 'iam.projects.serviceAccounts.keys'

_CORE_CLIENT_VERSION = 'v1'
_CRD_CLIENT_VERSION = 'v1beta1'


@contextlib.contextmanager
def Connect(conn_context):
  """Provide a EventflowOperations instance to use.

  If we're using the GKE Serverless Add-on, connect to the relevant cluster.
  Otherwise, connect to the right region of GSE.

  Arguments:
    conn_context: a context manager that yields a ConnectionInfo and manages a
      dynamic context that makes connecting to serverless possible.

  Yields:
    A EventflowOperations instance.
  """

  # The One Platform client is required for making requests against
  # endpoints that do not supported Kubernetes-style resource naming
  # conventions. The One Platform client must be initialized outside of a
  # connection context so that it does not pick up the api_endpoint_overrides
  # values from the connection context.
  op_client = apis.GetClientInstance(
      conn_context.api_name,
      conn_context.api_version)

  with conn_context as conn_info:
    # pylint: disable=protected-access
    client = apis_internal._GetClientInstance(
        conn_info.api_name,
        conn_info.api_version,
        # Only check response if not connecting to GKE
        check_response_func=apis.CheckResponseForApiEnablement()
        if conn_context.supports_one_platform else None,
        http_client=conn_context.HttpClient())
    # This client is used for working with core resources (e.g. Secrets)
    core_client = apis_internal._GetClientInstance(
        conn_context.api_name,
        _CORE_CLIENT_VERSION,
        http_client=conn_context.HttpClient())
    # This client is only used to get CRDs because the api group they are
    # under uses different versioning in k8s
    crd_client = apis_internal._GetClientInstance(
        conn_context.api_name,
        _CRD_CLIENT_VERSION,
        http_client=conn_context.HttpClient())
    # pylint: enable=protected-access
    yield EventflowOperations(
        client,
        conn_info.region,
        core_client,
        crd_client,
        op_client)


# TODO(b/149793348): Remove this grace period
_POLLING_GRACE_PERIOD = datetime.timedelta(seconds=15)


class TimeLockedUnfailingConditionPoller(serverless_operations.ConditionPoller):
  """Condition poller that never fails and is only done on success for a period of time.

  Knative Eventing occasionally returns Ready == False on a resource that will
  shortly become Ready == True. In these cases, we cannot rely upon that False
  status as an indication of a terminal failure. Instead, only Ready == True can
  be relied upon as a terminal state and all other statuses (False, Unknown)
  simply mean not currently successful, but provide no indication if this is a
  temporary or permanent state.

  This condition poller never fails a stage for that reason, and therefore is
  never done until successful.

  This behavior only exists for a period of time, after which it acts like a
  normal condition poller.
  """

  def __init__(self,
               getter,
               tracker,
               dependencies=None,
               grace_period=_POLLING_GRACE_PERIOD):
    super(TimeLockedUnfailingConditionPoller,
          self).__init__(getter, tracker, dependencies)
    self._grace_period = _POLLING_GRACE_PERIOD
    self._start_time = datetime.datetime.now()

  def _HasGracePeriodPassed(self):
    return datetime.datetime.now() - self._start_time > self._grace_period

  def IsDone(self, conditions):
    """Within grace period -  this only checks for IsReady rather than IsTerminal.

    Args:
      conditions: A condition.Conditions object.

    Returns:
      A bool indicating whether `conditions` is ready.
    """
    if self._HasGracePeriodPassed():
      return super(TimeLockedUnfailingConditionPoller, self).IsDone(conditions)

    if conditions is None:
      return False
    return conditions.IsReady()

  def Poll(self, unused_ref):
    """Within grace period - this polls like normal but does not raise on failure.

    Args:
      unused_ref: A string representing the operation reference. Unused and may
        be None.

    Returns:
      A condition.Conditions object or None if there's no conditions on the
        resource or if the conditions are not fresh (the generation on the
        resource doesn't match the observedGeneration)
    """
    if self._HasGracePeriodPassed():
      return super(TimeLockedUnfailingConditionPoller, self).Poll(unused_ref)

    conditions = self.GetConditions()

    if conditions is None or not conditions.IsFresh():
      return None

    conditions_message = conditions.DescriptiveMessage()
    if conditions_message:
      self._tracker.UpdateHeaderMessage(conditions_message)

    self._PollTerminalSubconditions(conditions, conditions_message)

    if conditions.IsReady():
      self._tracker.UpdateHeaderMessage(self._ready_message)
      # TODO(b/120679874): Should not have to manually call Tick()
      self._tracker.Tick()

    return conditions

  def _PossiblyFailStage(self, condition, message):
    """Within grace period - stages are never marked as failed."""
    if self._HasGracePeriodPassed():
      # pylint:disable=protected-access
      return super(TimeLockedUnfailingConditionPoller,
                   self)._PossiblyFailStage(condition, message)


class TriggerConditionPoller(TimeLockedUnfailingConditionPoller):
  """A ConditionPoller for triggers."""


class SourceConditionPoller(TimeLockedUnfailingConditionPoller):
  """A ConditionPoller for sources."""


class EventflowOperations(object):
  """Client used by Eventflow to communicate with the actual API."""

  def __init__(self, client, region, core_client, crd_client, op_client):
    """Inits EventflowOperations with given API clients.

    Args:
      client: The API client for interacting with Kubernetes Cloud Run APIs.
      region: str, The region of the control plane if operating against
        hosted Cloud Run, else None.
      core_client: The API client for queries against core resources.
      crd_client: The API client for querying for CRDs
      op_client: The API client for interacting with One Platform APIs. Or
        None if interacting with Cloud Run for Anthos.
    """
    self._client = client
    self._core_client = core_client
    self._crd_client = crd_client
    self._op_client = op_client
    self._region = region

  @property
  def client(self):
    return self._client

  @property
  def messages(self):
    return self._client.MESSAGES_MODULE

  def GetTrigger(self, trigger_ref):
    """Returns the referenced trigger."""
    request = self.messages.RunNamespacesTriggersGetRequest(
        name=trigger_ref.RelativeName())
    try:
      with metrics.RecordDuration(metric_names.GET_TRIGGER):
        response = self._client.namespaces_triggers.Get(request)
    except api_exceptions.HttpNotFoundError:
      return None
    return trigger.Trigger(response, self.messages)

  def CreateTrigger(self, trigger_ref, source_obj, event_type, target_service,
                    broker):
    """Create a trigger that sends events to the target service.

    Args:
      trigger_ref: googlecloudsdk.core.resources.Resource, trigger resource.
      source_obj: source.Source. The source object to be created after the
        trigger. If creating a custom event, this may be None.
      event_type: str, the event type the source will filter by.
      target_service: str, name of the Cloud Run service to subscribe.
      broker: str, name of the broker to act as a sink for the source.

    Returns:
      trigger.Trigger of the created trigger.
    """
    trigger_obj = trigger.Trigger.New(self._client, trigger_ref.Parent().Name())
    trigger_obj.name = trigger_ref.Name()
    if source_obj is not None:
      trigger_obj.dependency = source_obj
      # TODO(b/141617597): Set to str(random.random()) without prepended string
      trigger_obj.filter_attributes[
          trigger.SOURCE_TRIGGER_LINK_FIELD] = 'link{}'.format(random.random())
    trigger_obj.filter_attributes[trigger.EVENT_TYPE_FIELD] = event_type
    trigger_obj.subscriber = target_service
    trigger_obj.broker = broker

    request = self.messages.RunNamespacesTriggersCreateRequest(
        trigger=trigger_obj.Message(),
        parent=trigger_ref.Parent().RelativeName())
    try:
      with metrics.RecordDuration(metric_names.CREATE_TRIGGER):
        response = self._client.namespaces_triggers.Create(request)
    except api_exceptions.HttpConflictError:
      raise exceptions.TriggerCreationError(
          'Trigger [{}] already exists.'.format(trigger_obj.name))

    return trigger.Trigger(response, self.messages)

  def PollTrigger(self, trigger_ref, tracker):
    """Wait for trigger to be Ready == True."""
    trigger_getter = functools.partial(self.GetTrigger, trigger_ref)
    poller = TriggerConditionPoller(trigger_getter, tracker,
                                    stages.TriggerSourceDependencies())
    util.WaitForCondition(poller, exceptions.TriggerCreationError)

  def ListTriggers(self, namespace_ref):
    """Returns a list of existing triggers in the given namespace."""
    request = self.messages.RunNamespacesTriggersListRequest(
        parent=namespace_ref.RelativeName())
    with metrics.RecordDuration(metric_names.LIST_TRIGGERS):
      response = self._client.namespaces_triggers.List(request)
    return [trigger.Trigger(item, self.messages) for item in response.items]

  def DeleteTrigger(self, trigger_ref):
    """Deletes the referenced trigger."""
    request = self.messages.RunNamespacesTriggersDeleteRequest(
        name=trigger_ref.RelativeName())
    try:
      with metrics.RecordDuration(metric_names.DELETE_TRIGGER):
        self._client.namespaces_triggers.Delete(request)
    except api_exceptions.HttpNotFoundError:
      raise exceptions.TriggerNotFound(
          'Trigger [{}] not found.'.format(trigger_ref.Name()))

  def _FindSourceMethod(self, source_crd, method_name):
    """Returns the given method for the given source kind.

    Because every source has its own methods for rpc requests, this helper is
    used to get the underlying methods for a request against a given source
    type. Preferred usage of this private message is via the public
    methods: self.Source{Method_name}Method.

    Args:
      source_crd: custom_resource_definition.SourceCustomResourceDefinition,
        source CRD of the type we want to make a request against.
      method_name: str, the method name (e.g. "get", "create", "list", etc.)

    Returns:
      registry.APIMethod, holds information for the requested method.
    """
    return registry.GetMethod(
        util.SOURCE_COLLECTION_NAME.format(
            plural_kind=source_crd.source_kind_plural), method_name)

  def SourceGetMethod(self, source_crd):
    """Returns the request method for a Get request of this source."""
    return self._FindSourceMethod(source_crd, 'get')

  def SourceCreateMethod(self, source_crd):
    """Returns the request method for a Create request of this source."""
    return self._FindSourceMethod(source_crd, 'create')

  def SourceDeleteMethod(self, source_crd):
    """Returns the request method for a Delete request of this source."""
    return self._FindSourceMethod(source_crd, 'delete')

  def GetSource(self, source_ref, source_crd):
    """Returns the referenced source."""
    request_method = self.SourceGetMethod(source_crd)
    request_message_type = request_method.GetRequestType()
    request = request_message_type(name=source_ref.RelativeName())
    try:
      with metrics.RecordDuration(metric_names.GET_SOURCE):
        response = request_method.Call(request, client=self._client)
    except api_exceptions.HttpNotFoundError:
      return None
    return source.Source(response, self.messages, source_crd.source_kind)

  def CreateSource(self, source_obj, source_crd, owner_trigger, namespace_ref,
                   broker, parameters):
    """Create an source with the specified event type and owner trigger.

    Args:
      source_obj: source.Source. The source object being created.
      source_crd: custom_resource_definition.SourceCRD, the source crd for the
        source to create
      owner_trigger: trigger.Trigger, trigger to associate as an owner of the
        source.
      namespace_ref: googlecloudsdk.core.resources.Resource, namespace resource.
      broker: str, name of the broker to act as a sink.
      parameters: dict, additional parameters to set on the source spec.

    Returns:
      source.Source of the created source.
    """
    source_obj.ce_overrides[trigger.SOURCE_TRIGGER_LINK_FIELD] = (
        owner_trigger.filter_attributes[trigger.SOURCE_TRIGGER_LINK_FIELD])
    source_obj.owners.append(
        self.messages.OwnerReference(
            apiVersion=owner_trigger.apiVersion,
            kind=owner_trigger.kind,
            name=owner_trigger.name,
            uid=owner_trigger.uid,
            controller=True))
    source_obj.sink = broker
    arg_utils.ParseStaticFieldsIntoMessage(source_obj.spec, parameters)

    request_method = self.SourceCreateMethod(source_crd)
    request_message_type = request_method.GetRequestType()
    request = request_message_type(**{
        request_method.request_field: source_obj.Message(),
        'parent': namespace_ref.RelativeName()})
    try:
      with metrics.RecordDuration(metric_names.CREATE_SOURCE):
        response = request_method.Call(request, client=self._client)
    except api_exceptions.HttpConflictError:
      raise exceptions.SourceCreationError(
          'Source [{}] already exists.'.format(source_obj.name))

    return source.Source(response, self.messages, source_crd.source_kind)

  def PollSource(self, source_obj, event_type, tracker):
    """Wait for source to be Ready == True."""
    source_ref = util.GetSourceRef(
        source_obj.name, source_obj.namespace, event_type.crd)
    source_getter = functools.partial(
        self.GetSource, source_ref, event_type.crd)
    poller = SourceConditionPoller(source_getter, tracker,
                                   stages.TriggerSourceDependencies())
    util.WaitForCondition(poller, exceptions.SourceCreationError)
    # Manually complete the stage indicating source readiness because we can't
    # track the Ready condition in the ConditionPoller.
    tracker.CompleteStage(stages.SOURCE_READY)

  def DeleteSource(self, source_ref, source_crd):
    """Deletes the referenced source."""
    request_method = self.SourceDeleteMethod(source_crd)
    request_message_type = request_method.GetRequestType()
    request = request_message_type(name=source_ref.RelativeName())
    try:
      with metrics.RecordDuration(metric_names.DELETE_SOURCE):
        request_method.Call(request, client=self._client)
    except api_exceptions.HttpNotFoundError:
      raise exceptions.SourceNotFound(
          '{} events source [{}] not found.'.format(
              source_crd.source_kind, source_ref.Name()))

  def ListSourceCustomResourceDefinitions(self):
    """Returns a list of CRDs for event sources."""
    # Passing the parent field is only needed for hosted, but shouldn't hurt
    # against an actual cluster
    namespace_ref = resources.REGISTRY.Parse(
        properties.VALUES.core.project.Get(), collection='run.namespaces')

    messages = self._crd_client.MESSAGES_MODULE
    request = messages.RunCustomresourcedefinitionsListRequest(
        parent=namespace_ref.RelativeName(),
        labelSelector=_EVENT_SOURCES_LABEL_SELECTOR)
    with metrics.RecordDuration(metric_names.LIST_SOURCE_CRDS):
      response = self._crd_client.customresourcedefinitions.List(request)
    source_crds = [
        custom_resource_definition.SourceCustomResourceDefinition(
            item, messages) for item in response.items
    ]
    # Only include CRDs for source kinds that are defined in the api.
    return [s for s in source_crds if hasattr(self.messages, s.source_kind)]

  def UpdateNamespaceWithLabels(self, namespace_ref, labels):
    """Updates an existing namespace with the labels provided.

    If a label already exists, this will replace that label with the value
    provided. This is akin to specifying --overwrite with kubectl.

    Args:
      namespace_ref: googlecloudsdk.core.resources.Resource, namespace resource.
        Note that this should be of the collection "run.api.v1.namespaces" and
        *not* "run.namespaces".
      labels: map[str, str] of label keys and values to patch.

    Returns:
      Namespace that was patched.
    """
    messages = self._core_client.MESSAGES_MODULE
    namespace = messages.Namespace()
    arg_utils.SetFieldInMessage(namespace, _METADATA_LABELS_FIELD, labels)

    old_additional_headers = {}
    try:
      # We need to specify a special content-type for k8s to accept our PATCH.
      # However, this appears to only be settable at the client level, not at
      # the request level. So we'll update the client for our request, and the
      # set it back to the old value afterwards.
      old_additional_headers = self._core_client.additional_http_headers
      additional_headers = old_additional_headers.copy()
      additional_headers['content-type'] = 'application/merge-patch+json'
      self._core_client.additional_http_headers = additional_headers
    except AttributeError:
      # TODO(b/150229881): Remove this try/except block and below.
      # The mocked test client does not have an additional_http_headers attr
      # So we won't be able to test this part.
      pass
    with metrics.RecordDuration(metric_names.UPDATE_NAMESPACE):
      try:
        request = messages.RunApiV1NamespacesPatchRequest(
            name=namespace_ref.RelativeName(),
            namespace=namespace,
            updateMask=_METADATA_LABELS_FIELD)
        response = self._core_client.api_v1_namespaces.Patch(request)
      finally:
        try:
          self._core_client.additional_http_headers = old_additional_headers
        except AttributeError:
          # The mocked test client does not have an additional_http_headers attr
          pass
    return response

  def CreateOrReplaceServiceAccountSecret(self, secret_ref,
                                          service_account_ref):
    """Create a new secret or replace an existing one.

    Secret data contains the key of the given service account.

    Args:
      secret_ref: googlecloudsdk.core.resources.Resource, secret resource.
      service_account_ref: googlecloudsdk.core.resources.Resource, service
        account whose key will be used to create/replace the secret.

    Returns:
      (secret.Secret, googlecloudsdk.core.resources.Resource): tuple of the
        wrapped Secret resource and a ref to the created service account key.
    """
    secret_obj = secret.Secret.New(
        self._core_client, secret_ref.Parent().Name())
    secret_obj.name = secret_ref.Name()
    key = iam_util.CreateServiceAccountKey(service_account_ref)
    secret_obj.data['key.json'] = key.privateKeyData
    key_ref = resources.REGISTRY.ParseResourceId(
        _SERVICE_ACCOUNT_KEY_COLLECTION, key.name, {})

    messages = self._core_client.MESSAGES_MODULE
    with metrics.RecordDuration(metric_names.CREATE_OR_REPLACE_SECRET):
      # Create secret or replace if already exists.
      try:
        request = messages.RunApiV1NamespacesSecretsCreateRequest(
            secret=secret_obj.Message(),
            parent=secret_ref.Parent().RelativeName())
        response = self._core_client.api_v1_namespaces_secrets.Create(request)
      except api_exceptions.HttpConflictError:
        request = messages.RunApiV1NamespacesSecretsReplaceSecretRequest(
            secret=secret_obj.Message(),
            name=secret_ref.RelativeName())
        response = self._core_client.api_v1_namespaces_secrets.ReplaceSecret(
            request)
    return secret.Secret(response, messages), key_ref
