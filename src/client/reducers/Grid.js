import * as ActionTypes from '../actionTypes/Grid';

const initialState = {
  pageLoading: false,
  gridList: [],
  editStatus: {
    isSuccess: null, data: null, message: null, operation: null
  }
};

export default function Grid(state = initialState, action) {
  switch (action.type) {
    case ActionTypes.GET_GRID_LIST:
      return {
        ...state,
        pageLoading: false,
        gridList: action.data
      };
    case ActionTypes.COMPLETE_EDIT:
      return {
        ...state,
        pageLoading: false,
        gridList: action.data,
        editStatus: { isSuccess: true, data: action.data, operation: action.operation }
      };
    case ActionTypes.FAIL_EDIT:
      return {
        ...state,
        pageLoading: false,
        editStatus: { isSuccess: false, message: action.message, operation: action.operation }
      };
    case ActionTypes.PAGE_LOADING:
      return {
        ...state,
        pageLoading: true
      };
    default:
      return state;
  }
}
