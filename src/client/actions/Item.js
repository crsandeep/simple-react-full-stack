import * as ActionTypes from '../actionTypes/Item';

export const sagaGetItemList = (spaceId) =>({
    type: ActionTypes.SAGA_GET_ITEM_LIST,
    spaceId: spaceId,
})

export const sagaGetItem = (itemId) =>({
    type: ActionTypes.SAGA_GET_ITEM,
    itemId: itemId,
})

export const sagaAddItem = (item, fileMap) =>({
    type: ActionTypes.SAGA_ADD_ITEM,
    item: item,
    fileMap: fileMap
})

export const sagaUpdateItem = (item, fileMap) =>({
    type: ActionTypes.SAGA_UPDATE_ITEM,
    item: item,
    fileMap: fileMap
})

export const sagaRemoveItemImg = (itemId) =>({
    type: ActionTypes.SAGA_REMOVE_ITEM_IMG,
    itemId: itemId,
})


export const sagaDeleteItem = (spaceId, itemId) =>({
    type: ActionTypes.SAGA_DELETE_ITEM,
    spaceId: spaceId,
    itemId: itemId,
})

export const startLoading = () => ({
    type: ActionTypes.PAGE_LOADING
});

export const getItemList = data => ({
    type: ActionTypes.GET_ITEM_LIST,
    data: data
});

export const getItem = data => ({
    type: ActionTypes.GET_ITEM,
    data: data
});

export const completeEdit = (data, operation) => ({
    type: ActionTypes.COMPLETE_EDIT,
    data: data,
    operation:operation
});

export const failEdit = (message, operation) =>({
    type: ActionTypes.FAIL_EDIT,
    message: message,
    operation:operation
});

export const updateFormMode = mode =>({
    type: ActionTypes.UPDATE_FORM_MODE,
    mode: mode
});

export const completeRemoveItemImg = (data) => ({
    type: ActionTypes.COMPLETE_REMOVE_ITEM_IMG,
    data: data
});

export const failRemoveItemImg = (message) => ({
    type: ActionTypes.FAIL_REMOVE_ITEM_IMG,
    message: message,
});

