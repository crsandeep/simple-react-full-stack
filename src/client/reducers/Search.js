import * as ActionTypes from '../actionTypes/Search';

const initialState = {
  pageLoading: false,
  validating: true,
  itemList: [],
  editStatus: {
    isSuccess: null, data: null, message: null, operation: null
  }
};

export default function Search(state = initialState, action) {
  switch (action.type) {
    case ActionTypes.SEARCH_ITEM:
      return {
        ...state,
        pageLoading: false,
        itemList: action.data,
        editStatus: { isSuccess: (action.data !== null), data: action.data, operation: action.operation }
      };
    case ActionTypes.PAGE_LOADING:
      return {
        ...state,
        pageLoading: true,
        editStatus: { // clear previous edit status
          isSuccess: null, data: null, message: null, operation: null
        }
      };
    default:
      return state;
  }
}
