# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Helpers and common arguments for Composer commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse
import re

from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.composer import parsers
from googlecloudsdk.command_lib.composer import util as command_util
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import properties

import ipaddress
import six


AIRFLOW_VERSION_TYPE = arg_parsers.RegexpValidator(
    r'^(\d+\.\d+(?:\.\d+)?)', 'must be in the form X.Y[.Z].')

IMAGE_VERSION_TYPE = arg_parsers.RegexpValidator(
    r'^composer-(\d+\.\d+\.\d+|latest)-airflow-(\d+\.\d+(?:\.\d+)?)',
    'must be in the form \'composer-A.B.C-airflow-X.Y[.Z]\' or '
    '\'latest\' can be provided in place of the Cloud Composer version '
    'string. For example: \'composer-latest-airflow-1.10.0\'.')

# TODO(b/118349075): Refactor global Argument definitions to be factory methods.
ENVIRONMENT_NAME_ARG = base.Argument(
    'name', metavar='NAME', help='The name of an environment.')

MULTI_ENVIRONMENT_NAME_ARG = base.Argument(
    'name', metavar='NAME', nargs='+', help='The name of an environment.')

MULTI_OPERATION_NAME_ARG = base.Argument(
    'name', metavar='NAME', nargs='+', help='The name or UUID of an operation.')

OPERATION_NAME_ARG = base.Argument(
    'name', metavar='NAME', help='The name or UUID of an operation.')

LOCATION_FLAG = base.Argument(
    '--location',
    required=False,
    help='The Cloud Composer location (e.g., us-central1).',
    action=actions.StoreProperty(properties.VALUES.composer.location))

_ENV_VAR_NAME_ERROR = (
    'Only upper and lowercase letters, digits, and underscores are allowed. '
    'Environment variable names may not start with a digit.')

_INVALID_IPV4_CIDR_BLOCK_ERROR = ('Invalid format of IPV4 CIDR block.')
_INVALID_GKE_MASTER_IPV4_CIDR_BLOCK_ERROR = (
    'Not a valid IPV4 CIDR block value for the kubernetes master')
_INVALID_WEB_SERVER_IPV4_CIDR_BLOCK_ERROR = (
    'Not a valid IPV4 CIDR block value for the Airflow web server')
_INVALID_CLOUD_SQL_IPV4_CIDR_BLOCK_ERROR = (
    'Not a valid IPV4 CIDR block value for the Cloud SQL instance')

AIRFLOW_CONFIGS_FLAG_GROUP_DESCRIPTION = (
    'Group of arguments for modifying the Airflow configuration.')

CLEAR_AIRFLOW_CONFIGS_FLAG = base.Argument(
    '--clear-airflow-configs',
    action='store_true',
    help="""\
    Removes all Airflow config overrides from the environment.
    """)

UPDATE_AIRFLOW_CONFIGS_FLAG = base.Argument(
    '--update-airflow-configs',
    metavar='KEY=VALUE',
    type=arg_parsers.ArgDict(key_type=str, value_type=str),
    action=arg_parsers.UpdateAction,
    help="""\
    A list of Airflow config override KEY=VALUE pairs to set. If a config
    override exists, its value is updated; otherwise, a new config override
    is created.

    KEYs should specify the configuration section and property name,
    separated by a hyphen, for example `core-print_stats_interval`. The
    section may not contain a closing square brace or period. The property
    name must be non-empty and may not contain an equals sign, semicolon,
    or period. By convention, property names are spelled with
    `snake_case.` VALUEs may contain any character.
    """)

REMOVE_AIRFLOW_CONFIGS_FLAG = base.Argument(
    '--remove-airflow-configs',
    metavar='KEY',
    type=arg_parsers.ArgList(),
    action=arg_parsers.UpdateAction,
    help="""\
    A list of Airflow config override keys to remove.
    """)

ENV_VARIABLES_FLAG_GROUP_DESCRIPTION = (
    'Group of arguments for modifying environment variables.')

UPDATE_ENV_VARIABLES_FLAG = base.Argument(
    '--update-env-variables',
    metavar='NAME=VALUE',
    type=arg_parsers.ArgDict(key_type=str, value_type=str),
    action=arg_parsers.UpdateAction,
    help="""\
    A list of environment variable NAME=VALUE pairs to set and provide to the
    Airflow scheduler, worker, and webserver processes. If an environment
    variable exists, its value is updated; otherwise, a new environment
    variable is created.

    NAMEs are the environment variable names and may contain upper and
    lowercase letters, digits, and underscores; they must not begin with a
    digit.

    User-specified environment variables should not be used to set Airflow
    configuration properties. Instead use the `--update-airflow-configs` flag.
    """)

REMOVE_ENV_VARIABLES_FLAG = base.Argument(
    '--remove-env-variables',
    metavar='NAME',
    type=arg_parsers.ArgList(),
    action=arg_parsers.UpdateAction,
    help="""\
    A list of environment variables to remove.

    Environment variables that have system-provided defaults cannot be unset
    with the `--remove-env-variables` or `--clear-env-variables` flags; only
    the user-supplied overrides will be removed.
    """)

CLEAR_ENV_VARIABLES_FLAG = base.Argument(
    '--clear-env-variables',
    action='store_true',
    help="""\
    Removes all environment variables from the environment.

    Environment variables that have system-provided defaults cannot be unset
    with the `--remove-env-variables` or `--clear-env-variables` flags; only
    the user-supplied overrides will be removed.
    """)

ENV_UPGRADE_GROUP_DESCRIPTION = (
    'Group of arguments for performing in-place environment upgrades.')

UPDATE_AIRFLOW_VERSION_FLAG = base.Argument(
    '--airflow-version',
    type=AIRFLOW_VERSION_TYPE,
    metavar='AIRFLOW_VERSION',
    help="""\
    Upgrade the environment to a later Airflow version in-place.

    Must be of the form `X.Y[.Z]`.

    The Airflow version is a semantic version. The patch version can be omitted
    and the current version will be selected. The version numbers that are used
    will be stored.
    """)

UPDATE_IMAGE_VERSION_FLAG = base.Argument(
    '--image-version',
    type=IMAGE_VERSION_TYPE,
    metavar='IMAGE_VERSION',
    help="""\
    Upgrade the environment to a later version in-place.

    The image version encapsulates the versions of both Cloud Composer and
    Apache Airflow. Must be of the form `composer-A.B.C-airflow-X.Y[.Z]`.

    The Cloud Composer and Airflow versions are semantic versions.
    `latest` can be provided instead of an explicit Cloud Composer
    version number indicating that the server will replace `latest`
    with the current Cloud Composer version. For the Apache Airflow
    portion, the patch version can be omitted and the current
    version will be selected. The version numbers that are used will
    be stored.
    """)

UPDATE_PYPI_FROM_FILE_FLAG = base.Argument(
    '--update-pypi-packages-from-file',
    help="""\
    The path to a file containing a list of PyPI packages to install in
    the environment. Each line in the file should contain a package
    specification in the format of the update-pypi-package argument
    defined above. The path can be a local file path or a Google Cloud Storage
    file path (Cloud Storage file path starts with 'gs://').
    """)

LABELS_FLAG_GROUP_DESCRIPTION = (
    'Group of arguments for modifying environment labels.')

GENERAL_REMOVAL_FLAG_GROUP_DESCRIPTION = 'Arguments available for item removal.'

PYPI_PACKAGES_FLAG_GROUP_DESCRIPTION = (
    'Group of arguments for modifying the PyPI package configuration.')

CLEAR_PYPI_PACKAGES_FLAG = base.Argument(
    '--clear-pypi-packages',
    action='store_true',
    help="""\
    Removes all PyPI packages from the environment.

    PyPI packages that are required by the environment's core software
    cannot be uninstalled with the `--remove-pypi-packages` or
    `--clear-pypi-packages` flags.
    """)

UPDATE_PYPI_PACKAGE_FLAG = base.Argument(
    '--update-pypi-package',
    metavar='PACKAGE[EXTRAS_LIST]VERSION_SPECIFIER',
    action='append',
    default=[],
    help="""\
    A PyPI package to add to the environment. If a package exists, its
    value is updated; otherwise, a new package is installed.

    The value takes the form of: `PACKAGE[EXTRAS_LIST]VERSION_SPECIFIER`,
    as one would specify in a pip requirements file.

    PACKAGE is specified as a package name, such as `numpy.` EXTRAS_LIST is
    a comma-delimited list of PEP 508 distribution extras that may be
    empty, in which case the enclosing square brackets may be omitted.
    VERSION_SPECIFIER is an optional PEP 440 version specifier. If both
    EXTRAS_LIST and VERSION_SPECIFIER are omitted, the `=` and
    everything to the right may be left empty.

    This is a repeated argument that can be specified multiple times to
    update multiple packages. If PACKAGE appears more than once, the last
    value will be used.
    """)

REMOVE_PYPI_PACKAGES_FLAG = base.Argument(
    '--remove-pypi-packages',
    metavar='PACKAGE',
    type=arg_parsers.ArgList(),
    action=arg_parsers.UpdateAction,
    help="""\
    A list of PyPI package names to remove.

    PyPI packages that are required by the environment's core software
    cannot be uninstalled with the `--remove-pypi-packages` or
    `--clear-pypi-packages` flags.
    """)

ENABLE_IP_ALIAS_FLAG = base.Argument(
    '--enable-ip-alias',
    default=None,
    action='store_true',
    help="""\
    Enable use of alias IPs (https://cloud.google.com/compute/docs/alias-ip/)
    for Pod IPs. This will require at least two secondary ranges in the
    subnetwork, one for the pod IPs and another to reserve space for the
    services range.
    """)

CLUSTER_SECONDARY_RANGE_NAME_FLAG = base.Argument(
    '--cluster-secondary-range-name',
    default=None,
    help="""\
    Secondary range to be used as the source for pod IPs. Alias ranges will be
    allocated from this secondary range. NAME must be the name of an existing
    secondary range in the cluster subnetwork.

    Cannot be specified unless '--enable-ip-alias' is also specified.
    """)

SERVICES_SECONDARY_RANGE_NAME_FLAG = base.Argument(
    '--services-secondary-range-name',
    default=None,
    help="""\
    Secondary range to be used for services (e.g. ClusterIPs). NAME must be the
    name of an existing secondary range in the cluster subnetwork.

    Cannot be specified unless '--enable-ip-alias' is also specified.
    """)

WEB_SERVER_ALLOW_IP = base.Argument(
    '--web-server-allow-ip',
    type=arg_parsers.ArgDict(spec={
        'ip_range': str,
        'description': str
    }),
    action='append',
    help="""\
    Specifies a list of IPv4 or IPv6 ranges that will be allowed to access the
    Airflow web server. By default, all IPs are allowed to access the web
    server.

    *ip_range*::: IPv4 or IPv6 range of addresses allowed to access the Airflow
    web server.

    *description*::: An optional description of the IP range.
    """)

WEB_SERVER_DENY_ALL = base.Argument(
    '--web-server-deny-all',
    action='store_true',
    help="""\
    Denies all incoming traffic to the Airflow web server.
    """)

WEB_SERVER_ALLOW_ALL = base.Argument(
    '--web-server-allow-all',
    action='store_true',
    help="""\
    Allows all IP addresses to access the Airflow web server.
    """)

UPDATE_WEB_SERVER_ALLOW_IP = base.Argument(
    '--update-web-server-allow-ip',
    type=arg_parsers.ArgDict(spec={
        'ip_range': str,
        'description': str
    }),
    action='append',
    help="""\
    Specifies a list of IPv4 or IPv6 ranges that will be allowed to access the
    Airflow web server. By default, all IPs are allowed to access the web
    server.

    *ip_range*::: IPv4 or IPv6 range of addresses allowed to access the Airflow
    web server.

    *description*::: An optional description of the IP range.
    """)


def _IsValidIpv4CidrBlock(ipv4_cidr_block):
  """Validates that IPV4 CIDR block arg has valid format.

  Intended to be used as an argparse validator.

  Args:
    ipv4_cidr_block: str, the IPV4 CIDR block string to validate

  Returns:
    bool, True if and only if the IPV4 CIDR block is valid
  """
  return ipaddress.IPv4Network(ipv4_cidr_block) is not None


IPV4_CIDR_BLOCK_FORMAT_VALIDATOR = arg_parsers.CustomFunctionValidator(
    _IsValidIpv4CidrBlock, _INVALID_IPV4_CIDR_BLOCK_ERROR)

CLUSTER_IPV4_CIDR_FLAG = base.Argument(
    '--cluster-ipv4-cidr',
    default=None,
    type=IPV4_CIDR_BLOCK_FORMAT_VALIDATOR,
    help="""\
    IP address range for the pods in this cluster in CIDR notation
    (e.g. 10.0.0.0/14).

    Cannot be specified unless '--enable-ip-alias' is also specified.
    """)

SERVICES_IPV4_CIDR_FLAG = base.Argument(
    '--services-ipv4-cidr',
    default=None,
    type=IPV4_CIDR_BLOCK_FORMAT_VALIDATOR,
    help="""\
    IP range for the services IPs.

    Can be specified as a netmask size (e.g. '/20') or as in CIDR notion
    (e.g. '10.100.0.0/20'). If given as a netmask size, the IP range will
    be chosen automatically from the available space in the network.

    If unspecified, the services CIDR range will be chosen with a default
    mask size.

    Cannot be specified unless '--enable-ip-alias' is also specified.
    """)

ENABLE_PRIVATE_ENVIRONMENT_FLAG = base.Argument(
    '--enable-private-environment',
    default=None,
    action='store_true',
    help="""\
    Environment cluster is created with no public IP addresses on the cluster
    nodes.

    If not specified, cluster nodes will be assigned public IP addresses.

    Cannot be specified unless '--enable-ip-alias' is also specified.
    """)

ENABLE_PRIVATE_ENDPOINT_FLAG = base.Argument(
    '--enable-private-endpoint',
    default=None,
    action='store_true',
    help="""\
    Environment cluster is managed using the private IP address of the master
    API endpoint. Therefore access to the master endpoint must be from
    internal IP addresses.

    If not specified, the master API endpoint will be accessible by its public
    IP address.

    Cannot be specified unless '--enable-private-environnment' is also
    specified.
    """)


def _GetIpv4CidrMaskSize(ipv4_cidr_block):
  """Returns the size of IPV4 CIDR block mask in bits.

  Args:
    ipv4_cidr_block: str, the IPV4 CIDR block string to check.

  Returns:
    int, the size of the block mask if ipv4_cidr_block is a valid CIDR block
    string, otherwise None.
  """
  network = ipaddress.IPv4Network(ipv4_cidr_block)
  if network is None:
    return None

  return 32 - (network.num_addresses.bit_length() - 1)


def _IsValidMasterIpv4CidrBlockWithMaskSize(ipv4_cidr_block, min_mask_size,
                                            max_mask_size):
  """Validates that IPV4 CIDR block arg for the cluster master is a valid value.

  Args:
    ipv4_cidr_block: str, the IPV4 CIDR block string to validate.
    min_mask_size: int, minimum allowed netmask size for CIDR block.
    max_mask_size: int, maximum allowed netmask size for CIDR block.

  Returns:
    bool, True if and only if the IPV4 CIDR block is valid and has the mask
    size between min_mask_size and max_mask_size.
  """
  is_valid = _IsValidIpv4CidrBlock(ipv4_cidr_block)
  if not is_valid:
    return False

  mask_size = _GetIpv4CidrMaskSize(ipv4_cidr_block)
  return min_mask_size <= mask_size and mask_size <= max_mask_size


_IS_VALID_MASTER_IPV4_CIDR_BLOCK = (
    lambda cidr: _IsValidMasterIpv4CidrBlockWithMaskSize(cidr, 23, 28))

MASTER_IPV4_CIDR_BLOCK_FORMAT_VALIDATOR = arg_parsers.CustomFunctionValidator(
    _IS_VALID_MASTER_IPV4_CIDR_BLOCK, _INVALID_GKE_MASTER_IPV4_CIDR_BLOCK_ERROR)

MASTER_IPV4_CIDR_FLAG = base.Argument(
    '--master-ipv4-cidr',
    default=None,
    type=MASTER_IPV4_CIDR_BLOCK_FORMAT_VALIDATOR,
    help="""\
    IPv4 CIDR range to use for the cluste master network. This should have a
    size of the netmask between 23 and 28.

    Cannot be specified unless '--enable-private-environnment' is also
    specified.
    """)

_IS_VALID_WEB_SERVER_IPV4_CIDR_BLOCK = (
    lambda cidr: _IsValidMasterIpv4CidrBlockWithMaskSize(cidr, 24, 29))

WEB_SERVER_IPV4_CIDR_BLOCK_FORMAT_VALIDATOR = arg_parsers.CustomFunctionValidator(
    _IS_VALID_WEB_SERVER_IPV4_CIDR_BLOCK,
    _INVALID_WEB_SERVER_IPV4_CIDR_BLOCK_ERROR)

WEB_SERVER_IPV4_CIDR_FLAG = base.Argument(
    '--web-server-ipv4-cidr',
    default=None,
    type=WEB_SERVER_IPV4_CIDR_BLOCK_FORMAT_VALIDATOR,
    help="""\
    IPv4 CIDR range to use for the Airflow web server network. This should have
    a size of the netmask between 24 and 29.

    Cannot be specified unless '--enable-private-environnment' is also
    specified.
    """)

_IS_VALID_CLOUD_SQL_IPV4_CIDR_BLOCK = (
    lambda cidr: _IsValidMasterIpv4CidrBlockWithMaskSize(cidr, 0, 24))

CLOUD_SQL_IPV4_CIDR_BLOCK_FORMAT_VALIDATOR = arg_parsers.CustomFunctionValidator(
    _IS_VALID_CLOUD_SQL_IPV4_CIDR_BLOCK,
    _INVALID_CLOUD_SQL_IPV4_CIDR_BLOCK_ERROR)

CLOUD_SQL_IPV4_CIDR_FLAG = base.Argument(
    '--cloud-sql-ipv4-cidr',
    default=None,
    type=CLOUD_SQL_IPV4_CIDR_BLOCK_FORMAT_VALIDATOR,
    help="""\
    IPv4 CIDR range to use for the Cloud SQL network. This should have a size
    of the netmask not greater than 24.

    Cannot be specified unless '--enable-private-environnment' is also
    specified.
    """)


def AddImportSourceFlag(parser, folder):
  """Adds a --source flag for a storage import command to a parser.

  Args:
    parser: argparse.ArgumentParser, the parser to which to add the flag
    folder: str, the top-level folder in the bucket into which the import
        command will write. Should not contain any slashes. For example, 'dags'.
  """
  base.Argument(
      '--source',
      required=True,
      help="""\
      Path to a local directory/file or Cloud Storage bucket/object to be
      imported into the {}/ subdirectory in the environment's Cloud Storage
      bucket. Cloud Storage paths must begin with 'gs://'.
      """.format(folder)).AddToParser(parser)


def AddImportDestinationFlag(parser, folder):
  """Adds a --destination flag for a storage import command to a parser.

  Args:
    parser: argparse.ArgumentParser, the parser to which to add the flag
    folder: str, the top-level folder in the bucket into which the import
        command will write. Should not contain any slashes. For example, 'dags'.
  """
  base.Argument(
      '--destination',
      metavar='DESTINATION',
      required=False,
      help="""\
      An optional subdirectory under the {}/ directory in the environment's
      Cloud Storage bucket into which to import files. May contain forward
      slashes to delimit multiple levels of subdirectory nesting, but should not
      contain leading or trailing slashes. If the DESTINATION does not exist, it
      will be created.
      """.format(folder)).AddToParser(parser)


def AddExportSourceFlag(parser, folder):
  """Adds a --source flag for a storage export command to a parser.

  Args:
    parser: argparse.ArgumentParser, the parser to which to add the flag
    folder: str, the top-level folder in the bucket from which the export
        command will read. Should not contain any slashes. For example, 'dags'.
  """
  base.Argument(
      '--source',
      help="""\
      An optional relative path to a file or directory to be exported from the
      {}/ subdirectory in the environment's Cloud Storage bucket.
      """.format(folder)).AddToParser(parser)


def AddExportDestinationFlag(parser):
  """Adds a --destination flag for a storage export command to a parser.

  Args:
    parser: argparse.ArgumentParser, the parser to which to add the flag
  """
  base.Argument(
      '--destination',
      metavar='DESTINATION',
      required=True,
      help="""\
      The path to an existing local directory or a Cloud Storage
      bucket/directory into which to export files.
      """).AddToParser(parser)


def AddDeleteTargetPositional(parser, folder):
  base.Argument(
      'target',
      nargs='?',
      help="""\
      A relative path to a file or subdirectory to delete within the
      {folder} Cloud Storage subdirectory. If not specified, the entire contents
      of the {folder} subdirectory will be deleted.
      """.format(folder=folder)).AddToParser(parser)


def _IsValidEnvVarName(name):
  """Validates that a user-provided arg is a valid environment variable name.

  Intended to be used as an argparse validator.

  Args:
    name: str, the environment variable name to validate

  Returns:
    bool, True if and only if the name is valid
  """
  return re.match('^[a-zA-Z_][a-zA-Z0-9_]*$', name) is not None


ENV_VAR_NAME_FORMAT_VALIDATOR = arg_parsers.CustomFunctionValidator(
    _IsValidEnvVarName, _ENV_VAR_NAME_ERROR)
CREATE_ENV_VARS_FLAG = base.Argument(
    '--env-variables',
    metavar='NAME=VALUE',
    type=arg_parsers.ArgDict(
        key_type=ENV_VAR_NAME_FORMAT_VALIDATOR, value_type=str),
    action=arg_parsers.UpdateAction,
    help='A comma-delimited list of environment variable `NAME=VALUE` '
    'pairs to provide to the Airflow scheduler, worker, and webserver '
    'processes. NAME may contain upper and lowercase letters, digits, '
    'and underscores, but they may not begin with a digit. '
    'To include commas as part of a `VALUE`, see `{top_command} topics'
    ' escaping` for information about overriding the delimiter.')


def IsValidUserPort(val):
  """Validates that a user-provided arg is a valid user port.

  Intended to be used as an argparse validator.

  Args:
    val: str, a string specifying a TCP port number to be validated

  Returns:
    int, the provided port number

  Raises:
    ArgumentTypeError: if the provided port is not an integer outside the
        system port range
  """
  port = int(val)
  if 1024 <= port and port <= 65535:
    return port
  raise argparse.ArgumentTypeError('PORT must be in range [1024, 65535].')


def ValidateDiskSize(parameter_name, disk_size):
  """Validates that a disk size is a multiple of some number of GB.

  Args:
    parameter_name: parameter_name, the name of the parameter, formatted as
        it would be in help text (e.g., '--disk-size' or 'DISK_SIZE')
    disk_size: int, the disk size in bytes

  Raises:
    exceptions.InvalidArgumentException: the disk size was invalid
  """
  gb_mask = (1 << 30) - 1
  if disk_size & gb_mask:
    raise exceptions.InvalidArgumentException(
        parameter_name, 'Must be an integer quantity of GB.')


def _AddPartialDictUpdateFlagsToGroup(update_type_group,
                                      clear_flag,
                                      remove_flag,
                                      update_flag,
                                      group_help_text=None):
  """Adds flags related to a partial update of arg represented by a dictionary.

  Args:
    update_type_group: argument group, the group to which flags should be added.
    clear_flag: flag, the flag to clear dictionary.
    remove_flag: flag, the flag to remove values from dictionary.
    update_flag: flag, the flag to add or update values in dictionary.
    group_help_text: (optional) str, the help info to apply to the created
        argument group. If not provided, then no help text will be applied to
        group.
  """
  group = update_type_group.add_argument_group(help=group_help_text)
  remove_group = group.add_mutually_exclusive_group(
      help=GENERAL_REMOVAL_FLAG_GROUP_DESCRIPTION)
  clear_flag.AddToParser(remove_group)
  remove_flag.AddToParser(remove_group)
  update_flag.AddToParser(group)


def AddNodeCountUpdateFlagToGroup(update_type_group):
  """Adds flag related to setting node count.

  Args:
    update_type_group: argument group, the group to which flag should be added.
  """
  update_type_group.add_argument(
      '--node-count',
      metavar='NODE_COUNT',
      type=arg_parsers.BoundedInt(lower_bound=3),
      help='The new number of nodes running the environment. Must be >= 3.')


def AddIpAliasEnvironmentFlags(update_type_group):
  """Adds flags related to IP aliasing to parser.

  IP alias flags are related to similar flags found within GKE SDK:
    /third_party/py/googlecloudsdk/command_lib/container/flags.py

  Args:
    update_type_group: argument group, the group to which flag should be added.
  """
  group = update_type_group.add_group(help='IP Alias (VPC-native)')
  ENABLE_IP_ALIAS_FLAG.AddToParser(group)
  CLUSTER_IPV4_CIDR_FLAG.AddToParser(group)
  SERVICES_IPV4_CIDR_FLAG.AddToParser(group)
  CLUSTER_SECONDARY_RANGE_NAME_FLAG.AddToParser(group)
  SERVICES_SECONDARY_RANGE_NAME_FLAG.AddToParser(group)


def AddPrivateIpEnvironmentFlags(update_type_group,
                                 web_server_cloud_sql_flags):
  """Adds flags related to private clusters to parser.

  Private cluster flags are related to similar flags found within GKE SDK:
    /third_party/py/googlecloudsdk/command_lib/container/flags.py

  Args:
    update_type_group: argument group, the group to which flag should be added.
    web_server_cloud_sql_flags: boolean, indicates if API includes new flags.
  """
  group = update_type_group.add_group(help='Private Clusters')
  ENABLE_PRIVATE_ENVIRONMENT_FLAG.AddToParser(group)
  ENABLE_PRIVATE_ENDPOINT_FLAG.AddToParser(group)
  MASTER_IPV4_CIDR_FLAG.AddToParser(group)
  if web_server_cloud_sql_flags:
    WEB_SERVER_IPV4_CIDR_FLAG.AddToParser(group)
    CLOUD_SQL_IPV4_CIDR_FLAG.AddToParser(group)


def AddPypiUpdateFlagsToGroup(update_type_group):
  """Adds flag related to setting Pypi updates.

  Args:
    update_type_group: argument group, the group to which flag should be added.
  """
  group = update_type_group.add_mutually_exclusive_group(
      PYPI_PACKAGES_FLAG_GROUP_DESCRIPTION)
  UPDATE_PYPI_FROM_FILE_FLAG.AddToParser(group)
  _AddPartialDictUpdateFlagsToGroup(
      group, CLEAR_PYPI_PACKAGES_FLAG, REMOVE_PYPI_PACKAGES_FLAG,
      UPDATE_PYPI_PACKAGE_FLAG)


def AddEnvVariableUpdateFlagsToGroup(update_type_group):
  """Adds flags related to updating environent variables.

  Args:
    update_type_group: argument group, the group to which flags should be added.
  """
  _AddPartialDictUpdateFlagsToGroup(update_type_group, CLEAR_ENV_VARIABLES_FLAG,
                                    REMOVE_ENV_VARIABLES_FLAG,
                                    UPDATE_ENV_VARIABLES_FLAG,
                                    ENV_VARIABLES_FLAG_GROUP_DESCRIPTION)


def AddAirflowConfigUpdateFlagsToGroup(update_type_group):
  """Adds flags related to updating Airflow configurations.

  Args:
    update_type_group: argument group, the group to which flags should be added.
  """
  _AddPartialDictUpdateFlagsToGroup(update_type_group,
                                    CLEAR_AIRFLOW_CONFIGS_FLAG,
                                    REMOVE_AIRFLOW_CONFIGS_FLAG,
                                    UPDATE_AIRFLOW_CONFIGS_FLAG,
                                    AIRFLOW_CONFIGS_FLAG_GROUP_DESCRIPTION)


def AddEnvUpgradeFlagsToGroup(update_type_group):
  """Adds flag group to perform in-place env upgrades.

  Args:
    update_type_group: argument group, the group to which flags should be added.
  """
  upgrade_group = update_type_group.add_argument_group(
      ENV_UPGRADE_GROUP_DESCRIPTION)
  UPDATE_AIRFLOW_VERSION_FLAG.AddToParser(upgrade_group)
  UPDATE_IMAGE_VERSION_FLAG.AddToParser(upgrade_group)


def AddLabelsUpdateFlagsToGroup(update_type_group):
  """Adds flags related to updating environment labels.

  Args:
    update_type_group: argument group, the group to which flags should be added.
  """
  labels_update_group = update_type_group.add_argument_group(
      LABELS_FLAG_GROUP_DESCRIPTION)
  labels_util.AddUpdateLabelsFlags(labels_update_group)


def FallthroughToLocationProperty(location_refs, flag_name, failure_msg):
  """Provides a list containing composer/location if `location_refs` is empty.

  This intended to be used as a fallthrough for a plural Location resource arg.
  The built-in fallthrough for plural resource args doesn't play well with
  properties, as it will iterate over each character in the string and parse
  it as the resource type. This function will parse the entire property and
  return a singleton list if `location_refs` is empty.

  Args:
    location_refs: [core.resources.Resource], a possibly empty list of location
        resource references
    flag_name: str, if `location_refs` is empty, and the composer/location
        property is also missing, an error message will be reported that will
        advise the user to set this flag name
    failure_msg: str, an error message to accompany the advisory described in
        the docs for `flag_name`.

  Returns:
    [core.resources.Resource]: a non-empty list of location resourc references.
    If `location_refs` was non-empty, it will be the same list, otherwise it
    will be a singleton list containing the value of the [composer/location]
    property.

  Raises:
    exceptions.RequiredArgumentException: both the user-provided locations
        and property fallback were empty
  """
  if location_refs:
    return location_refs

  fallthrough_location = parsers.GetLocation(required=False)
  if fallthrough_location:
    return [parsers.ParseLocation(fallthrough_location)]
  else:
    raise exceptions.RequiredArgumentException(flag_name, failure_msg)


def ValidateIpRanges(ip_ranges):
  """Validates list of IP ranges.

  Raises exception when any of the given strings is not a valid IPv4
  or IPv6 network IP range.
  Args:
    ip_ranges: [string], list of IP ranges to validate
  """
  for ip_range in ip_ranges:
    if six.PY2:
      ip_range = ip_range.decode()
    try:
      ipaddress.ip_network(ip_range)
    except:
      raise command_util.InvalidUserInputError(
          'Invalid IP range: [{}].'.format(ip_range))
