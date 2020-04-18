# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""notebooks instances api helper."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from enum import Enum
from googlecloudsdk.api_lib.notebooks import environments as env_util
from googlecloudsdk.api_lib.notebooks import util
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import resources


def CreateInstance(args):
  """Creates the Instance message for the create request.

  Args:
    args: Argparse object from Command.Run

  Returns:
    Instance of the Instance message.
  """

  def GetContainerImageFromExistingEnvironment():
    environment_service = util.GetClient().projects_locations_environments
    result = environment_service.Get(
        env_util.CreateEnvironmentDescribeRequest(args))
    return result.containerImage

  def GetVmImageFromExistingEnvironment():
    environment_service = util.GetClient().projects_locations_environments
    result = environment_service.Get(
        env_util.CreateEnvironmentDescribeRequest(args))
    return result.vmImage

  def GetKmsRelativeName():
    if args.IsSpecified('kms_key'):
      return args.CONCEPTS.kms_key.Parse().RelativeName()

  def GetNetworkRelativeName():
    if args.IsSpecified('network'):
      return args.CONCEPTS.network.Parse().RelativeName()

  def GetSubnetRelativeName():
    if args.IsSpecified('subnet'):
      return args.CONCEPTS.subnet.Parse().RelativeName()

  def CreateAcceleratorConfigMessage():
    accelerator_config = util.GetMessages().AcceleratorConfig
    type_enum = None
    if args.IsSpecified('accelerator_type'):
      type_enum = arg_utils.ChoiceEnumMapper(
          arg_name='accelerator-type',
          message_enum=accelerator_config.TypeValueValuesEnum,
          include_filter=lambda x: 'UNSPECIFIED' not in x).GetEnumForChoice(
              arg_utils.EnumNameToChoice(args.accelerator_type))
    return accelerator_config(
        type=type_enum, coreCount=args.accelerator_core_count)

  def GetBootDisk():
    type_enum = None
    if args.IsSpecified('boot_disk_type'):
      instance_message = util.GetMessages().Instance
      type_enum = arg_utils.ChoiceEnumMapper(
          arg_name='boot-disk-type',
          message_enum=instance_message.BootDiskTypeValueValuesEnum,
          include_filter=lambda x: 'UNSPECIFIED' not in x).GetEnumForChoice(
              arg_utils.EnumNameToChoice(args.boot_disk_type))
    return type_enum

  def GetDiskEncryption():
    instance_message = util.GetMessages().Instance
    type_enum = None
    if args.IsSpecified('disk_encryption'):
      type_enum = arg_utils.ChoiceEnumMapper(
          arg_name='disk-encryption',
          message_enum=instance_message.BootDiskTypeValueValuesEnum,
          include_filter=lambda x: 'UNSPECIFIED' not in x).GetEnumForChoice(
              arg_utils.EnumNameToChoice(args.disk_encryption))
    return type_enum

  def CreateContainerImageFromArgs():
    if args.IsSpecified('environment'):
      return GetContainerImageFromExistingEnvironment()
    if args.IsSpecified('container_repository'):
      container_image = util.GetMessages().ContainerImage(
          repository=args.container_repository, tag=args.container_tag)
      return container_image
    return None

  def CreateVmImageFromArgs():
    """Create VmImage Message from an environment or from args."""
    if args.IsSpecified('environment'):
      return GetVmImageFromExistingEnvironment()
    if args.IsSpecified('vm_image_project'):
      vm_image = util.GetMessages().VmImage(project=args.vm_image_project)
      if args.IsSpecified('vm_image_family'):
        vm_image.imageFamily = args.vm_image_family
      else:
        vm_image.imageName = args.vm_image_name
      return vm_image
    return None

  def GetInstanceOwnersFromArgs():
    if args.IsSpecified('instance_owners'):
      return [args.instance_owners]
    return []

  def GetLabelsFromArgs():
    if args.IsSpecified('labels'):
      labels_message = util.GetMessages().Instance.LabelsValue
      return labels_message(additionalProperties=[
          labels_message.AdditionalProperty(key=key, value=value)
          for key, value in args.labels.items()
      ])
    return None

  def GetMetadataFromArgs():
    if args.IsSpecified('metadata'):
      metadata_message = util.GetMessages().Instance.MetadataValue
      return metadata_message(additionalProperties=[
          metadata_message.AdditionalProperty(key=key, value=value)
          for key, value in args.metadata.items()
      ])
    return None

  instance = util.GetMessages().Instance(
      name=args.instance,
      postStartupScript=args.post_startup_script,
      bootDiskSizeGb=args.boot_disk_size,
      customGpuDriverPath=args.custom_gpu_driver_path,
      instanceOwners=GetInstanceOwnersFromArgs(),
      kmsKey=GetKmsRelativeName(),
      machineType=args.machine_type,
      network=GetNetworkRelativeName(),
      noProxyAccess=args.no_proxy_access,
      noPublicIp=args.no_public_ip,
      serviceAccount=args.service_account,
      subnet=GetSubnetRelativeName(),
      vmImage=CreateVmImageFromArgs(),
      acceleratorConfig=CreateAcceleratorConfigMessage(),
      bootDiskType=GetBootDisk(),
      containerImage=CreateContainerImageFromArgs(),
      diskEncryption=GetDiskEncryption(),
      labels=GetLabelsFromArgs(),
      metadata=GetMetadataFromArgs(),
      installGpuDriver=args.install_gpu_driver,
  )
  return instance


def CreateInstanceCreateRequest(args):
  parent = util.GetParentForInstance(args)
  instance = CreateInstance(args)
  return util.GetMessages().NotebooksProjectsLocationsInstancesCreateRequest(
      parent=parent, instance=instance, instanceId=args.instance)


def CreateInstanceListRequest(args):
  parent = util.GetParentFromArgs(args)
  return util.GetMessages().NotebooksProjectsLocationsInstancesListRequest(
      parent=parent)


def CreateInstanceDeleteRequest(args):
  instance = GetInstanceResource(args).RelativeName()
  return util.GetMessages().NotebooksProjectsLocationsInstancesDeleteRequest(
      name=instance)


def CreateInstanceDescribeRequest(args):
  instance = GetInstanceResource(args).RelativeName()
  return util.GetMessages().NotebooksProjectsLocationsInstancesGetRequest(
      name=instance)


def CreateInstanceRegisterRequest(args):
  instance = GetInstanceResource(args)
  parent = util.GetLocationResource(instance.locationsId,
                                    instance.projectsId).RelativeName()
  register_request = util.GetMessages().RegisterInstanceRequest(
      instanceId=instance.Name())
  return util.GetMessages().NotebooksProjectsLocationsInstancesRegisterRequest(
      parent=parent, registerInstanceRequest=register_request)


def CreateInstanceResetRequest(args):
  instance = GetInstanceResource(args).RelativeName()
  reset_request = util.GetMessages().ResetInstanceRequest()
  return util.GetMessages().NotebooksProjectsLocationsInstancesResetRequest(
      name=instance, resetInstanceRequest=reset_request)


def CreateInstanceStartRequest(args):
  instance = GetInstanceResource(args).RelativeName()
  start_request = util.GetMessages().StartInstanceRequest()
  return util.GetMessages().NotebooksProjectsLocationsInstancesStartRequest(
      name=instance, startInstanceRequest=start_request)


def CreateInstanceStopRequest(args):
  instance = GetInstanceResource(args).RelativeName()
  stop_request = util.GetMessages().StopInstanceRequest()
  return util.GetMessages().NotebooksProjectsLocationsInstancesStopRequest(
      name=instance, stopInstanceRequest=stop_request)


def CreateSetAcceleratorRequest(args):
  """Create and return Accelerator update request."""
  instance = GetInstanceResource(args).RelativeName()
  set_acc_request = util.GetMessages().SetInstanceAcceleratorRequest()
  accelerator_config = util.GetMessages().SetInstanceAcceleratorRequest
  if args.IsSpecified('accelerator_core_count'):
    set_acc_request.coreCount = args.accelerator_core_count
  if args.IsSpecified('accelerator_type'):
    type_enum = arg_utils.ChoiceEnumMapper(
        arg_name='accelerator-type',
        message_enum=accelerator_config.TypeValueValuesEnum,
        include_filter=lambda x: 'UNSPECIFIED' not in x).GetEnumForChoice(
            arg_utils.EnumNameToChoice(args.accelerator_type))
    set_acc_request.type = type_enum
  return util.GetMessages(
  ).NotebooksProjectsLocationsInstancesSetAcceleratorRequest(
      name=instance, setInstanceAcceleratorRequest=set_acc_request)


def CreateSetLabelsRequest(args):
  instance = GetInstanceResource(args).RelativeName()
  set_label_request = util.GetMessages().SetInstanceLabelsRequest()
  labels_message = util.GetMessages().SetInstanceLabelsRequest.LabelsValue
  set_label_request.labels = labels_message(additionalProperties=[
      labels_message.AdditionalProperty(key=key, value=value)
      for key, value in args.labels.items()
  ])
  return util.GetMessages().NotebooksProjectsLocationsInstancesSetLabelsRequest(
      name=instance, setInstanceLabelsRequest=set_label_request)


def CreateSetMachineTypeRequest(args):
  instance = GetInstanceResource(args).RelativeName()
  set_machine_request = util.GetMessages().SetInstanceMachineTypeRequest(
      machineType=args.machine_type)
  return util.GetMessages(
  ).NotebooksProjectsLocationsInstancesSetMachineTypeRequest(
      name=instance, setInstanceMachineTypeRequest=set_machine_request)


def GetInstanceResource(args):
  return args.CONCEPTS.instance.Parse()


def GetInstanceURI(resource):
  instance = resources.REGISTRY.ParseRelativeName(
      resource.name, collection='notebooks.projects.locations.instances')
  return instance.SelfLink()


class OperationType(Enum):
  CREATE = (log.CreatedResource, 'created')
  UPDATE = (log.UpdatedResource, 'updated')
  DELETE = (log.DeletedResource, 'deleted')
  RESET = (log.ResetResource, 'reset')


def HandleLRO(operation,
              args,
              instance_service,
              operation_type=OperationType.UPDATE):
  """Handles Long Running Operations for both cases of async.

  Args:
    operation: The operation to poll.
    args: ArgParse instance containing user entered arguments.
    instance_service: The service to get the resource after the long running
      operation completes.
    operation_type: Enum value of type OperationType indicating the kind of
      operation to wait for.

  Raises:
    apitools.base.py.HttpError: if the request returns an HTTP error

  Returns:
    The Instance resource if synchronous, else the Operation Resource.
  """
  logging_method = operation_type.value[0]
  if args.async_:
    logging_method(
        util.GetOperationResource(operation.name),
        kind='notebooks instance {0}'.format(args.instance),
        is_async=True)
    return operation
  else:
    response = util.WaitForOperation(
        operation,
        'Waiting for operation on Instance [{}] to be {} with [{}]'.format(
            args.instance, operation_type.value[1], operation.name),
        service=instance_service,
        is_delete=(operation_type.value[1] == 'deleted'))
    logging_method(
        util.GetOperationResource(operation.name),
        kind='notebooks instance {0}'.format(args.instance),
        is_async=False)
    return response
