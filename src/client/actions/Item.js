import * as ActionTypes from '../actionTypes/Item';

export const sagaGetItemList = gridId => ({
  type: ActionTypes.SAGA_GET_ITEM_LIST,
  gridId
});

export const sagaGetItem = itemId => ({
  type: ActionTypes.SAGA_GET_ITEM,
  itemId
});

export const sagaAddItem = (item, fileMap) => ({
  type: ActionTypes.SAGA_ADD_ITEM,
  item,
  fileMap
});

export const sagaUpdateItem = (item, fileMap) => ({
  type: ActionTypes.SAGA_UPDATE_ITEM,
  item,
  fileMap
});

export const sagaRemoveItemImg = itemId => ({
  type: ActionTypes.SAGA_REMOVE_ITEM_IMG,
  itemId
});


export const sagaDeleteItem = (gridId, itemId) => ({
  type: ActionTypes.SAGA_DELETE_ITEM,
  gridId,
  itemId
});

export const startLoading = () => ({
  type: ActionTypes.PAGE_LOADING
});

export const getItemList = data => ({
  type: ActionTypes.GET_ITEM_LIST,
  data
});

export const getItem = data => ({
  type: ActionTypes.GET_ITEM,
  data
});

export const completeEdit = (data, operation) => ({
  type: ActionTypes.COMPLETE_EDIT,
  data,
  operation
});

export const failEdit = (message, operation) => ({
  type: ActionTypes.FAIL_EDIT,
  message,
  operation
});

export const updateFormMode = mode => ({
  type: ActionTypes.UPDATE_FORM_MODE,
  mode
});

export const completeRemoveItemImg = data => ({
  type: ActionTypes.COMPLETE_REMOVE_ITEM_IMG,
  data
});

export const failRemoveItemImg = message => ({
  type: ActionTypes.FAIL_REMOVE_ITEM_IMG,
  message
});
