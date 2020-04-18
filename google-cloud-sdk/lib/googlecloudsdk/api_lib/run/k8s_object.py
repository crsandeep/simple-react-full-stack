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
"""Utilities for wrapping/dealing with a k8s-style objects."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import abc
import collections
from apitools.base.protorpclite import messages
from googlecloudsdk.api_lib.run import condition
from googlecloudsdk.core.console import console_attr

import six


SERVING_GROUP = 'serving.knative.dev'
AUTOSCALING_GROUP = 'autoscaling.knative.dev'
EVENTING_GROUP = 'eventing.knative.dev'
CLIENT_GROUP = 'client.knative.dev'

GOOGLE_GROUP = 'cloud.googleapis.com'
RUN_GROUP = 'run.googleapis.com'

INTERNAL_GROUPS = (
    CLIENT_GROUP, SERVING_GROUP, AUTOSCALING_GROUP, EVENTING_GROUP,
    GOOGLE_GROUP)


REGION_LABEL = GOOGLE_GROUP + '/location'


def Meta(m):
  """Metadta class from messages module."""
  if hasattr(m, 'ObjectMeta'):
    return m.ObjectMeta
  elif hasattr(m, 'K8sIoApimachineryPkgApisMetaV1ObjectMeta'):
    return m.K8sIoApimachineryPkgApisMetaV1ObjectMeta
  raise ValueError('Provided module does not have a known metadata class')


def ListMeta(m):
  """List Metadta class from messages module."""
  if hasattr(m, 'ListMeta'):
    return m.ListMeta
  elif hasattr(m, 'K8sIoApimachineryPkgApisMetaV1ListMeta'):
    return m.K8sIoApimachineryPkgApisMetaV1ListMeta
  raise ValueError('Provided module does not have a known metadata class')


def MakeMeta(m, *args, **kwargs):
  """Make metadata message from messages module."""
  return Meta(m)(*args, **kwargs)


def InitializedInstance(msg_cls, excluded_fields=None):
  """Produce an instance of msg_cls, with all sub-messages initialized.

  Args:
    msg_cls: A message-class to be instantiated.
    excluded_fields: [str], List of field names to exclude from instantiation.
  Returns:
    An instance of the given class, with all fields initialized blank objects.
  """
  def Instance(field):
    if field.repeated:
      return []
    return InitializedInstance(field.message_type, excluded_fields)

  def IncludeField(field):
    if not isinstance(field, messages.MessageField):
      return False

    if excluded_fields and field.name in excluded_fields:
      return False

    return True

  args = {
      field.name: Instance(field) for field in msg_cls.all_fields()
      if IncludeField(field)
  }
  return msg_cls(**args)


@six.add_metaclass(abc.ABCMeta)
class KubernetesObject(object):
  """Base class for wrappers around Kubernetes-style Object messages.

  Requires subclasses to provide class-level constants KIND for the k8s Kind
  field, and API_CATEGORY for the k8s API Category. It infers the API version
  from the version of the client object.

  Additionally, you can set READY_CONDITION and TERMINAL_CONDITIONS to be the
  name of a condition that indicates readiness, and a set of conditions
  indicating a steady state, respectively.
  """

  READY_CONDITION = 'Ready'
  # Message fields to exclude from instantiation of this object.
  FIELD_BLACKLIST = []

  @classmethod
  def Kind(cls, kind=None):
    """Returns the passed str if given, else the class KIND."""
    return kind if kind is not None else cls.KIND

  @classmethod
  def ApiCategory(cls, api_category=None):
    """Returns the passed str if given, else the class API_CATEGORY."""
    return api_category if api_category is not None else cls.API_CATEGORY

  @classmethod
  def ApiVersion(cls, api_version, api_category=None):
    """Returns the api version with group prefix if exists."""
    if api_category is None:
      return api_version
    return '{}/{}'.format(api_category, api_version)

  @classmethod
  def SpecOnly(cls, spec, messages_mod, kind=None):
    """Produces a wrapped message with only the given spec.

    It is meant to be used as part of another message; it will error if you
    try to access the metadata or status.

    Arguments:
      spec: messages.Message, The spec to include
      messages_mod: the messages module
      kind: str, the resource kind

    Returns:
      A new k8s_object with only the given spec.
    """
    msg_cls = getattr(messages_mod, cls.Kind(kind))
    return cls(msg_cls(spec=spec), messages_mod, kind)

  @classmethod
  def Template(cls, template, messages_mod, kind=None):
    """Wraps a template object: spec and metadata only, no status."""
    msg_cls = getattr(messages_mod, cls.Kind(kind))
    return cls(msg_cls(spec=template.spec, metadata=template.metadata),
               messages_mod, kind)

  @classmethod
  def New(cls, client, namespace, kind=None, api_category=None):
    """Produces a new wrapped message of the appropriate type.

    All the sub-objects in it are recursively initialized to the appropriate
    message types, and the kind, apiVersion, and namespace set.

    Arguments:
      client: the API client to use
      namespace: str, The namespace to create the object in
      kind: str, the resource kind
      api_category: str, the api group of the resource

    Returns:
      The newly created wrapped message.
    """
    api_category = cls.ApiCategory(api_category)
    api_version = cls.ApiVersion(getattr(client, '_VERSION'), api_category)
    messages_mod = client.MESSAGES_MODULE
    kind = cls.Kind(kind)
    ret = InitializedInstance(getattr(messages_mod, kind), cls.FIELD_BLACKLIST)
    try:
      ret.kind = kind
      ret.apiVersion = api_version
    except AttributeError:
      # TODO(b/113172423): Workaround. Some top-level messages don't have
      # apiVersion and kind yet but they should
      pass
    ret.metadata.namespace = namespace
    return cls(ret, messages_mod, kind)

  def __init__(self, to_wrap, messages_mod, kind=None):
    msg_cls = getattr(messages_mod, self.Kind(kind))
    if not isinstance(to_wrap, msg_cls):
      raise ValueError('Oops, trying to wrap wrong kind of message')
    self._m = to_wrap
    self._messages = messages_mod

  def MessagesModule(self):
    """Return the messages module."""
    return self._messages

  def AssertFullObject(self):
    if not self._m.metadata:
      raise ValueError('This instance is spec-only.')

  # Access the "raw" k8s message parts. When subclasses want to allow mutability
  # they should provide their own convenience properties with setters.
  @property
  def kind(self):
    self.AssertFullObject()
    return self._m.kind

  @property
  def apiVersion(self):  # pylint: disable=invalid-name
    self.AssertFullObject()
    return self._m.apiVersion

  @property
  def spec(self):
    return self._m.spec

  @property
  def status(self):
    self.AssertFullObject()
    return self._m.status

  @property
  def metadata(self):
    self.AssertFullObject()
    return self._m.metadata

  # Alias common bits of metadata to the top level, for convenience.
  @property
  def name(self):
    self.AssertFullObject()
    return self._m.metadata.name

  @name.setter
  def name(self, value):
    self.AssertFullObject()
    self._m.metadata.name = value

  @property
  def creation_timestamp(self):
    return self.metaddata.creationTimestamp

  @property
  def namespace(self):
    self.AssertFullObject()
    return self._m.metadata.namespace

  @namespace.setter
  def namespace(self, value):
    self.AssertFullObject()
    self._m.metadata.namespace = value

  @property
  def resource_version(self):
    self.AssertFullObject()
    return self._m.metadata.resourceVersion

  @property
  def self_link(self):
    self.AssertFullObject()
    return self._m.metadata.selfLink.lstrip('/')

  @property
  def uid(self):
    self.AssertFullObject()
    return self._m.metadata.uid

  @property
  def owners(self):
    self.AssertFullObject()
    return self._m.metadata.ownerReferences

  @property
  def is_managed(self):
    return REGION_LABEL in self.labels

  @property
  def region(self):
    self.AssertFullObject()
    return self.labels[REGION_LABEL]

  @property
  def generation(self):
    self.AssertFullObject()
    # For the hack where generation is in spec, it's worse than unpopulated in
    # the metadata; it's always `1`.
    # TODO(b/110275620): remove this hack.
    if getattr(self._m.spec, 'generation', None) is not None:
      return self._m.spec.generation
    return self._m.metadata.generation

  @generation.setter
  def generation(self, value):
    self._m.metadata.generation = value

  @property
  def conditions(self):
    self.AssertFullObject()
    if self._m.status:
      c = self._m.status.conditions
    else:
      c = []
    return condition.Conditions(
        c,
        self.READY_CONDITION,
        getattr(self._m.status, 'observedGeneration', None),
        self.generation,
    )

  @property
  def annotations(self):
    self.AssertFullObject()
    return AnnotationsFromMetadata(self._messages, self._m.metadata)

  @property
  def labels(self):
    self.AssertFullObject()
    return LabelsFromMetadata(self._messages, self._m.metadata)

  @property
  def ready_condition(self):
    assert hasattr(self, 'READY_CONDITION')
    if self.conditions and self.READY_CONDITION in self.conditions:
      return self.conditions[self.READY_CONDITION]

  @property
  def ready(self):
    assert hasattr(self, 'READY_CONDITION')
    if self.ready_condition:
      return self.ready_condition['status']

  @property
  def last_transition_time(self):
    assert hasattr(self, 'READY_CONDITION')
    return next((c.lastTransitionTime
                 for c in self.status.conditions
                 if c.type == self.READY_CONDITION), None)

  def _PickSymbol(self, best, alt, encoding):
    """Choose the best symbol (if it's in this encoding) or an alternate."""
    try:
      best.encode(encoding)
      return best
    except UnicodeError:
      return alt

  @property
  def ready_symbol(self):
    """Return a symbol summarizing the status of this object."""
    return self.ReadySymbolAndColor()[0]

  def ReadySymbolAndColor(self):
    """Return a tuple of ready_symbol and display color for this object."""
    # NB: This can be overridden by subclasses to allow symbols for more
    # complex reasons the object isn't ready. Ex: Service overrides it to
    # provide '!' for "I'm serving, but not the revision you wanted."
    encoding = console_attr.GetConsoleAttr().GetEncoding()
    if self.ready is None:
      return self._PickSymbol(
          '\N{HORIZONTAL ELLIPSIS}', '.', encoding), 'yellow'
    elif self.ready:
      return self._PickSymbol('\N{HEAVY CHECK MARK}', '+', encoding), 'green'
    else:
      return 'X', 'red'

  def AsObjectReference(self):
    return self._messages.ObjectReference(
        kind=self.kind,
        namespace=self.namespace,
        name=self.name,
        uid=self.uid,
        apiVersion=self.apiVersion)

  def Message(self):
    """Return the actual message we've wrapped."""
    return self._m

  def MakeSerializable(self):
    return self.Message()

  def MakeCondition(self, *args, **kwargs):
    if hasattr(self._messages, 'GoogleCloudRunV1Condition'):
      return self._messages.GoogleCloudRunV1Condition(*args, **kwargs)
    else:
      return getattr(self._messages, self.kind + 'Condition')(*args, **kwargs)

  def __eq__(self, other):
    if isinstance(other, type(self)):
      return self.Message() == other.Message()
    return False

  def __repr__(self):
    return '{}({})'.format(type(self).__name__, repr(self._m))


def AnnotationsFromMetadata(messages_mod, metadata):
  if not metadata.annotations:
    metadata.annotations = Meta(messages_mod).AnnotationsValue()
  return ListAsDictionaryWrapper(
      metadata.annotations.additionalProperties,
      Meta(messages_mod).AnnotationsValue.AdditionalProperty,
      key_field='key',
      value_field='value')


def LabelsFromMetadata(messages_mod, metadata):
  if not metadata.labels:
    metadata.labels = Meta(messages_mod).LabelsValue()
  return ListAsDictionaryWrapper(
      metadata.labels.additionalProperties,
      Meta(messages_mod).LabelsValue.AdditionalProperty,
      key_field='key',
      value_field='value')


class LazyListWrapper(collections.MutableSequence):
  """Wraps a list that does not exist at object creation time.

  We sometimes have a need to allow access to a list property of a nested
  message, when we're not sure if all the layers above the list exist yet.
  We want to arrange it so that when you write to the list, all the above
  messages are lazily created.

  When you create a LazyListWrapper, you pass in a create function, which
  must do whatever setup you need to do, and then return the list that it
  creates in an underlying message.

  As soon as you start adding items to the LazyListWrapper, it will do the
  setup for you. Until then, it won't create any underlying messages.
  """

  def __init__(self, create):
    self._create = create
    self._l = None

  def __getitem__(self, i):
    if self._l:
      return self._l[i]
    raise IndexError()

  def __setitem__(self, i, v):
    if self._l is None:
      self._l = self._create()
    self._l[i] = v

  def __delitem__(self, i):
    if self._l:
      del self._l[i]
    else:
      raise IndexError()

  def __len__(self):
    if self._l:
      return len(self._l)
    return 0

  def insert(self, i, v):
    if self._l is None:
      self._l = self._create()
    self._l.insert(i, v)


class ListAsReadOnlyDictionaryWrapper(collections.Mapping):
  """Wraps repeated messages field with name in a dict-like object.

  This class is a simplified version of ListAsDictionaryWrapper for when there
  is no single value field on the underlying messages. Compared to
  ListAsDictionaryWrapper, this class does not directly allow mutating the
  underlying messages and returns the entire message when getting.

  Operations in these classes are O(n) for simplicity. This needs to match the
  live state of the underlying list of messages, including edits made by others.
  """

  def __init__(self, to_wrap, key_field='name', filter_func=None):
    """Wraps list of messages to be accessible as a read-only dictionary.

    Arguments:
      to_wrap: List[Message], List of messages to treat as a dictionary.
      key_field: attribute to use as the keys of the dictionary
      filter_func: filter function to allow only considering certain messages
        from the wrapped list. This function should take a message as its only
        argument and return True if this message should be included.
    """
    self._m = to_wrap
    self._key_field = key_field
    self._filter = filter_func or (lambda _: True)

  def __getitem__(self, key):
    """Implements evaluation of `self[key]`."""
    for item in self._m:
      if getattr(item, self._key_field) == key:
        if self._filter(item):
          return item
        break
    raise KeyError(key)

  def __contains__(self, item):
    """Implements evaluation of `item in self`."""
    for list_elem in self._m:
      if getattr(list_elem, self._key_field) == item:
        return self._filter(list_elem)
    return False

  def __len__(self):
    """Implements evaluation of `len(self)`."""
    return sum(1 for m in self._m if self._filter(m))

  def __iter__(self):
    """Returns a generator yielding the message keys."""
    for item in self._m:
      if self._filter(item):
        yield getattr(item, self._key_field)

  def MakeSerializable(self):
    return self._m

  def __repr__(self):
    return '{}{{{}}}'.format(
        type(self).__name__,
        ', '.join('{}: {}'.format(k, v) for k, v in self.items()))


class ListAsDictionaryWrapper(ListAsReadOnlyDictionaryWrapper,
                              collections.MutableMapping):
  """Wraps repeated messages field with name and value in a dict-like object.

  Properties which resemble dictionaries (e.g. environment variables, build
  template arguments) are represented in the underlying messages fields as a
  list of objects, each of which has a name and value field. This class wraps
  that list in a dict-like object that can be used to mutate the underlying
  fields in a more Python-idiomatic way.
  """

  def __init__(self, to_wrap, item_class,
               key_field='name', value_field='value', filter_func=None):
    """Wrap a list of messages to be accessible as a dictionary.

    Arguments:
      to_wrap: List[Message], List of messages to treat as a dictionary.
      item_class: type of the underlying Message objects
      key_field: attribute to use as the keys of the dictionary
      value_field: attribute to use as the values of the dictionary
      filter_func: filter function to allow only considering certain messages
        from the wrapped list. This function should take a message as its only
        argument and return True if this message should be included.
    """
    super(ListAsDictionaryWrapper, self).__init__(
        to_wrap, key_field=key_field, filter_func=filter_func)
    self._item_class = item_class
    self._value_field = value_field

  def __getitem__(self, key):
    """Implements evaluation of `self[key]`."""
    item = super(ListAsDictionaryWrapper, self).__getitem__(key)
    return getattr(item, self._value_field)

  def __setitem__(self, key, value):
    """Implements evaluation of `self[key] = value`.

    Args:
      key: value of the key field
      value: value of the value field

    Raises:
      KeyError: if a message with the same key value already exists, but is
        hidden by the filter func, this is raised to prevent accidental
        overwrites
    """
    for item in self._m:
      if getattr(item, self._key_field) == key:
        if self._filter(item):
          setattr(item, self._value_field, value)
          break
        else:
          raise KeyError(key)
    else:
      self._m.append(self._item_class(**{
          self._key_field: key,
          self._value_field: value}))

  def __delitem__(self, key):
    """Implements evaluation of `del self[key]`."""
    index_to_delete = None
    for index, item in enumerate(self._m):
      if getattr(item, self._key_field) == key:
        if self._filter(item):
          index_to_delete = index
        break
    if index_to_delete is None:
      raise KeyError(key)
    del self._m[index_to_delete]
