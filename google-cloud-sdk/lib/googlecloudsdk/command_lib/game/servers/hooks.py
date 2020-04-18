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

"""Argument processors for Game Servers surface arguments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.core import properties

DEFAULT_LOCATION = 'global'

PARENT_TEMPLATE = 'projects/{}/locations/{}'
PARENT_DEPLOYMENT_TEMPLATE = 'projects/{}/locations/{}/gameServerDeployments/{}'
PARENT_REALM_TEMPLATE = 'projects/{}/locations/{}/realms/{}'

DEPLOYMENT_WILDCARD = '-'
LOCATION_WILDCARD = '-'
REALM_WILDCARD = '-'


def FlattenedArgDict(value):
  dict_value = arg_parsers.ArgDict()(value)
  return [{'key': key, 'value': value} for key, value in dict_value.items()]


def AddDefaultLocationToListRequest(ref, args, req):
  """Python hook for yaml commands to wildcard the location in list requests."""
  del ref  # Unused
  project = properties.VALUES.core.project.Get(required=True)
  location = args.location or LOCATION_WILDCARD
  req.parent = PARENT_TEMPLATE.format(project, location)
  return req


def AddDefaultLocationAndRealmToListRequest(ref, args, req):
  """Python hook for yaml commands to wildcard the realm and location in list requests."""
  del ref
  project = properties.VALUES.core.project.Get(required=True)
  location = args.location or LOCATION_WILDCARD
  # If realm is specified but location is not, we fall back to global, which is
  # the default location for realms.
  if args.realm and not args.location:
    location = DEFAULT_LOCATION
  realm = args.realm or REALM_WILDCARD
  req.parent = PARENT_REALM_TEMPLATE.format(project, location, realm)
  return req


def AddDefaultLocationAndDeploymentToListRequest(ref, args, req):
  """Python hook for yaml commands to wildcard the deployment and location in list requests."""
  del ref
  project = properties.VALUES.core.project.Get(required=True)
  location = args.location or LOCATION_WILDCARD
  # If deployment is specified but location is not, we fall back to global
  # which is the default location for realms.
  if args.deployment and not args.location:
    location = DEFAULT_LOCATION
  deployment = args.deployment or DEPLOYMENT_WILDCARD
  req.parent = PARENT_DEPLOYMENT_TEMPLATE.format(project, location, deployment)
  return req
