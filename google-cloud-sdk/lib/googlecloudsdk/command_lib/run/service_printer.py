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

"""Service-specific printer."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import collections
import textwrap

from googlecloudsdk.api_lib.run import k8s_object
from googlecloudsdk.api_lib.run import revision
from googlecloudsdk.command_lib.run import traffic_printer
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.resource import custom_printer_base as cp

import six


SERVICE_PRINTER_FORMAT = 'service'


def FormatSecretKeyRef(v):
  return '{}:{}'.format(v.secretKeyRef.name, v.secretKeyRef.key)


def FormatSecretVolumeSource(v):
  if v.items:
    return '{}:{}'.format(v.secretName, v.items[0].key)
  else:
    return v.secretName


def FormatConfigMapKeyRef(v):
  return '{}:{}'.format(v.configMapKeyRef.name, v.configMapKeyRef.key)


def FormatConfigMapVolumeSource(v):
  if v.items:
    return '{}:{}'.format(v.name, v.items[0].key)
  else:
    return v.name


class ServicePrinter(cp.CustomPrinterBase):
  """Prints the run Service in a custom human-readable format.

  Format specific to Cloud Run services. Only available on Cloud Run commands
  that print services.
  """

  def _GetRevisionHeader(self, record):
    return console_attr.GetConsoleAttr().Emphasize(
        'Revision {}'.format(record.status.latestCreatedRevisionName))

  def _GetLimits(self, rev):
    return collections.defaultdict(str, rev.resource_limits)

  def _OrderByKey(self, map_):
    for k in sorted(map_):
      yield k, map_[k]

  def _GetTimeout(self, record):
    if record.template.timeout is not None:
      return '{}s'.format(record.template.timeout)
    return None

  def _GetSecrets(self, record):
    secrets = {}
    secrets.update({
        k: FormatSecretKeyRef(v)
        for k, v in record.template.env_vars.secrets.items()})
    secrets.update({
        k: FormatSecretVolumeSource(v)
        for k, v in record.template.MountedVolumeJoin('secrets').items()})
    return cp.Mapped(self._OrderByKey(secrets))

  def _GetConfigMaps(self, record):
    config_maps = {}
    config_maps.update({
        k: FormatConfigMapKeyRef(v)
        for k, v in record.template.env_vars.config_maps.items()})
    config_maps.update({
        k: FormatConfigMapVolumeSource(v)
        for k, v in record.template.MountedVolumeJoin('config_maps').items()})
    return cp.Mapped(self._OrderByKey(config_maps))

  def _GetUserEnvironmentVariables(self, record):
    return cp.Mapped(self._OrderByKey(record.template.env_vars.literals))

  def _GetCloudSqlInstances(self, record):
    instances = record.template_annotations.get(
        revision.CLOUDSQL_ANNOTATION, '')
    return instances.replace(',', ', ')

  def _RevisionPrinters(self, record):
    """Adds printers for the revision."""
    limits = self._GetLimits(record.template)
    return cp.Lines([
        self._GetRevisionHeader(record),
        self._GetLabels(record.template.labels),
        cp.Labeled([
            ('Image', record.UserImage()),
            ('Command', ' '.join(record.template.container.command)),
            ('Args', ' '.join(record.template.container.args)),
            ('Port', ' '.join(
                six.text_type(cp.containerPort)
                for cp in record.template.container.ports)),
            ('Memory', limits['memory']),
            ('CPU', limits['cpu']),
            ('Service account', record.template.spec.serviceAccountName),
            ('Env vars', self._GetUserEnvironmentVariables(record)),
            ('Secrets', self._GetSecrets(record)),
            ('Config Maps', self._GetConfigMaps(record)),
            ('Concurrency', record.template.concurrency),
            ('SQL connections', self._GetCloudSqlInstances(record)),
            ('Timeout', self._GetTimeout(record)),
        ]),
    ])

  def _GetServiceHeader(self, record):
    con = console_attr.GetConsoleAttr()
    status = con.Colorize(*record.ReadySymbolAndColor())
    try:
      place = 'region ' + record.region
    except KeyError:
      place = 'namespace ' + record.namespace
    return con.Emphasize('{} Service {} in {}'.format(
        status,
        record.name,
        place))

  def _GetLabels(self, labels):
    """Returns a human readable description of user provided labels if any."""
    if not labels:
      return ''
    return ' '.join(sorted(['{}:{}'.format(k, v) for k, v in labels.items()
                            if not k.startswith(k8s_object.INTERNAL_GROUPS)]))

  def _GetLastUpdated(self, record):
    modifier = record.last_modifier or '?'
    last_transition_time = '?'
    for condition in record.status.conditions:
      if condition.type == 'Ready' and condition.lastTransitionTime:
        last_transition_time = condition.lastTransitionTime
    return 'Last updated on {} by {}'.format(last_transition_time, modifier)

  def _GetReadyMessage(self, record):
    if record.ready_condition and record.ready_condition['message']:
      symbol, color = record.ReadySymbolAndColor()
      return console_attr.GetConsoleAttr().Colorize(
          textwrap.fill('{} {}'.format(
              symbol, record.ready_condition['message']), 100), color)
    else:
      return ''

  def Transform(self, record):
    """Transform a service into the output structure of marker classes."""
    fmt = cp.Lines([
        self._GetServiceHeader(record),
        self._GetLabels(record.labels),
        ' ',
        traffic_printer.TransformTraffic(record),
        ' ',
        cp.Labeled(
            [(self._GetLastUpdated(record), self._RevisionPrinters(record))]),
        self._GetReadyMessage(record)])
    return fmt
