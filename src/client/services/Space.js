import * as ApiUtil from '../utils/apiUtil';

export async function updateSpace(space, fileMap) {
  const result = await ApiUtil.invokeApi(
    ApiUtil.API_INVOKE_TYPE_PUT,
    ApiUtil.API_SPACE.UPDATE_SPACE + space.spaceId,
    space,
    fileMap
  );
  return result;
}

export async function removeSpaceImg(spaceId) {
  const result = await ApiUtil.invokeApi(
    ApiUtil.API_INVOKE_TYPE_DELETE,
    ApiUtil.API_SPACE.REMOVE_SPACE_IMG + spaceId,
  );
  return result;
}

export async function addSpace(space, fileMap) {
  const result = await ApiUtil.invokeApi(
    ApiUtil.API_INVOKE_TYPE_POST,
    ApiUtil.API_SPACE.ADD_SPACE,
    space,
    fileMap
  );
  return result;
}

export async function deleteSpace(spaceId) {
  const result = await ApiUtil.invokeApi(
    ApiUtil.API_INVOKE_TYPE_DELETE,
    ApiUtil.API_SPACE.DELETE_SPACE + spaceId,
    null
  );
  return result;
}

export async function getSpaceList(userId) {
  const result = await ApiUtil.invokeApi(
    ApiUtil.API_INVOKE_TYPE_GET,
    ApiUtil.API_SPACE.GET_SPACE_LIST_BY_USER_ID + userId,
    null
  );
  return result;
}

export async function getSpace(spaceId) {
  const result = await ApiUtil.invokeApi(
    ApiUtil.API_INVOKE_TYPE_GET,
    ApiUtil.API_SPACE.GET_SPACE + spaceId,
    null
  );
  return result;
}
