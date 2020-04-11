import * as ActionTypes from '../actionTypes/Space';

export const sagaGetSpaceList = (userId) =>({
    type: ActionTypes.SAGA_GET_SPACE_LIST,
    userId: userId,
})

export const sagaGetSpace = (spaceId) =>({
    type: ActionTypes.SAGA_GET_SPACE,
    spaceId: spaceId,
})

export const sagaAddSpace = (space, fileMap) =>({
    type: ActionTypes.SAGA_ADD_SPACE,
    space: space,
    fileMap: fileMap
})

export const sagaUpdateSpace = (space, fileMap) =>({
    type: ActionTypes.SAGA_UPDATE_SPACE,
    space: space,
    fileMap: fileMap
})

export const sagaRemoveSpaceImg = (spaceId) =>({
    type: ActionTypes.SAGA_REMOVE_SPACE_IMG,
    spaceId: spaceId,
})


export const sagaDeleteSpace = (userId, spaceId) =>({
    type: ActionTypes.SAGA_DELETE_SPACE,
    userId: userId,
    spaceId: spaceId,
})

export const startLoading = () => ({
    type: ActionTypes.PAGE_LOADING
});

export const getSpaceList = data => ({
    type: ActionTypes.GET_SPACE_LIST,
    data: data
});

export const getSpace = data => ({
    type: ActionTypes.GET_SPACE,
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

export const completeRemoveSpaceImg = (data) => ({
    type: ActionTypes.COMPLETE_REMOVE_SPACE_IMG,
    data: data
});

export const failRemoveSpaceImg = (message) => ({
    type: ActionTypes.FAIL_REMOVE_SPACE_IMG,
    message: message,
});

