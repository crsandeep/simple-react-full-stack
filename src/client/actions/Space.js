import * as ActionTypes from '../actionTypes/Space';

export const sagaGetSpaceList = userId => ({
  type: ActionTypes.SAGA_GET_SPACE_LIST,
  userId
});

export const sagaGetSpace = spaceId => ({
  type: ActionTypes.SAGA_GET_SPACE,
  spaceId
});

export const sagaAddSpace = (space, fileMap) => ({
  type: ActionTypes.SAGA_ADD_SPACE,
  space,
  fileMap
});

export const sagaUpdateSpace = (space, fileMap) => ({
  type: ActionTypes.SAGA_UPDATE_SPACE,
  space,
  fileMap
});

export const sagaRemoveSpaceImg = spaceId => ({
  type: ActionTypes.SAGA_REMOVE_SPACE_IMG,
  spaceId
});


export const sagaDeleteSpace = (userId, spaceId) => ({
  type: ActionTypes.SAGA_DELETE_SPACE,
  userId,
  spaceId
});

export const startLoading = () => ({
  type: ActionTypes.PAGE_LOADING
});

export const getSpaceList = (data, operation) => ({
  type: ActionTypes.GET_SPACE_LIST,
  data,
  operation
});

export const getSpace = (data, operation) => ({
  type: ActionTypes.GET_SPACE,
  data,
  operation
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

export const completeRemoveSpaceImg = (data, operation) => ({
  type: ActionTypes.COMPLETE_REMOVE_SPACE_IMG,
  data,
  operation
});

export const failRemoveSpaceImg = (message, operation) => ({
  type: ActionTypes.FAIL_REMOVE_SPACE_IMG,
  message,
  operation
});


export const setCurrentSpaceId = spaceId => ({
  type: ActionTypes.SET_CURRENT_SPACE_ID,
  spaceId
});
