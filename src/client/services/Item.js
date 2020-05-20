import * as ApiUtil from '../utils/apiUtil';


export async function updateItem(item, fileMap) {
  const result = await ApiUtil.invokeApi(
    ApiUtil.API_INVOKE_TYPE_PUT,
    ApiUtil.API_ITEM.UPDATE_ITEM + item.itemId,
    item,
    fileMap
  );
  return result;
}

export async function removeItemImg(itemId) {
  const result = await ApiUtil.invokeApi(
    ApiUtil.API_INVOKE_TYPE_DELETE,
    ApiUtil.API_ITEM.REMOVE_ITEM_IMG + itemId,
  );
  return result;
}

export async function addItem(item, fileMap) {
  const result = await ApiUtil.invokeApi(
    ApiUtil.API_INVOKE_TYPE_POST,
    ApiUtil.API_ITEM.ADD_ITEM,
    item,
    fileMap
  );
  return result;
}

export async function deleteItem(itemId) {
  const result = await ApiUtil.invokeApi(
    ApiUtil.API_INVOKE_TYPE_DELETE,
    ApiUtil.API_ITEM.DELETE_ITEM + itemId,
    null
  );
  return result;
}

export async function getItemList(gridId) {
  const result = await ApiUtil.invokeApi(
    ApiUtil.API_INVOKE_TYPE_GET,
    ApiUtil.API_ITEM.GET_ITEM_LIST_BY_SPACE_ID + gridId,
    null
  );
  return result;
}

export async function getItem(itemId) {
  const result = await ApiUtil.invokeApi(
    ApiUtil.API_INVOKE_TYPE_GET,
    ApiUtil.API_ITEM.GET_ITEM + itemId,
    null
  );
  return result;
}
