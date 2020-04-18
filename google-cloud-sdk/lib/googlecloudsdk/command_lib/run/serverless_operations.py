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
"""Allows you to write surfaces in terms of logical Serverless operations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import contextlib
import datetime
import functools

from apitools.base.py import encoding
from apitools.base.py import exceptions as api_exceptions
from apitools.base.py import list_pager
from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.api_lib.run import condition as run_condition
from googlecloudsdk.api_lib.run import configuration
from googlecloudsdk.api_lib.run import domain_mapping
from googlecloudsdk.api_lib.run import global_methods
from googlecloudsdk.api_lib.run import metric_names
from googlecloudsdk.api_lib.run import revision
from googlecloudsdk.api_lib.run import route
from googlecloudsdk.api_lib.run import service
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import apis_internal
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.command_lib.run import config_changes as config_changes_mod
from googlecloudsdk.command_lib.run import exceptions as serverless_exceptions
from googlecloudsdk.command_lib.run import name_generator
from googlecloudsdk.command_lib.run import resource_name_conversion
from googlecloudsdk.command_lib.run import stages
from googlecloudsdk.core import config
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import metrics
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.core.util import retry
import six

DEFAULT_ENDPOINT_VERSION = 'v1'


# Wait 11 mins for each deployment. This is longer than the server timeout,
# making it more likely to get a useful error message from the server.
MAX_WAIT_MS = 660000

ALLOW_UNAUTH_POLICY_BINDING_MEMBER = 'allUsers'
ALLOW_UNAUTH_POLICY_BINDING_ROLE = 'roles/run.invoker'

NEEDED_IAM_PERMISSIONS = ['run.services.setIamPolicy']


class UnknownAPIError(exceptions.Error):
  pass


@contextlib.contextmanager
def Connect(conn_context):
  """Provide a ServerlessOperations instance to use.

  If we're using the GKE Serverless Add-on, connect to the relevant cluster.
  Otherwise, connect to the right region of GSE.

  Arguments:
    conn_context: a context manager that yields a ConnectionInfo and manages a
      dynamic context that makes connecting to serverless possible.

  Yields:
    A ServerlessOperations instance.
  """

  # The One Platform client is required for making requests against
  # endpoints that do not supported Kubernetes-style resource naming
  # conventions. The One Platform client must be initialized outside of a
  # connection context so that it does not pick up the api_endpoint_overrides
  # values from the connection context.
  # pylint: disable=protected-access
  op_client = apis.GetClientInstance(
      conn_context.api_name,
      conn_context.api_version)
  # pylint: enable=protected-access

  with conn_context as conn_info:
    # pylint: disable=protected-access
    client = apis_internal._GetClientInstance(
        conn_info.api_name,
        conn_info.api_version,
        # Only check response if not connecting to GKE
        check_response_func=apis.CheckResponseForApiEnablement()
        if conn_context.supports_one_platform else None,
        http_client=conn_context.HttpClient())
    # pylint: enable=protected-access
    yield ServerlessOperations(
        client,
        conn_info.api_name,
        conn_info.api_version,
        conn_info.region,
        op_client)


class DomainMappingResourceRecordPoller(waiter.OperationPoller):
  """Poll for when a DomainMapping first has resourceRecords."""

  def __init__(self, ops):
    self._ops = ops

  def IsDone(self, mapping):
    if getattr(mapping.status, 'resourceRecords', None):
      return True
    conditions = mapping.conditions
    # pylint: disable=g-bool-id-comparison
    # False (indicating failure) as distinct from None (indicating not sure yet)
    if conditions and conditions['Ready']['status'] is False:
      return True
    # pylint: enable=g-bool-id-comparison
    return False

  def GetResult(self, mapping):
    return mapping

  def Poll(self, domain_mapping_ref):
    return self._ops.GetDomainMapping(domain_mapping_ref)


class ConditionPoller(waiter.OperationPoller):
  """A poller for CloudRun resource creation or update.

  Takes in a reference to a StagedProgressTracker, and updates it with progress.
  """

  def __init__(self,
               resource_getter,
               tracker,
               dependencies=None,
               ready_message='Done.'):
    """Initialize the ConditionPoller.

    Start any unblocked stages in the tracker immediately.

    Arguments:
      resource_getter: function, returns a resource with conditions.
      tracker: a StagedProgressTracker to keep updated. It must contain a stage
        for each condition in the dependencies map, if the dependencies map
        is provided.

        The stage represented by each key can only start when the set of
        conditions in the corresponding value have all completed. If a condition
        should be managed by this ConditionPoller but depends on nothing, it
        should map to an empty set. Conditions in the tracker but *not*
        managed by the ConditionPoller should not appear in the dict.

      dependencies: Dict[str, Set[str]], The dependencies between conditions
        that are managed by this ConditionPoller. The values are the set of
        conditions that must become true before the key begins being worked on
        by the server.

        If the entire dependencies dict is None, the poller will assume that
        all keys in the tracker are relevant and none have dependencies.

      ready_message: str, message to display in header of tracker when
        conditions are ready.
    """
    # _dependencies is a map of condition -> {preceding conditions}
    # It is meant to be checked off as we finish things.
    self._dependencies = {k: set() for k in tracker}
    if dependencies is not None:
      for k in dependencies:
        # Add dependencies, only if they're still not complete. If a stage isn't
        # in the tracker. consider it "already complete".
        self._dependencies[k] = {
            c for c in dependencies[k]
            if c in tracker and not tracker.IsComplete(c)}
    self._resource_getter = resource_getter
    self._tracker = tracker
    self._resource_fail_type = exceptions.Error
    self._ready_message = ready_message
    self._StartUnblocked()

  def _IsBlocked(self, condition):
    return condition in self._dependencies and self._dependencies[condition]

  def IsDone(self, conditions):
    """Overrides.

    Args:
      conditions: A condition.Conditions object.

    Returns:
      a bool indicates whether `conditions` is terminal.
    """
    if conditions is None:
      return False
    return conditions.IsTerminal()

  def _PollTerminalSubconditions(self, conditions, conditions_message):
    for condition in conditions.TerminalSubconditions():
      if condition not in self._dependencies:
        continue
      message = conditions[condition]['message']
      status = conditions[condition]['status']
      self._PossiblyUpdateMessage(condition, message, conditions_message)
      if status is None:
        continue
      elif status:
        if self._PossiblyCompleteStage(
            condition, message, conditions.IsReady()):
          # Check all terminal subconditions again to ensure any stages that
          # were unblocked by this stage completing are re-checked before we
          # check the ready condition
          self._PollTerminalSubconditions(conditions, conditions_message)
          break
      else:
        self._PossiblyFailStage(condition, message)

  def Poll(self, unused_ref):
    """Overrides.

    Args:
      unused_ref: A string representing the operation reference. Currently it
        must be 'deploy'.

    Returns:
      A condition.Conditions object.
    """
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
    elif conditions.IsFailed():
      raise self._resource_fail_type(conditions_message)

    return conditions

  def _PossiblyUpdateMessage(self, condition, message, conditions_message):
    """Update the stage message.

    Args:
      condition: str, The name of the status condition.
      message: str, The new message to display
      conditions_message: str, The message from the conditions object we're
        displaying..
    """
    if condition not in self._tracker or self._tracker.IsComplete(condition):
      return

    if self._IsBlocked(condition):
      return

    if message != conditions_message:
      self._tracker.UpdateStage(condition, message)

  def _RecordConditionComplete(self, condition):
    """Take care of the internal-to-this-class bookkeeping stage complete."""
    # Unblock anything that was blocked on this.

    # Strategy: "check off" each dependency as we complete it by removing from
    # the set in the value.
    for requirements in self._dependencies.values():
      requirements.discard(condition)

  def _PossiblyCompleteStage(self, condition, message, ready):
    """Complete the stage if it's not already complete.

    Make sure the necessary internal bookkeeping is done.

    Args:
      condition: str, The name of the condition whose stage should be completed.
      message: str, The detailed message for the condition.
      ready: boolean, True if the Ready condition is true.

    Returns:
      bool: True if stage was completed, False if no action taken
    """
    if condition not in self._tracker or self._tracker.IsComplete(condition):
      return False
    # A blocked condition is likely to remain True (indicating the previous
    # operation concerning it was successful) until the blocking condition(s)
    # finish and it's time to switch to Unknown (the current operation
    # concerning it is in progress). Don't mark those done before they switch to
    # Unknown.
    if not self._tracker.IsRunning(condition):
      return False
    self._RecordConditionComplete(condition)
    self._StartUnblocked()
    self._tracker.CompleteStage(condition, message)
    return True

  def _StartUnblocked(self):

    """Call StartStage in the tracker for any not-started not-blocked tasks.

    Record the fact that they're started in our internal bookkeeping.
    """
    # The set of stages that aren't marked started and don't have unsatisfied
    # dependencies are newly unblocked.
    for c in self._dependencies:
      if c not in self._tracker:
        continue
      if self._tracker.IsWaiting(c) and not self._IsBlocked(c):
        self._tracker.StartStage(c)
    # TODO(b/120679874): Should not have to manually call Tick()
    self._tracker.Tick()

  def _PossiblyFailStage(self, condition, message):
    """Possibly fail the stage.

    Args:
      condition: str, The name of the status whose stage failed.
      message: str, The detailed message for the condition.

    Raises:
      DeploymentFailedError: If the 'Ready' condition failed.
    """
    # Don't fail an already failed stage.
    if condition not in self._tracker or self._tracker.IsComplete(condition):
      return

    self._tracker.FailStage(
        condition,
        self._resource_fail_type(message),
        message)

  def GetResult(self, conditions):
    """Overrides.

    Get terminal conditions as the polling result.

    Args:
      conditions: A condition.Conditions object.

    Returns:
      A condition.Conditions object.
    """
    return conditions

  def GetConditions(self):
    """Returns the resource conditions wrapped in condition.Conditions.

    Returns:
      A condition.Conditions object.
    """
    resource = self._resource_getter()

    if resource is None:
      return None
    return resource.conditions


class ServiceConditionPoller(ConditionPoller):
  """A ConditionPoller for services."""

  def __init__(self, getter, tracker, dependencies=None, serv=None):
    def GetIfProbablyNewer():
      """Workaround for https://github.com/knative/serving/issues/4149).

      The workaround is to wait for the condition lastTransitionTime to
      change. Note that the granularity of lastTransitionTime is seconds
      so to avoid hanging in the unlikely case that two updates happen
      in the same second we limit waiting for the change to 5 seconds.

      Returns:
        The requested resource or None if it seems stale.
      """
      resource = getter()
      if (resource
          and self._old_last_transition_time
          and self._old_last_transition_time == resource.last_transition_time
          and not self.HaveFiveSecondsPassed()):
        return None
      else:
        return resource

    super(ServiceConditionPoller, self).__init__(
        GetIfProbablyNewer, tracker, dependencies)
    self._resource_fail_type = serverless_exceptions.DeploymentFailedError
    self._old_last_transition_time = serv.last_transition_time if serv else None
    self._start_time = datetime.datetime.now()
    self._five_seconds = datetime.timedelta(seconds=5)

  def HaveFiveSecondsPassed(self):
    return datetime.datetime.now() - self._start_time > self._five_seconds


class _NewRevisionForcingChange(config_changes_mod.ConfigChanger):
  """Forces a new revision to get created by changing the revision name."""

  def __init__(self, revision_suffix):
    self._revision_name_change = config_changes_mod.RevisionNameChanges(
        revision_suffix)

  def Adjust(self, resource):
    """Adjust by revision name."""
    if revision.NONCE_LABEL in resource.template.labels:
      del resource.template.labels[revision.NONCE_LABEL]
    return self._revision_name_change.Adjust(resource)


def _IsDigest(url):
  """Return true if the given image url is by-digest."""
  return '@sha256:' in url


class RevisionNameBasedPoller(waiter.OperationPoller):
  """Poll for the revision with the given name to exist."""

  def __init__(self, operations, revision_ref_getter):
    self._operations = operations
    self._revision_ref_getter = revision_ref_getter

  def IsDone(self, revision_obj):
    return bool(revision_obj)

  def Poll(self, revision_name):
    revision_ref = self._revision_ref_getter(revision_name)
    return self._operations.GetRevision(revision_ref)

  def GetResult(self, revision_obj):
    return revision_obj


class NonceBasedRevisionPoller(waiter.OperationPoller):
  """To poll for exactly one revision with the given nonce to appear."""

  def __init__(self, operations, namespace_ref):
    self._operations = operations
    self._namespace = namespace_ref

  def IsDone(self, revisions):
    return bool(revisions)

  def Poll(self, nonce):
    return self._operations.GetRevisionsByNonce(self._namespace, nonce)

  def GetResult(self, revisions):
    if len(revisions) == 1:
      return revisions[0]
    return None


class _SwitchToDigestChange(config_changes_mod.ConfigChanger):
  """Switches the configuration from by-tag to by-digest."""

  def __init__(self, base_revision):
    self._base_revision = base_revision

  def Adjust(self, resource):
    if _IsDigest(self._base_revision.image):
      return resource
    if not self._base_revision.image_digest:
      return resource

    # Mutates through to metadata: Save the by-tag user intent.
    resource.annotations[revision.USER_IMAGE_ANNOTATION] = (
        self._base_revision.image)
    resource.template.annotations[revision.USER_IMAGE_ANNOTATION] = (
        self._base_revision.image)
    resource.template.image = self._base_revision.image_digest
    return resource

_CLIENT_NAME_ANNOTATION = 'run.googleapis.com/client-name'
_CLIENT_NAME = 'gcloud'
_CLIENT_VERSION_ANNOTATION = 'run.googleapis.com/client-version'


class _SetClientNameAndVersion(config_changes_mod.ConfigChanger):
  """Sets the client name and version annotations."""

  def Adjust(self, resource):
    resource.annotations[_CLIENT_NAME_ANNOTATION] = _CLIENT_NAME
    resource.template.annotations[_CLIENT_NAME_ANNOTATION] = _CLIENT_NAME
    resource.annotations[_CLIENT_VERSION_ANNOTATION] = config.CLOUD_SDK_VERSION
    resource.template.annotations[
        _CLIENT_VERSION_ANNOTATION] = config.CLOUD_SDK_VERSION
    return resource


class ServerlessOperations(object):
  """Client used by Serverless to communicate with the actual Serverless API.
  """

  def __init__(self, client, api_name, api_version, region, op_client):
    """Inits ServerlessOperations with given API clients.

    Args:
      client: The API client for interacting with Kubernetes Cloud Run APIs.
      api_name: str, The name of the Cloud Run API.
      api_version: str, The version of the Cloud Run API.
      region: str, The region of the control plane if operating against
        hosted Cloud Run, else None.
      op_client: The API client for interacting with One Platform APIs. Or
        None if interacting with Cloud Run for Anthos.
    """
    self._client = client
    self._registry = resources.REGISTRY.Clone()
    self._registry.RegisterApiByName(api_name, api_version)
    self._op_client = op_client
    self._region = region

  @property
  def messages_module(self):
    return self._client.MESSAGES_MODULE

  def GetRevision(self, revision_ref):
    """Get the revision.

    Args:
      revision_ref: Resource, revision to get.

    Returns:
      A revision.Revision object.
    """
    messages = self.messages_module
    revision_name = revision_ref.RelativeName()
    request = messages.RunNamespacesRevisionsGetRequest(
        name=revision_name)
    try:
      with metrics.RecordDuration(metric_names.GET_REVISION):
        response = self._client.namespaces_revisions.Get(request)
      return revision.Revision(response, messages)
    except api_exceptions.HttpNotFoundError:
      return None

  def Upload(self, deployable):
    """Upload the code for the given deployable."""
    deployable.UploadFiles()

  def _GetRoute(self, service_ref):
    """Return the relevant Route from the server, or None if 404."""
    messages = self.messages_module
    # GET the Route
    route_name = self._registry.Parse(
        service_ref.servicesId,
        params={
            'namespacesId': service_ref.namespacesId,
        },
        collection='run.namespaces.routes').RelativeName()
    route_get_request = messages.RunNamespacesRoutesGetRequest(
        name=route_name,
    )

    try:
      with metrics.RecordDuration(metric_names.GET_ROUTE):
        route_get_response = self._client.namespaces_routes.Get(
            route_get_request)
      return route.Route(route_get_response, messages)
    except api_exceptions.HttpNotFoundError:
      return None

  def WaitForCondition(self, poller):
    """Wait for a configuration to be ready in latest revision.

    Args:
      poller: A ConditionPoller object.

    Returns:
      A condition.Conditions object.

    Raises:
      RetryException: Max retry limit exceeded.
      ConfigurationError: configuration failed to
    """

    try:
      return waiter.PollUntilDone(poller, None, wait_ceiling_ms=1000)
    except retry.RetryException as err:
      conditions = poller.GetConditions()
      # err.message already indicates timeout. Check ready_cond_type for more
      # information.
      msg = conditions.DescriptiveMessage() if conditions else None
      if msg:
        log.error('Still waiting: {}'.format(msg))
      raise err
    if not conditions.IsReady():
      raise serverless_exceptions.ConfigurationError(
          conditions.DescriptiveMessage())

  def GetActiveRevisions(self, service_ref):
    """Return the actively serving revisions.

    Args:
      service_ref: the service Resource reference.

    Returns:
      {str, int}, A dict mapping revisionID to its traffic percentage target.

    Raises:
      serverless_exceptions.NoActiveRevisionsError: if no serving revisions
        were found.
    """
    serv_route = self._GetRoute(service_ref)
    active_revisions = serv_route.active_revisions

    if len(active_revisions) < 1:
      raise serverless_exceptions.NoActiveRevisionsError()

    return serv_route.active_revisions

  def ListServices(self, namespace_ref):
    messages = self.messages_module
    request = messages.RunNamespacesServicesListRequest(
        parent=namespace_ref.RelativeName())
    with metrics.RecordDuration(metric_names.LIST_SERVICES):
      response = self._client.namespaces_services.List(request)
    return [service.Service(item, messages) for item in response.items]

  def ListConfigurations(self, namespace_ref):
    messages = self.messages_module
    request = messages.RunNamespacesConfigurationsListRequest(
        parent=namespace_ref.RelativeName())
    with metrics.RecordDuration(metric_names.LIST_CONFIGURATIONS):
      response = self._client.namespaces_configurations.List(request)
    return [configuration.Configuration(item, messages)
            for item in response.items]

  def ListRoutes(self, namespace_ref):
    messages = self.messages_module
    request = messages.RunNamespacesRoutesListRequest(
        parent=namespace_ref.RelativeName())
    with metrics.RecordDuration(metric_names.LIST_ROUTES):
      response = self._client.namespaces_routes.List(request)
    return [route.Route(item, messages) for item in response.items]

  def GetService(self, service_ref):
    """Return the relevant Service from the server, or None if 404."""
    messages = self.messages_module
    service_get_request = messages.RunNamespacesServicesGetRequest(
        name=service_ref.RelativeName())

    try:
      with metrics.RecordDuration(metric_names.GET_SERVICE):
        service_get_response = self._client.namespaces_services.Get(
            service_get_request)
      return service.Service(service_get_response, messages)
    except api_exceptions.HttpNotFoundError:
      return None

  def GetConfiguration(self, service_or_configuration_ref):
    """Return the relevant Configuration from the server, or None if 404."""
    messages = self.messages_module
    if hasattr(service_or_configuration_ref, 'servicesId'):
      name = self._registry.Parse(
          service_or_configuration_ref.servicesId,
          params={
              'namespacesId': service_or_configuration_ref.namespacesId,
          },
          collection='run.namespaces.configurations').RelativeName()
    else:
      name = service_or_configuration_ref.RelativeName()
    configuration_get_request = (
        messages.RunNamespacesConfigurationsGetRequest(
            name=name))

    try:
      with metrics.RecordDuration(metric_names.GET_CONFIGURATION):
        configuration_get_response = self._client.namespaces_configurations.Get(
            configuration_get_request)
      return configuration.Configuration(configuration_get_response, messages)
    except api_exceptions.HttpNotFoundError:
      return None

  def GetRoute(self, service_or_route_ref):
    """Return the relevant Route from the server, or None if 404."""
    messages = self.messages_module
    if hasattr(service_or_route_ref, 'servicesId'):
      name = self._registry.Parse(
          service_or_route_ref.servicesId,
          params={
              'namespacesId': service_or_route_ref.namespacesId,
          },
          collection='run.namespaces.routes').RelativeName()
    else:
      name = service_or_route_ref.RelativeName()
    route_get_request = (
        messages.RunNamespacesRoutesGetRequest(
            name=name))

    try:
      with metrics.RecordDuration(metric_names.GET_ROUTE):
        route_get_response = self._client.namespaces_routes.Get(
            route_get_request)
      return route.Route(route_get_response, messages)
    except api_exceptions.HttpNotFoundError:
      return None

  def DeleteService(self, service_ref):
    """Delete the provided Service.

    Args:
      service_ref: Resource, a reference to the Service to delete

    Raises:
      ServiceNotFoundError: if provided service is not found.
    """
    messages = self.messages_module
    service_name = service_ref.RelativeName()
    service_delete_request = messages.RunNamespacesServicesDeleteRequest(
        name=service_name,
    )

    try:
      with metrics.RecordDuration(metric_names.DELETE_SERVICE):
        self._client.namespaces_services.Delete(service_delete_request)
    except api_exceptions.HttpNotFoundError:
      raise serverless_exceptions.ServiceNotFoundError(
          'Service [{}] could not be found.'.format(service_ref.servicesId))

  def DeleteRevision(self, revision_ref):
    """Delete the provided Revision.

    Args:
      revision_ref: Resource, a reference to the Revision to delete

    Raises:
      RevisionNotFoundError: if provided revision is not found.
    """
    messages = self.messages_module
    revision_name = revision_ref.RelativeName()
    request = messages.RunNamespacesRevisionsDeleteRequest(
        name=revision_name)
    try:
      with metrics.RecordDuration(metric_names.DELETE_REVISION):
        self._client.namespaces_revisions.Delete(request)
    except api_exceptions.HttpNotFoundError:
      raise serverless_exceptions.RevisionNotFoundError(
          'Revision [{}] could not be found.'.format(revision_ref.revisionsId))

  def GetRevisionsByNonce(self, namespace_ref, nonce):
    """Return all revisions with the given nonce."""
    messages = self.messages_module
    request = messages.RunNamespacesRevisionsListRequest(
        parent=namespace_ref.RelativeName(),
        labelSelector='{} = {}'.format(revision.NONCE_LABEL, nonce))
    response = self._client.namespaces_revisions.List(request)
    return [revision.Revision(item, messages) for item in response.items]

  def _GetBaseRevision(self, template, metadata, status):
    """Return a Revision for use as the "base revision" for a change.

    When making a change that should not affect the code running, the
    "base revision" is the revision that we should lock the code to - it's where
    we get the digest for the image to run.

    Getting this revision:
      * If there's a name in the template metadata, use that
      * If there's a nonce in the revisonTemplate metadata, use that
      * If that query produces >1 or 0 after a short timeout, use
        the latestCreatedRevision in status.

    Arguments:
      template: Revision, the revision template to get the base revision of.
        May have been derived from a Service.
      metadata: ObjectMeta, the metadata from the top-level object
      status: Union[ConfigurationStatus, ServiceStatus], the status of the top-
        level object.

    Returns:
      The base revision of the configuration or None if not found by revision
        name nor nonce and latestCreatedRevisionName does not exist on the
        Service object.
    """
    base_revision = None
    # Try to find by revision name
    base_revision_name = template.name
    if base_revision_name:
      try:
        revision_ref_getter = functools.partial(
            self._registry.Parse,
            params={'namespacesId': metadata.namespace},
            collection='run.namespaces.revisions')
        poller = RevisionNameBasedPoller(self, revision_ref_getter)
        base_revision = poller.GetResult(
            waiter.PollUntilDone(
                poller, base_revision_name, sleep_ms=500, max_wait_ms=2000))
      except retry.RetryException:
        pass
    # Name polling didn't work. Fall back to nonce polling
    if not base_revision:
      base_revision_nonce = template.labels.get(revision.NONCE_LABEL, None)
      if base_revision_nonce:
        try:
          # TODO(b/150322097): Remove this when the api has been split.
          # This try/except block is needed because the v1alpha1 and v1 run apis
          # have different collection names for the namespaces.
          try:
            namespace_ref = self._registry.Parse(
                metadata.namespace,
                collection='run.namespaces')
          except resources.InvalidCollectionException:
            namespace_ref = self._registry.Parse(
                metadata.namespace,
                collection='run.api.v1.namespaces')
          poller = NonceBasedRevisionPoller(self, namespace_ref)
          base_revision = poller.GetResult(waiter.PollUntilDone(
              poller, base_revision_nonce,
              sleep_ms=500, max_wait_ms=2000))
        except retry.RetryException:
          pass
    # Nonce polling didn't work, because some client didn't post one or didn't
    # change one. Fall back to the (slightly racy) `latestCreatedRevisionName`.
    if not base_revision:
      # TODO(b/117663680) Getattr -> normal access.
      if getattr(status, 'latestCreatedRevisionName', None):
        # Get by latestCreatedRevisionName
        revision_ref = self._registry.Parse(
            status.latestCreatedRevisionName,
            params={'namespacesId': metadata.namespace},
            collection='run.namespaces.revisions')
        base_revision = self.GetRevision(revision_ref)
    return base_revision

  def _EnsureImageDigest(self, serv, config_changes):
    """Make config_changes include switch by-digest image if not so already."""
    if not _IsDigest(serv.template.image):
      base_revision = self._GetBaseRevision(
          serv.template, serv.metadata, serv.status)
      if base_revision:
        config_changes.append(_SwitchToDigestChange(base_revision))

  def _UpdateOrCreateService(
      self, service_ref, config_changes, with_code, serv):
    """Apply config_changes to the service. Create it if necessary.

    Arguments:
      service_ref: Reference to the service to create or update
      config_changes: list of ConfigChanger to modify the service with
      with_code: bool, True if the config_changes contains code to deploy.
        We can't create the service if we're not deploying code.
      serv: service.Service, For update the Service to update and for
        create None.

    Returns:
      The Service object we created or modified.
    """
    messages = self.messages_module
    try:
      if serv:
        # PUT the changed Service
        for config_change in config_changes:
          serv = config_change.Adjust(serv)
        serv_name = service_ref.RelativeName()
        serv_update_req = (
            messages.RunNamespacesServicesReplaceServiceRequest(
                service=serv.Message(),
                name=serv_name))
        with metrics.RecordDuration(metric_names.UPDATE_SERVICE):
          updated = self._client.namespaces_services.ReplaceService(
              serv_update_req)
        return service.Service(updated, messages)

      else:
        if not with_code:
          raise serverless_exceptions.ServiceNotFoundError(
              'Service [{}] could not be found.'.format(service_ref.servicesId))
        # POST a new Service
        new_serv = service.Service.New(self._client, service_ref.namespacesId)
        new_serv.name = service_ref.servicesId
        parent = service_ref.Parent().RelativeName()
        for config_change in config_changes:
          new_serv = config_change.Adjust(new_serv)
        serv_create_req = (
            messages.RunNamespacesServicesCreateRequest(
                service=new_serv.Message(),
                parent=parent))
        with metrics.RecordDuration(metric_names.CREATE_SERVICE):
          raw_service = self._client.namespaces_services.Create(
              serv_create_req)
        return service.Service(raw_service, messages)
    except api_exceptions.HttpBadRequestError as e:
      exceptions.reraise(serverless_exceptions.HttpError(e))
    except api_exceptions.HttpNotFoundError as e:
      platform = properties.VALUES.run.platform.Get()
      error_msg = 'Deployment endpoint was not found.'
      if platform == 'gke':
        all_clusters = global_methods.ListClusters()
        clusters = ['* {} in {}'.format(c.name, c.zone) for c in all_clusters]
        error_msg += (' Perhaps the provided cluster was invalid or '
                      'does not have Cloud Run enabled. Pass the '
                      '`--cluster` and `--cluster-location` flags or set the '
                      '`run/cluster` and `run/cluster_location` properties to '
                      'a valid cluster and zone and retry.'
                      '\nAvailable clusters:\n{}'.format('\n'.join(clusters)))
      elif platform == 'managed':
        all_regions = global_methods.ListRegions(self._op_client)
        if self._region not in all_regions:
          regions = ['* {}'.format(r) for r in all_regions]
          error_msg += (' The provided region was invalid. '
                        'Pass the `--region` flag or set the '
                        '`run/region` property to a valid region and retry.'
                        '\nAvailable regions:\n{}'.format('\n'.join(regions)))
      elif platform == 'kubernetes':
        error_msg += (' Perhaps the provided cluster was invalid or '
                      'does not have Cloud Run enabled. Ensure in your '
                      'kubeconfig file that the cluster referenced in '
                      'the current context or the specified context '
                      'is a valid cluster and retry.')
      raise serverless_exceptions.DeploymentFailedError(error_msg)
    except api_exceptions.HttpError as e:
      platform = properties.VALUES.run.platform.Get()
      if platform == 'managed':
        exceptions.reraise(e)
      k8s_error = serverless_exceptions.KubernetesExceptionParser(e)
      causes = '\n\n'.join([c['message'] for c in k8s_error.causes])
      if not causes:
        causes = k8s_error.error
      raise serverless_exceptions.KubernetesError('Error{}:\n{}\n'.format(
          's' if len(k8s_error.causes) > 1 else '', causes))

  def UpdateTraffic(self, service_ref, config_changes, tracker, asyn):
    """Update traffic splits for service."""
    if tracker is None:
      tracker = progress_tracker.NoOpStagedProgressTracker(
          stages.UpdateTrafficStages(),
          interruptable=True,
          aborted_message='aborted')
    serv = self.GetService(service_ref)
    if not serv:
      raise serverless_exceptions.ServiceNotFoundError(
          'Service [{}] could not be found.'.format(service_ref.servicesId))

    if serv.configuration:
      raise serverless_exceptions.UnsupportedOperationError(
          'This service is using an old version of Cloud Run for Anthos '
          'that does not support traffic features. Please upgrade to 0.8 '
          'or later.')

    self._UpdateOrCreateService(service_ref, config_changes, False, serv)

    if not asyn:
      getter = functools.partial(self.GetService, service_ref)
      self.WaitForCondition(ServiceConditionPoller(getter, tracker, serv=serv))

  def _AddRevisionForcingChange(self, serv, config_changes):
    """Get a new revision forcing config change for the given service."""
    curr_generation = serv.generation if serv is not None else 0
    revision_suffix = '{}-{}'.format(
        str(curr_generation + 1).zfill(5), name_generator.GenerateName())
    config_changes.insert(0, _NewRevisionForcingChange(revision_suffix))

  def ReleaseService(self,
                     service_ref,
                     config_changes,
                     tracker=None,
                     asyn=False,
                     allow_unauthenticated=None,
                     for_replace=False,
                     prefetch=False,
                     build_op_ref=None,
                     build_log_url=None):
    """Change the given service in prod using the given config_changes.

    Ensures a new revision is always created, even if the spec of the revision
    has not changed.

    Arguments:
      service_ref: Resource, the service to release.
      config_changes: list, objects that implement Adjust().
      tracker: StagedProgressTracker, to report on the progress of releasing.
      asyn: bool, if True, return without waiting for the service to be updated.
      allow_unauthenticated: bool, True if creating a hosted Cloud Run
        service which should also have its IAM policy set to allow
        unauthenticated access. False if removing the IAM policy to allow
        unauthenticated access from a service.
      for_replace: bool, If the change is for a replacing the service from a
        YAML specification.
      prefetch: the service, pre-fetched for ReleaseService. `False` indicates
        the caller did not perform a prefetch; `None` indicates a nonexistant
        service.
      build_op_ref: The reference to the build.
      build_log_url: The log url of the build result.
    """
    if tracker is None:
      tracker = progress_tracker.NoOpStagedProgressTracker(
          stages.ServiceStages(allow_unauthenticated is not None),
          interruptable=True, aborted_message='aborted')
    if build_op_ref is not None:
      tracker.StartStage(stages.BUILD_READY)
      tracker.UpdateHeaderMessage('Building Container.')
      tracker.UpdateStage(
          stages.BUILD_READY, 'Logs are available at [{build_log_url}].'.format(
              build_log_url=build_log_url))
      client = cloudbuild_util.GetClientInstance()
      poller = waiter.CloudOperationPoller(client.projects_builds,
                                           client.operations)
      operation = waiter.PollUntilDone(poller, build_op_ref)
      response_dict = encoding.MessageToPyValue(operation.response)
      if response_dict and response_dict['status'] != 'SUCCESS':
        tracker.FailStage(
            stages.BUILD_READY, None,
            message='Container build failed and '
            'logs are available at [{build_log_url}].'.format(
                build_log_url=build_log_url))
        return
      else:
        tracker.CompleteStage(stages.BUILD_READY)
    if prefetch is None:
      serv = None
    else:
      serv = prefetch or self.GetService(service_ref)
    if for_replace:
      with_image = True
    else:
      with_image = any(
          isinstance(c, config_changes_mod.ImageChange) for c in config_changes)
      self._AddRevisionForcingChange(serv, config_changes)
      if serv and not with_image:
        # Avoid changing the running code by making the new revision by digest
        self._EnsureImageDigest(serv, config_changes)
    config_changes = [_SetClientNameAndVersion()] + config_changes

    self._UpdateOrCreateService(
        service_ref, config_changes, with_image, serv)

    if allow_unauthenticated is not None:
      try:
        tracker.StartStage(stages.SERVICE_IAM_POLICY_SET)
        tracker.UpdateStage(stages.SERVICE_IAM_POLICY_SET, '')
        self.AddOrRemoveIamPolicyBinding(service_ref, allow_unauthenticated,
                                         ALLOW_UNAUTH_POLICY_BINDING_MEMBER,
                                         ALLOW_UNAUTH_POLICY_BINDING_ROLE)
        tracker.CompleteStage(stages.SERVICE_IAM_POLICY_SET)
      except api_exceptions.HttpError:
        warning_message = (
            'Setting IAM policy failed, try "gcloud beta run services '
            '{}-iam-policy-binding --region={region} --member=allUsers '
            '--role=roles/run.invoker {service}"'.format(
                'add' if allow_unauthenticated else 'remove',
                region=self._region,
                service=service_ref.servicesId))
        tracker.CompleteStageWithWarning(
            stages.SERVICE_IAM_POLICY_SET, warning_message=warning_message)

    if not asyn:
      getter = functools.partial(self.GetService, service_ref)
      poller = ServiceConditionPoller(
          getter,
          tracker,
          dependencies=stages.ServiceDependencies(),
          serv=serv)
      self.WaitForCondition(poller)
      for msg in run_condition.GetNonTerminalMessages(poller.GetConditions()):
        tracker.AddWarning(msg)

  def ListRevisions(self, namespace_ref, service_name,
                    limit=None, page_size=100):
    """List all revisions for the given service.

    Revision list gets sorted by service name and creation timestamp.

    Args:
      namespace_ref: Resource, namespace to list revisions in
      service_name: str, The service for which to list revisions.
      limit: Optional[int], max number of revisions to list.
      page_size: Optional[int], number of revisions to fetch at a time

    Yields:
      Revisions for the given surface
    """
    messages = self.messages_module
    # NB: This is a hack to compensate for apitools not generating this line.
    #     It's necessary to make the URL parameter be "continue".
    encoding.AddCustomJsonFieldMapping(
        messages.RunNamespacesRevisionsListRequest, 'continue_', 'continue')
    request = messages.RunNamespacesRevisionsListRequest(
        parent=namespace_ref.RelativeName(),
    )
    if service_name is not None:
      # For now, same as the service name, and keeping compatible with
      # 'service-less' operation.
      request.labelSelector = 'serving.knative.dev/service = {}'.format(
          service_name)
    for result in list_pager.YieldFromList(
        service=self._client.namespaces_revisions,
        request=request,
        limit=limit,
        batch_size=page_size,
        current_token_attribute='continue_',
        next_token_attribute=('metadata', 'continue_'),
        batch_size_attribute='limit'):
      yield revision.Revision(result, messages)

  def ListDomainMappings(self, namespace_ref):
    """List all domain mappings.

    Args:
      namespace_ref: Resource, namespace to list domain mappings in.

    Returns:
      A list of domain mappings.
    """
    messages = self.messages_module
    request = messages.RunNamespacesDomainmappingsListRequest(
        parent=namespace_ref.RelativeName())
    with metrics.RecordDuration(metric_names.LIST_DOMAIN_MAPPINGS):
      response = self._client.namespaces_domainmappings.List(request)
    return [domain_mapping.DomainMapping(item, messages)
            for item in response.items]

  def CreateDomainMapping(self,
                          domain_mapping_ref,
                          service_name,
                          force_override=False):
    """Create a domain mapping.

    Args:
      domain_mapping_ref: Resource, domainmapping resource.
      service_name: str, the service to which to map domain.
      force_override: bool, override an existing mapping of this domain.

    Returns:
      A domain_mapping.DomainMapping object.
    """

    messages = self.messages_module
    new_mapping = domain_mapping.DomainMapping.New(
        self._client, domain_mapping_ref.namespacesId)
    new_mapping.name = domain_mapping_ref.domainmappingsId
    new_mapping.route_name = service_name
    new_mapping.force_override = force_override

    request = messages.RunNamespacesDomainmappingsCreateRequest(
        domainMapping=new_mapping.Message(),
        parent=domain_mapping_ref.Parent().RelativeName())
    with metrics.RecordDuration(metric_names.CREATE_DOMAIN_MAPPING):
      try:
        response = self._client.namespaces_domainmappings.Create(request)
      except api_exceptions.HttpConflictError:
        raise serverless_exceptions.DomainMappingCreationError(
            'Domain mapping to [{}] for service [{}] already exists.'.format(
                domain_mapping_ref.Name(), service_name))
      # 'run domain-mappings create' is synchronous. Poll for its completion.x
      with progress_tracker.ProgressTracker('Creating...'):
        mapping = waiter.PollUntilDone(
            DomainMappingResourceRecordPoller(self), domain_mapping_ref)
      ready = mapping.conditions.get('Ready')
      message = None
      if ready and ready.get('message'):
        message = ready['message']
      if not mapping.records:
        raise serverless_exceptions.DomainMappingCreationError(
            message or 'Could not create domain mapping.')
      if message:
        log.status.Print(message)
      return mapping

    return domain_mapping.DomainMapping(response, messages)

  def DeleteDomainMapping(self, domain_mapping_ref):
    """Delete a domain mapping.

    Args:
      domain_mapping_ref: Resource, domainmapping resource.
    """
    messages = self.messages_module

    request = messages.RunNamespacesDomainmappingsDeleteRequest(
        name=domain_mapping_ref.RelativeName())
    with metrics.RecordDuration(metric_names.DELETE_DOMAIN_MAPPING):
      self._client.namespaces_domainmappings.Delete(request)

  def GetDomainMapping(self, domain_mapping_ref):
    """Get a domain mapping.

    Args:
      domain_mapping_ref: Resource, domainmapping resource.

    Returns:
      A domain_mapping.DomainMapping object.
    """
    messages = self.messages_module
    request = messages.RunNamespacesDomainmappingsGetRequest(
        name=domain_mapping_ref.RelativeName())
    with metrics.RecordDuration(metric_names.GET_DOMAIN_MAPPING):
      response = self._client.namespaces_domainmappings.Get(request)
    return domain_mapping.DomainMapping(response, messages)

  def _GetIamPolicy(self, service_name):
    """Gets the IAM policy for the service."""
    messages = self.messages_module
    request = messages.RunProjectsLocationsServicesGetIamPolicyRequest(
        resource=six.text_type(service_name))
    response = self._op_client.projects_locations_services.GetIamPolicy(request)
    return response

  def AddOrRemoveIamPolicyBinding(self, service_ref, add_binding=True,
                                  member=None, role=None):
    """Add or remove the given IAM policy binding to the provided service.

    If no members or role are provided, set the IAM policy to the current IAM
    policy. This is useful for checking whether the authenticated user has
    the appropriate permissions for setting policies.

    Args:
      service_ref: str, The service to which to add the IAM policy.
      add_binding: bool, Whether to add to or remove from the IAM policy.
      member: str, One of the users for which the binding applies.
      role: str, The role to grant the provided members.

    Returns:
      A google.iam.v1.TestIamPermissionsResponse.
    """
    messages = self.messages_module
    oneplatform_service = resource_name_conversion.K8sToOnePlatform(
        service_ref, self._region)
    policy = self._GetIamPolicy(oneplatform_service)
    # Don't modify bindings if not member or roles provided
    if member and role:
      if add_binding:
        iam_util.AddBindingToIamPolicy(messages.Binding, policy, member, role)
      elif iam_util.BindingInPolicy(policy, member, role):
        iam_util.RemoveBindingFromIamPolicy(policy, member, role)
    request = messages.RunProjectsLocationsServicesSetIamPolicyRequest(
        resource=six.text_type(oneplatform_service),
        setIamPolicyRequest=messages.SetIamPolicyRequest(policy=policy))
    result = self._op_client.projects_locations_services.SetIamPolicy(request)
    return result

  def CanSetIamPolicyBinding(self, service_ref):
    """Check if user has permission to set the iam policy on the service."""
    messages = self.messages_module
    oneplatform_service = resource_name_conversion.K8sToOnePlatform(
        service_ref, self._region)
    request = messages.RunProjectsLocationsServicesTestIamPermissionsRequest(
        resource=six.text_type(oneplatform_service),
        testIamPermissionsRequest=messages.TestIamPermissionsRequest(
            permissions=NEEDED_IAM_PERMISSIONS))
    response = self._op_client.projects_locations_services.TestIamPermissions(
        request)
    return set(NEEDED_IAM_PERMISSIONS).issubset(set(response.permissions))
