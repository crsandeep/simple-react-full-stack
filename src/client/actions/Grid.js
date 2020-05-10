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

export const getGridList = (data, operation) => ({
  type: ActionTypes.GET_GRID_LIST,
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


export const setCurrentGridId = gridId => ({
  type: ActionTypes.SET_CURRENT_GRID_ID,
  gridId
});
