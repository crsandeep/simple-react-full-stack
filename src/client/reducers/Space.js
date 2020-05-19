import * as ActionTypes from '../actionTypes/Space';
import * as Constants from '../constants/Space';

const initialState = {
  formMode: Constants.FORM_READONLY_MODE,
  pageLoading: false,
  validating: true,
  spaceList: [],
  editStatus: {
    isSuccess: null, data: null, message: null, operation: null
  },
  currentSpaceId: null,

  // form field
  spaceId: null,
  name: '',
  imgFile: null,
  imgPath: null,
  location: ''
};

export default function Space(state = initialState, action) {
  switch (action.type) {
    case ActionTypes.GET_SPACE_LIST:
      return {
        ...state,
        pageLoading: false,
        spaceList: action.data,
        editStatus: { isSuccess: (action.data !== null), data: action.data, operation: action.operation }
      };
    case ActionTypes.GET_SPACE:
      return {
        ...state,
        formMode: Constants.FORM_EDIT_MODE, // set form to edit
        pageLoading: false,
        spaceId: action.data.spaceId,
        name: action.data.name,
        imgFile: null,
        imgPath: action.data.imgPath,
        location: action.data.location,
        editStatus: { isSuccess: (action.data !== null), data: action.data, operation: action.operation }
      };
    case ActionTypes.COMPLETE_EDIT:
      return {
        ...state,
        pageLoading: false,
        formMode: Constants.FORM_READONLY_MODE, // set form to read only to hide inputs
        editStatus: { isSuccess: true, data: action.data, operation: action.operation }
      };
    case ActionTypes.FAIL_EDIT:
      return {
        ...state,
        pageLoading: false,
        editStatus: { isSuccess: false, message: action.message, operation: action.operation }
      };
    case ActionTypes.COMPLETE_REMOVE_SPACE_IMG:
      return {
        ...state,
        pageLoading: false,
        imgPath: null,
        imgFile: null,
        editStatus: { isSuccess: true, data: action.data, operation: action.operation }
      };
    case ActionTypes.FAIL_REMOVE_SPACE_IMG:
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
    case ActionTypes.UPDATE_FORM_MODE:
      return {
        ...state,
        pageLoading: false,
        formMode: action.mode,
        spaceId: null,
        name: '',
        imgFile: null,
        imgPath: null,
        location: ''
      };
    case ActionTypes.SET_CURRENT_SPACE_ID:
      return {
        ...state,
        currentSpaceId: action.spaceId
      };
    default:
      return state;
  }
}
