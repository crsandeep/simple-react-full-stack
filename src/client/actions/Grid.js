import * as ActionTypes from '../actionTypes/Grid';

export const sagaGetGridList = spaceId => ({
  type: ActionTypes.SAGA_GET_GRID_LIST,
  spaceId
});

export const sagaSaveGrids = grids => ({
  type: ActionTypes.SAGA_SAVE_GRIDS,
  grids
});


export const sagaDeleteGrid = gridId => ({
  type: ActionTypes.SAGA_DELETE_GRID,
  gridId
});

export const startLoading = () => ({
  type: ActionTypes.PAGE_LOADING
});

export const getGridList = data => ({
  type: ActionTypes.GET_GRID_LIST,
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

export const clearEditStatus = () => ({
  type: ActionTypes.CLEAR_EDIT_STATUS
});
