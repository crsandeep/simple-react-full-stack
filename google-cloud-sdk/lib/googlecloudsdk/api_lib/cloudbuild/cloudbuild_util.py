# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Utilities for the cloudbuild API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re
from apitools.base.protorpclite import messages as proto_messages
from apitools.base.py import encoding as apitools_encoding
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import yaml
from googlecloudsdk.core.resource import resource_property
from googlecloudsdk.core.util import files

import six

_API_NAME = 'cloudbuild'
_API_VERSION = 'v1'
_ALPHA_API_VERSION = 'v1alpha2'

WORKERPOOL_NAME_MATCHER = r'projects/.*/workerPools/.*'
WORKERPOOL_NAME_SELECTOR = r'projects/.*/workerPools/(.*)'


def GetMessagesModule():
  return apis.GetMessagesModule(_API_NAME, _API_VERSION)


def GetClientClass():
  return apis.GetClientClass(_API_NAME, _API_VERSION)


def GetClientInstance(use_http=True):
  return apis.GetClientInstance(_API_NAME, _API_VERSION, no_http=(not use_http))


def GetMessagesModuleAlpha():
  return apis.GetMessagesModule(_API_NAME, _ALPHA_API_VERSION)


def GetClientClassAlpha():
  return apis.GetClientClass(_API_NAME, _ALPHA_API_VERSION)


def GetClientInstanceAlpha(use_http=True):
  return apis.GetClientInstance(
      _API_NAME, _ALPHA_API_VERSION, no_http=(not use_http))


def EncodeSubstitutions(substitutions, messages):
  if not substitutions:
    return None
  substition_properties = []
  # TODO(b/35470611): Use map encoder function instead when implemented
  for key, value in sorted(six.iteritems(substitutions)):  # Sort for tests
    substition_properties.append(
        messages.Build.SubstitutionsValue.AdditionalProperty(
            key=key, value=value))
  return messages.Build.SubstitutionsValue(
      additionalProperties=substition_properties)


def EncodeTriggerSubstitutions(substitutions, messages):
  if not substitutions:
    return None
  substition_properties = []
  for key, value in sorted(six.iteritems(substitutions)):  # Sort for tests
    substition_properties.append(
        messages.BuildTrigger.SubstitutionsValue.AdditionalProperty(
            key=key, value=value))
  return messages.BuildTrigger.SubstitutionsValue(
      additionalProperties=substition_properties)


class ParserError(exceptions.Error):
  """Error parsing YAML into a dictionary."""

  def __init__(self, path, msg):
    msg = 'parsing {path}: {msg}'.format(
        path=path,
        msg=msg,
    )
    super(ParserError, self).__init__(msg)


class ParseProtoException(exceptions.Error):
  """Error interpreting a dictionary as a specific proto message."""

  def __init__(self, path, proto_name, msg):
    msg = 'interpreting {path} as {proto_name}: {msg}'.format(
        path=path,
        proto_name=proto_name,
        msg=msg,
    )
    super(ParseProtoException, self).__init__(msg)


def SnakeToCamelString(snake):
  """Change a snake_case string into a camelCase string.

  Args:
    snake: str, the string to be transformed.

  Returns:
    str, the transformed string.
  """
  parts = snake.split('_')
  if not parts:
    return snake

  # Handle snake with leading '_'s by collapsing them into the next part.
  # Legit field names will never look like this, but completeness of the
  # function is important.
  leading_blanks = 0
  for p in parts:
    if not p:
      leading_blanks += 1
    else:
      break
  if leading_blanks:
    parts = parts[leading_blanks:]
    if not parts:
      # If they were all blanks, then we over-counted by one because of split
      # behavior.
      return '_' * (leading_blanks - 1)
    parts[0] = '_' * leading_blanks + parts[0]

  return ''.join(parts[:1] + [s.capitalize() for s in parts[1:]])


def SnakeToCamel(msg, skip=None):
  """Recursively transform all keys and values from snake_case to camelCase.

  If a key is in skip, then its value is left alone.

  Args:
    msg: dict, list, or other. If 'other', the function returns immediately.
    skip: contains dict keys whose values should not have camel case applied.

  Returns:
    Same type as msg, except all strings that were snake_case are now CamelCase,
    except for the values of dict keys contained in skip.
  """
  if skip is None:
    skip = []
  if isinstance(msg, dict):
    return {
        SnakeToCamelString(key):
        (SnakeToCamel(val, skip) if key not in skip else val)
        for key, val in six.iteritems(msg)
    }
  elif isinstance(msg, list):
    return [SnakeToCamel(elem, skip) for elem in msg]
  else:
    return msg


def MessageToFieldPaths(msg):
  """Produce field paths from a message object.

  The result is used to create a FieldMask proto message that contains all field
  paths presented in the object.
  https://github.com/protocolbuffers/protobuf/blob/master/src/google/protobuf/field_mask.proto

  Args:
    msg: An user defined message object that extends the messages.Message class.
    https://github.com/google/apitools/blob/master/apitools/base/protorpclite/messages.py

  Returns:
    The list of field paths.
  """
  fields = []
  for field in msg.all_fields():
    v = msg.get_assigned_value(field.name)
    if field.repeated and not v:
      # Repeated field is initialized as an empty list.
      continue
    if v is not None:
      name = resource_property.ConvertToSnakeCase(field.name)
      if hasattr(v, 'all_fields'):
        # message has sub-messages, constructing subpaths.
        for f in MessageToFieldPaths(v):
          fields.append('{}.{}'.format(name, f))
      else:
        fields.append(name)
  return fields


def _UnpackCheckUnused(obj, msg_type):
  """Stuff a dict into a proto message, and fail if there are unused values.

  Args:
    obj: dict(), The structured data to be reflected into the message type.
    msg_type: type, The proto message type.

  Raises:
    ValueError: If there is an unused value in obj.

  Returns:
    Proto message, The message that was created from obj.
  """
  msg = apitools_encoding.DictToMessage(obj, msg_type)

  def _CheckForUnusedFields(obj):
    """Check for any unused fields in nested messages or lists."""
    if isinstance(obj, proto_messages.Message):
      unused_fields = obj.all_unrecognized_fields()
      if unused_fields:
        if len(unused_fields) > 1:
          # Because this message shows up in a dotted path, use braces.
          # eg .foo.bar.{x,y,z}
          unused_msg = '{%s}' % ','.join(sorted(unused_fields))
        else:
          # For single items, omit the braces.
          # eg .foo.bar.x
          unused_msg = unused_fields[0]
        raise ValueError('.%s: unused' % unused_msg)
      for used_field in obj.all_fields():
        try:
          field = getattr(obj, used_field.name)
          _CheckForUnusedFields(field)
        except ValueError as e:
          raise ValueError('.%s%s' % (used_field.name, e))
    if isinstance(obj, list):
      for i, item in enumerate(obj):
        try:
          _CheckForUnusedFields(item)
        except ValueError as e:
          raise ValueError('[%d]%s' % (i, e))

  _CheckForUnusedFields(msg)

  return msg


def LoadMessageFromStream(stream,
                          msg_type,
                          msg_friendly_name,
                          skip_camel_case=None,
                          path=None):
  """Load a proto message from a stream of JSON or YAML text.

  Args:
    stream: file-like object containing the JSON or YAML data to be decoded.
    msg_type: The protobuf message type to create.
    msg_friendly_name: A readable name for the message type, for use in error
      messages.
    skip_camel_case: Contains proto field names or map keys whose values should
      not have camel case applied.
    path: str or None. Optional path to be used in error messages.

  Raises:
    ParserError: If there was a problem parsing the stream as a dict.
    ParseProtoException: If there was a problem interpreting the stream as the
    given message type.

  Returns:
    Proto message, The message that got decoded.
  """
  if skip_camel_case is None:
    skip_camel_case = []
  # Turn the data into a dict
  try:
    structured_data = yaml.load(stream, file_hint=path)
  except yaml.Error as e:
    raise ParserError(path, e.inner_error)
  if not isinstance(structured_data, dict):
    raise ParserError(path, 'Could not parse as a dictionary.')

  return _YamlToMessage(structured_data, msg_type, msg_friendly_name,
                        skip_camel_case, path)


def LoadMessagesFromStream(stream,
                           msg_type,
                           msg_friendly_name,
                           skip_camel_case=None,
                           path=None):
  """Load multiple proto message from a stream of JSON or YAML text.

  Args:
    stream: file-like object containing the JSON or YAML data to be decoded.
    msg_type: The protobuf message type to create.
    msg_friendly_name: A readable name for the message type, for use in error
      messages.
    skip_camel_case: Contains proto field names or map keys whose values should
      not have camel case applied.
    path: str or None. Optional path to be used in error messages.

  Raises:
    ParserError: If there was a problem parsing the stream.
    ParseProtoException: If there was a problem interpreting the stream as the
    given message type.

  Returns:
    Proto message list of the messages that got decoded.
  """
  if skip_camel_case is None:
    skip_camel_case = []
  # Turn the data into a dict
  try:
    structured_data = yaml.load_all(stream, file_hint=path)
  except yaml.Error as e:
    raise ParserError(path, e.inner_error)

  return [
      _YamlToMessage(item, msg_type, msg_friendly_name, skip_camel_case, path)
      for item in structured_data
  ]


def _YamlToMessage(structured_data,
                   msg_type,
                   msg_friendly_name,
                   skip_camel_case=None,
                   path=None):
  """Load a proto message from a file containing JSON or YAML text.

  Args:
    structured_data: Dict containing the decoded YAML data.
    msg_type: The protobuf message type to create.
    msg_friendly_name: A readable name for the message type, for use in error
      messages.
    skip_camel_case: Contains proto field names or map keys whose values should
      not have camel case applied.
    path: str or None. Optional path to be used in error messages.

  Raises:
    ParseProtoException: If there was a problem interpreting the file as the
    given message type.

  Returns:
    Proto message, The message that got decoded.
  """

  # Transform snake_case into camelCase.
  structured_data = SnakeToCamel(structured_data, skip_camel_case)

  # Then, turn the dict into a proto message.
  try:
    msg = _UnpackCheckUnused(structured_data, msg_type)
  except Exception as e:
    # Catch all exceptions here because a valid YAML can sometimes not be a
    # valid message, so we need to catch all errors in the dict to message
    # conversion.
    raise ParseProtoException(path, msg_friendly_name, '%s' % e)

  return msg


def LoadMessageFromPath(path,
                        msg_type,
                        msg_friendly_name,
                        skip_camel_case=None):
  """Load a proto message from a file containing JSON or YAML text.

  Args:
    path: The path to a file containing the JSON or YAML data to be decoded.
    msg_type: The protobuf message type to create.
    msg_friendly_name: A readable name for the message type, for use in error
      messages.
    skip_camel_case: Contains proto field names or map keys whose values should
      not have camel case applied.

  Raises:
    files.MissingFileError: If the file does not exist.
    ParserError: If there was a problem parsing the file as a dict.
    ParseProtoException: If there was a problem interpreting the file as the
    given message type.

  Returns:
    Proto message, The message that got decoded.
  """
  with files.FileReader(path) as f:  # Returns user-friendly error messages
    return LoadMessageFromStream(f, msg_type, msg_friendly_name,
                                 skip_camel_case, path)


def LoadMessagesFromPath(path,
                         msg_type,
                         msg_friendly_name,
                         skip_camel_case=None):
  """Load a proto message from a file containing JSON or YAML text.

  Args:
    path: The path to a file containing the JSON or YAML data to be decoded.
    msg_type: The protobuf message type to create.
    msg_friendly_name: A readable name for the message type, for use in error
      messages.
    skip_camel_case: Contains proto field names or map keys whose values should
      not have camel case applied.

  Raises:
    files.MissingFileError: If the file does not exist.
    ParseProtoException: If there was a problem interpreting the file as the
    given message type.

  Returns:
    Proto message list of the messages that got decoded.
  """
  with files.FileReader(path) as f:  # Returns user-friendly error messages
    return LoadMessagesFromStream(f, msg_type, msg_friendly_name,
                                  skip_camel_case, path)


def WorkerPoolShortName(resource_name):
  """Turn a worker pool's full resource name into its short name (the ID).

  For example, this turns "projects/abc/workerPools/def" into "def".

  Args:
    resource_name: A Worker pool's full resource name.

  Raises:
    ValueError: If the full resource name was not well-formatted.

  Returns:
    The worker pool's short name.
  """
  match = re.search(WORKERPOOL_NAME_SELECTOR, resource_name)
  if match:
    return match.group(1)
  raise ValueError('The worker pool resource name must match "%s"' %
                   (WORKERPOOL_NAME_MATCHER,))
