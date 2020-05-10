import * as ActionTypes from '../actionTypes/Grid';

const initialState = {
  pageLoading: false,
  gridList: [],
  editStatus: {
    isSuccess: null, data: null, message: null, operation: null
  },
  currentGridId: null
};

export default function Grid(state = initialState, action) {
  switch (action.type) {
    case ActionTypes.GET_GRID_LIST:
      return {
        ...state,
        pageLoading: false,
        gridList: action.data,
        editStatus: { isSuccess: (action.data !== null), data: action.data, operation: action.operation }
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
        pageLoading: true,
        editStatus: { // clear previous edit status
          isSuccess: null, data: null, message: null, operation: null
        }
      };
    case ActionTypes.SET_CURRENT_GRID_ID:
      return {
        ...state,
        currentGridId: action.gridId
      };
    default:
      return state;
  }
}
