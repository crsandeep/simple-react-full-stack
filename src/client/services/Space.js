import * as ApiUtil from '../utils/apiUtil';

export const updateSpace = async (space, fileMap) => await ApiUtil.invokeApi(
  ApiUtil.API_INVOKE_TYPE_PUT,
  ApiUtil.API_SPACE.UPDATE_SPACE + space.spaceId,
  space,
  fileMap
);

export const removeSpaceImg = async spaceId => await ApiUtil.invokeApi(
  ApiUtil.API_INVOKE_TYPE_DELETE,
  ApiUtil.API_SPACE.REMOVE_SPACE_IMG + spaceId,
);


export const addSpace = async (space, fileMap) => await ApiUtil.invokeApi(
  ApiUtil.API_INVOKE_TYPE_POST,
  ApiUtil.API_SPACE.ADD_SPACE,
  space,
  fileMap
);


export const deleteSpace = async spaceId => await ApiUtil.invokeApi(
  ApiUtil.API_INVOKE_TYPE_DELETE,
  ApiUtil.API_SPACE.DELETE_SPACE + spaceId,
  null
);


export const getSpaceList = async userId => await ApiUtil.invokeApi(
  ApiUtil.API_INVOKE_TYPE_GET,
  ApiUtil.API_SPACE.GET_SPACE_LIST_BY_USER_ID + userId,
  null
);

export const getSpace = async spaceId => await ApiUtil.invokeApi(
  ApiUtil.API_INVOKE_TYPE_GET,
  ApiUtil.API_SPACE.GET_SPACE + spaceId,
  null
);
