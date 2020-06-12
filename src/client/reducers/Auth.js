import * as ActionTypes from '../actionTypes/Auth';

const initialState = {
  pageLoading: false,
  editStatus: {
    isSuccess: null, data: null, messageCd: null, message: null, operation: null
  },
  currentJwt: null
};

export default function Auth(state = initialState, action) {
  switch (action.type) {
    case ActionTypes.REGISTER_COMPLETE:
    case ActionTypes.LOGIN_COMPLETE:
      return {
        ...state,
        pageLoading: false,
        editStatus: {
          isSuccess: action.operResult.isSuccess, data: action.operResult.payload, operation: action.operationCd
        },
        currentJwt: action.operResult.payload
      };
    case ActionTypes.REGISTER_FAIL:
    case ActionTypes.LOGIN_FAIL:
      return {
        ...state,
        pageLoading: false,
        editStatus: {
          isSuccess: false, messageCd: action.operResult.messageCd, message: action.operResult.message, operation: action.operationCd
        },
        currentJwt: null
      };
    case ActionTypes.PAGE_LOADING:
      return {
        ...state,
        pageLoading: true,
        editStatus: { // clear previous edit status
          isSuccess: null, data: null, messageCd: null, message: null, operation: null
        }
      };
    case ActionTypes.LOGIN_CLEAR:
      return {
        ...state,
        currentJwt: null
      };
    default:
      return state;
  }
}
