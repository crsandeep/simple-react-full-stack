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
"""Module for wrangling bigtable command arguments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.bigtable import util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util import completers
from googlecloudsdk.command_lib.util.apis import yaml_data
from googlecloudsdk.command_lib.util.args import resource_args
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core.util import text


class ClusterCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(ClusterCompleter, self).__init__(
        collection='bigtableadmin.projects.instances.clusters',
        list_command='beta bigtable clusters list --uri',
        **kwargs)


class InstanceCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(InstanceCompleter, self).__init__(
        collection='bigtableadmin.projects.instances',
        list_command='beta bigtable instances list --uri',
        **kwargs)


class TableCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(TableCompleter, self).__init__(
        collection='bigtableadmin.projects.instances.tables',
        list_command='beta bigtable instances tables list --uri',
        **kwargs)


def ProcessInstanceTypeAndNodes(args, instance_type):
  """Ensure that --instance-type and --num-nodes are consistent.

  If --instance-type is DEVELOPMENT, then no --cluster-num-nodes can be
  specified. If --instance-type is PRODUCTION, then --cluster-num-nodes defaults
  to 3 if not specified, but can be any positive value.

  Args:
    args: an argparse namespace.
    instance_type: string, The instance type; PRODUCTION or DEVELOPMENT.

  Raises:
    exceptions.InvalidArgumentException: If --cluster-num-nodes is specified
        when --instance-type is DEVELOPMENT, or --cluster-num-nodes is not
        positive.

  Returns:
    Number of nodes or None if DEVELOPMENT instance-type.
  """
  msgs = util.GetAdminMessages()
  num_nodes = args.cluster_num_nodes
  if not args.IsSpecified('cluster_num_nodes'):
    if instance_type == msgs.Instance.TypeValueValuesEnum.PRODUCTION:
      num_nodes = 3
  else:
    if instance_type == msgs.Instance.TypeValueValuesEnum.DEVELOPMENT:
      raise exceptions.InvalidArgumentException(
          '--cluster-num-nodes',
          'Cannot set --cluster-num-nodes for DEVELOPMENT instances.')
    elif num_nodes < 1:
      raise exceptions.InvalidArgumentException(
          '--cluster-num-nodes',
          'Clusters of PRODUCTION instances must have at least 1 node.')
  return num_nodes


class ArgAdder(object):
  """A class for adding Bigtable command-line arguments."""

  def __init__(self, parser):
    self.parser = parser

  def AddAsync(self):
    base.ASYNC_FLAG.AddToParser(self.parser)
    return self

  def AddCluster(self):
    """Add cluster argument."""
    self.parser.add_argument(
        '--cluster',
        completer=ClusterCompleter,
        help='ID of the cluster.',
        required=True)
    return self

  def AddClusterNodes(self, in_instance=False, required=None, default=None):
    is_required = required if required is not None else not in_instance
    self.parser.add_argument(
        '--cluster-num-nodes' if in_instance else '--num-nodes',
        help='Number of nodes to serve.',
        default=default,
        required=is_required,
        type=int)
    return self

  def AddClusterStorage(self):
    storage_argument = base.ChoiceArgument(
        '--cluster-storage-type',
        choices=['hdd', 'ssd'],
        default='ssd',
        help_str='Storage class for the cluster.')
    storage_argument.AddToParser(self.parser)
    return self

  def AddClusterZone(self, in_instance=False):
    self.parser.add_argument(
        '--cluster-zone' if in_instance else '--zone',
        help='ID of the zone where the cluster is located. Supported zones '
        'are listed at https://cloud.google.com/bigtable/docs/locations.',
        required=True)
    return self

  def AddInstance(self, positional=True, required=True, multiple=False,
                  additional_help=None):
    """Add argument for instance ID to parser."""
    help_text = 'ID of the {}.'.format(text.Pluralize(2 if multiple else 1,
                                                      'instance'))
    if additional_help:
      help_text = ' '.join([help_text, additional_help])
    name = 'instance' if positional else '--instance'
    args = {
        'completer': InstanceCompleter,
        'help': help_text
    }
    if multiple:
      if positional:
        args['nargs'] = '+'
      else:
        name = '--instances'
        args['type'] = arg_parsers.ArgList()
        args['metavar'] = 'INSTANCE'
    if not positional:
      args['required'] = required

    self.parser.add_argument(name, **args)
    return self

  def AddTable(self):
    """Add table argument."""
    self.parser.add_argument(
        '--table',
        completer=TableCompleter,
        help='ID of the table.',
        required=True)
    return self

  def AddAppProfileRouting(self, required=True):
    """Adds arguments for app_profile routing to parser."""
    routing_group = self.parser.add_mutually_exclusive_group(required=required)
    any_group = routing_group.add_group('Multi Cluster Routing Policy')
    any_group.add_argument(
        '--route-any',
        action='store_true',
        default=False,
        help='Use Multi Cluster Routing policy.')
    route_to_group = routing_group.add_group('Single Cluster Routing Policy')
    route_to_group.add_argument(
        '--route-to',
        completer=ClusterCompleter,
        required=True,
        help='Cluster ID to route to using Single Cluster Routing policy.')
    route_to_group.add_argument(
        '--transactional-writes',
        action='store_true',
        default=False,
        help='Allow transactional writes with a Single Cluster Routing policy.')
    return self

  def AddDescription(self, resource, required=True):
    """Add argument for description to parser."""
    self.parser.add_argument(
        '--description',
        help='Friendly name of the {}.'.format(resource),
        required=required)
    return self

  def AddForce(self, verb):
    """Add argument for force to the parser."""
    self.parser.add_argument(
        '--force',
        action='store_true',
        default=False,
        help='Ignore warnings and force {}.'.format(verb))
    return self

  def AddInstanceDisplayName(self, required=False):
    """Add argument group for display-name to parser."""
    self.parser.add_argument(
        '--display-name',
        help='Friendly name of the instance.',
        required=required)
    return self

  def AddInstanceType(self, default=None, help_text=None):
    """Add default instance type choices to parser."""
    choices = {
        'PRODUCTION':
            'Production instances have a minimum of '
            'three nodes, provide high availability, and are suitable for '
            'applications in production.',
        'DEVELOPMENT': 'Development instances are low-cost instances meant '
                       'for development and testing only. They do not '
                       'provide high availability and no service level '
                       'agreement applies.'
    }

    self.parser.add_argument(
        '--instance-type',
        default=default,
        type=lambda x: x.upper(),
        choices=choices,
        help=help_text)

    return self


def InstanceAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='instance', help_text='Cloud Bigtable instance for the {resource}.')


def TableAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='table', help_text='Cloud Bigtable table for the {resource}.')


def ClusterAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='cluster', help_text='Cloud Bigtable cluster for the {resource}.')


def AppProfileAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='app profile',
      help_text='Cloud Bigtable application profile for the {resource}.')


def BackupAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='backup', help_text='Cloud Bigtable backup for the {resource}.')


def GetInstanceResourceSpec():
  """Return the resource specification for a Bigtable instance."""
  return concepts.ResourceSpec(
      'bigtableadmin.projects.instances',
      resource_name='instance',
      instancesId=InstanceAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False)


def GetTableResourceSpec():
  """Return the resource specification for a Bigtable table."""
  return concepts.ResourceSpec(
      'bigtableadmin.projects.instances.tables',
      resource_name='table',
      tablesId=TableAttributeConfig(),
      instancesId=InstanceAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False)


def GetClusterResourceSpec():
  """Return the resource specification for a Bigtable cluster."""
  return concepts.ResourceSpec(
      'bigtableadmin.projects.instances.clusters',
      resource_name='cluster',
      clustersId=ClusterAttributeConfig(),
      instancesId=InstanceAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False)


def GetAppProfileResourceSpec():
  """Return the resource specification for a Bigtable app profile."""
  return concepts.ResourceSpec(
      'bigtableadmin.projects.instances.appProfiles',
      resource_name='app profile',
      instancesId=InstanceAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False)


def AddInstancesResourceArg(parser, verb, positional=False):
  """Add --instances resource argument to the parser."""
  concept_parsers.ConceptParser.ForResource(
      'instance' if positional else '--instances',
      GetInstanceResourceSpec(),
      'The instances {}.'.format(verb),
      required=positional,
      plural=True).AddToParser(parser)


def AddInstanceResourceArg(parser, verb, positional=False, required=True):
  """Add --instance resource argument to the parser."""
  concept_parsers.ConceptParser.ForResource(
      'instance' if positional else '--instance',
      GetInstanceResourceSpec(),
      'The instance {}.'.format(verb),
      required=required,
      plural=False).AddToParser(parser)


def AddTableResourceArg(parser, verb, positional=False):
  """Add --table resource argument to the parser."""
  concept_parsers.ConceptParser.ForResource(
      'table' if positional else '--table',
      GetTableResourceSpec(),
      'The table {}.'.format(verb),
      required=True,
      plural=False).AddToParser(parser)


def AddClusterResourceArg(parser, verb):
  """Add cluster positional resource argument to the parser."""
  concept_parsers.ConceptParser.ForResource(
      'cluster',
      GetClusterResourceSpec(),
      'The cluster {}.'.format(verb),
      required=True).AddToParser(parser)


def AddAppProfileResourceArg(parser, verb):
  """Add app profile positional resource argument to the parser."""
  concept_parsers.ConceptParser.ForResource(
      'app_profile',
      GetAppProfileResourceSpec(),
      'The app profile {}.'.format(verb),
      required=True).AddToParser(parser)


def AddBackupResourceArg(parser, verb):
  """Add backup positional resource argument to the parser."""
  concept_parsers.ConceptParser(
      [presentation_specs.ResourcePresentationSpec(
          '--instance',
          GetInstanceResourceSpec(),
          'The instance {}.'.format(verb),
          required=False),
       presentation_specs.ResourcePresentationSpec(
           '--cluster',
           GetClusterResourceSpec(),
           'The cluster {}.'.format(verb),
           required=False,
           flag_name_overrides={'instance': ''})]).AddToParser(parser)


def AddTableRestoreResourceArg(parser):
  """Add Table resource args (source, destination) for restore command."""
  table_spec_data = yaml_data.ResourceYAMLData.FromPath('bigtable.table')
  backup_spec_data = yaml_data.ResourceYAMLData.FromPath('bigtable.backup')

  arg_specs = [
      resource_args.GetResourcePresentationSpec(
          verb='to copy from', name='source', required=True, prefixes=True,
          attribute_overrides={'table': 'source'}, positional=False,
          resource_data=backup_spec_data.GetData()),
      resource_args.GetResourcePresentationSpec(
          verb='to copy to', name='destination',
          required=True, prefixes=True,
          attribute_overrides={'table': 'destination'}, positional=False,
          resource_data=table_spec_data.GetData())]
  fallthroughs = {
      '--source.instance': ['--destination.instance'],
      '--destination.instance': ['--source.instance']
  }
  concept_parsers.ConceptParser(arg_specs, fallthroughs).AddToParser(parser)
