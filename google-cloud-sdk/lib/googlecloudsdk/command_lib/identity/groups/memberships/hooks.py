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

"""Declarative hooks for Cloud Identity Groups Memberships CLI."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.identity import cloudidentity_client as ci_client
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.identity.groups import hooks as groups_hooks
from googlecloudsdk.core.util import times


# request hooks
def SetMembership(unused_ref, args, request):
  """Set Membership in request.

  Args:
    unused_ref: unused.
    args: The argparse namespace.
    request: The request to modify.

  Returns:
    The updated request.

  """

  version = groups_hooks.GetApiVersion(args)
  messages = ci_client.GetMessages(version)
  request.membership = messages.Membership()

  return request


def SetEntityKey(unused_ref, args, request):
  """Set EntityKey in group resource.

  Args:
    unused_ref: unused.
    args: The argparse namespace.
    request: The request to modify.

  Returns:
    The updated request.

  """

  version = groups_hooks.GetApiVersion(args)
  messages = ci_client.GetMessages(version)
  if hasattr(args, 'member_email') and args.IsSpecified('member_email'):
    entity_key = messages.EntityKey(id=args.member_email)
    if hasattr(request.membership, 'memberKey'):
      request.membership.memberKey = entity_key
    elif hasattr(request.membership, 'preferredMemberKey'):
      request.membership.preferredMemberKey = entity_key

  return request


def SetPageSize(unused_ref, args, request):
  """Set page size to request.pageSize.

  Args:
    unused_ref: unused.
    args: The argparse namespace.
    request: The request to modify.

  Returns:
    The updated request.

  """

  if hasattr(args, 'page_size') and args.IsSpecified('page_size'):
    request.pageSize = int(args.page_size)

  return request


def SetMembershipParent(unused_ref, args, request):
  """Set resource name to request.parent.

  Args:
    unused_ref: unused.
    args: The argparse namespace.
    request: The request to modify.

  Returns:
    The updated request.

  """

  version = groups_hooks.GetApiVersion(args)
  if args.IsSpecified('group_email'):
    # Resource name example: groups/03qco8b4452k99t
    request.parent = groups_hooks.ConvertEmailToResourceName(
        version, args.group_email, 'group_email')

  return request


def SetMembershipResourceName(unused_ref, args, request):
  """Set membership resource name to request.name.

  Args:
    unused_ref: unused.
    args: The argparse namespace.
    request: The request to modify.

  Returns:
    The updated request.

  """

  version = groups_hooks.GetApiVersion(args)
  name = ''
  if args.IsSpecified('group_email') and args.IsSpecified('member_email'):
    name = ConvertEmailToMembershipResourceName(
        version, args, 'group_email', 'member_email')
  else:
    raise exceptions.InvalidArgumentException(
        'Must specify group-email and member-email argument.')

  request.name = name

  if hasattr(request, 'membership'):
    request.membership.name = name

  return request


def SetMembershipRoles(unused_ref, args, request):
  """Set MembershipRoles to request.membership.roles.

  Args:
    unused_ref: unused.
    args: The argparse namespace.
    request: The request to modify.

  Returns:
    The updated request.

  """

  version = groups_hooks.GetApiVersion(args)
  if not hasattr(args, 'roles') or not args.IsSpecified('roles'):
    empty_list = []
    request.membership.roles = ReformatMembershipRoles(version, empty_list)
  else:
    request.membership.roles = ReformatMembershipRoles(version, args.roles)

  return request


def SetExpiryDetail(unused_ref, args, request):
  """Set expiration to request.membership.expiryDetail.

  Args:
    unused_ref: unused.
    args: The argparse namespace.
    request: The request to modify.

  Returns:
    The updated request.

  """

  version = groups_hooks.GetApiVersion(args)
  if hasattr(args, 'expiration') and args.IsSpecified('expiration'):
    request.membership.expiryDetail = ReformatExpiryDetail(
        version, args.expiration)

  return request


def UpdateMembershipRoles(unused_ref, args, request):
  """Update MembershipRoles to request.membership.roles.

  Args:
    unused_ref: unused.
    args: The argparse namespace.
    request: The request to modify.

  Returns:
    The updated request.

  """

  version = groups_hooks.GetApiVersion(args)
  if hasattr(args, 'roles') and args.IsSpecified('roles'):
    request.membership.roles = ReformatMembershipRoles(version, args.roles)

  return request


def UpdateRoles(unused_ref, args, request):
  """Update 'MembershipRoles' to request.modifyMembershipRolesRequest.

  Args:
    unused_ref: unused.
    args: The argparse namespace.
    request: The request to modify.

  Returns:
    The updated request.

  """

  # Following logic is used only when 'add-roles' parameter is used.
  if hasattr(args, 'add_roles') and args.IsSpecified('add_roles'):
    # Convert a comma separated string to a list of strings.
    role_list = args.add_roles.split(',')

    # Convert a list of strings to a list of MembershipRole objects.
    version = groups_hooks.GetApiVersion(args)
    roles = []
    messages = ci_client.GetMessages(version)
    for role in role_list:
      membership_role = messages.MembershipRole(name=role)
      roles.append(membership_role)

    request.modifyMembershipRolesRequest = messages.ModifyMembershipRolesRequest(
        addRoles=roles)

  return request


# processor hooks
def UpdateRolesParamsToUpdate(arg_dict):
  """Update roles params to update to modifyMembershipRolesRequest.updateRolesParams.

  Note: This method should be used in ALPHA release only.

  Args:
    arg_dict: ArgDicts, RolesParams to update.
    (e.g. OrderedDict([(u'OWNER', u'expiration=4d')]))
  Returns:
    List of updateRolesParams to update.
  """

  roles_params = []
  # TODO(b/147011481): Remove hard coded version info if necessary.
  messages = ci_client.GetMessages('v1alpha1')
  arg_name = '--update-roles-params'
  for role, params in arg_dict.items():
    # Tokenize params to name and value
    # Example params: expiration=6m
    # ==> name: expiration, value: 6m
    # TODO(b/142829363): Implement to support multiple params if necessary.
    param_name, param_value = TokenizeParams(params, arg_name)

    # Instantiate MembershipRole object.
    # TODO(b/147011481): Remove hard coded version info if necessary.
    expiry_detail = ReformatExpiryDetail('v1alpha1', param_value)
    membership_role = messages.MembershipRole(
        name=role, expiryDetail=expiry_detail)

    # Create 'update_mask' string
    update_mask = GetUpdateMask(param_name, arg_name)

    update_membership_roles_params = messages.UpdateMembershipRolesParams(
        fieldMask=update_mask, membershipRole=membership_role)

    roles_params.append(update_membership_roles_params)

  return roles_params


# private methods
def ConvertEmailToMembershipResourceName(
    version, args, group_arg_name, member_arg_name):
  """Convert email to membership resource name.

  Args:
    version: Release track information
    args: The argparse namespace
    group_arg_name: argument/parameter name related to group info
    member_arg_name: argument/parameter name related to member info

  Returns:
    Membership Id (e.g. groups/11zu0gzc3tkdgn2/memberships/1044279104595057141)

  """

  # Resource name example: groups/03qco8b4452k99t
  group_id = groups_hooks.ConvertEmailToResourceName(
      version, args.group_email, group_arg_name)

  lookup_membership_name_resp = ci_client.LookupMembershipName(
      version, group_id, args.member_email)

  if 'name' in lookup_membership_name_resp:
    return lookup_membership_name_resp['name']

  # If there is no group exists (or deleted) for the given group email,
  # print out an error message.
  parameter_name = group_arg_name + ', ' + member_arg_name
  error_msg = ('There is no such a membership associated with the specified '
               'arguments:{}, {}').format(args.group_email, args.member_email)

  raise exceptions.InvalidArgumentException(parameter_name, error_msg)


def ReformatExpiryDetail(version, expiration):
  """Reformat expiration string to ExpiryDetail object.

  Args:
    version: Release track information
    expiration: expiration string.

  Returns:
    ExpiryDetail object that contains the expiration data.

  """

  messages = ci_client.GetMessages(version)
  duration = 'P' + expiration
  expiration_ts = FormatDateTime(duration)
  return messages.MembershipRoleExpiryDetail(expireTime=expiration_ts)


def ReformatMembershipRoles(version, roles_list):
  """Reformat roles string to MembershipRoles object list.

  Args:
    version: Release track information
    roles_list: list of roles in a string format.

  Returns:
    List of MembershipRoles object.

  """

  messages = ci_client.GetMessages(version)
  roles = []
  if not roles_list:
    # If no MembershipRole is provided, 'MEMBER' is used as a default value.
    roles.append(messages.MembershipRole(name='MEMBER'))
    return roles

  for role in roles_list:
    new_membership_role = messages.MembershipRole(name=role)
    roles.append(new_membership_role)

  return roles


def GetUpdateMask(role_param, arg_name):
  """Set the update mask on the request based on the role param.

  Args:
    role_param: The param that needs to be updated for a specified role.
    arg_name: The argument name

  Returns:
    Update mask

  Raises:
    InvalidArgumentException: If no fields are specified to update.

  """
  update_mask = []

  if role_param == 'expiration':
    update_mask.append('expiry_detail.expire_time')

  if not update_mask:
    raise exceptions.InvalidArgumentException(
        arg_name, 'Must specify at least one field mask.')

  return ','.join(update_mask)


def FormatDateTime(duration):
  """Return RFC3339 string for datetime that is now + given duration.

  Args:
    duration: string ISO 8601 duration, e.g. 'P5D' for period 5 days.

  Returns:
    string timestamp

  """

  # We use a format that preserves +00:00 for UTC to match timestamp format
  # returned by container API.
  fmt = '%Y-%m-%dT%H:%M:%S.%3f%Oz'

  return times.FormatDateTime(
      times.ParseDateTime(duration, tzinfo=times.UTC), fmt=fmt)


def TokenizeParams(params, arg_name):
  token_list = params.split('=')
  if len(token_list) == 2:
    return token_list[0], token_list[1]

  raise exceptions.InvalidArgumentException(
      arg_name, 'Invalid format of params: ' + params)
