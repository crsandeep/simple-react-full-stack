import * as ApiUtil from '../utils/apiUtil';

export const updateItem = async (item, fileMap) => await ApiUtil.invokeApi(
  ApiUtil.API_INVOKE_TYPE_PUT,
  ApiUtil.API_ITEM.UPDATE_ITEM + item.itemId,
  item,
  fileMap
);

export const removeItemImg = async itemId => await ApiUtil.invokeApi(
  ApiUtil.API_INVOKE_TYPE_DELETE,
  ApiUtil.API_ITEM.REMOVE_ITEM_IMG + itemId,
);


export const addItem = async (item, fileMap) => await ApiUtil.invokeApi(
  ApiUtil.API_INVOKE_TYPE_POST,
  ApiUtil.API_ITEM.ADD_ITEM,
  item,
  fileMap
);


export const deleteItem = async itemId => await ApiUtil.invokeApi(
  ApiUtil.API_INVOKE_TYPE_DELETE,
  ApiUtil.API_ITEM.DELETE_ITEM + itemId,
  null
);


export const getItemList = async gridId => await ApiUtil.invokeApi(
  ApiUtil.API_INVOKE_TYPE_GET,
  ApiUtil.API_ITEM.GET_ITEM_LIST_BY_SPACE_ID + gridId,
  null
);

export const getItem = async itemId => await ApiUtil.invokeApi(
  ApiUtil.API_INVOKE_TYPE_GET,
  ApiUtil.API_ITEM.GET_ITEM + itemId,
  null
);
