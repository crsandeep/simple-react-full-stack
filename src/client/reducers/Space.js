import * as ActionTypes from '../actionTypes/Space'
import * as Constants from '../constants/Space';

const initialState = {
  formMode: Constants.FORM_READONLY_MODE,
  pageLoading: false,
  validating: true,
  spaceList: [],
  editStatus: { isSuccess: null, data: null, message: null, operation:null },

  //form field
  spaceId: null,
  name: '',
  colorCode: '',
  imgFile: null,
  imgPath: null,
  tags:null,
  location: '',
  sizeUnit: null,
  sizeWidth: null,
  sizeHeight: null,
  sizeDepth: null,
};
 
export default function Space (state = initialState, action) {
  switch (action.type) {
    case ActionTypes.GET_SPACE_LIST:
      return {
          ...state,
          pageLoading: false, 
          spaceList: action.data
        }
    case ActionTypes.GET_SPACE:
      return { ...state, 
        formMode: Constants.FORM_EDIT_MODE, //set form to edit
        pageLoading: false, 
        spaceId: action.data.spaceId,
        name: action.data.name,
        colorCode: action.data.colorCode,
        imgFile: null,
        imgPath: action.data.imgPath,
        tags: action.data.tags,
        location: action.data.location,
        sizeUnit: action.data.sizeUnit,
        sizeWidth: action.data.sizeWidth,
        sizeHeight: action.data.sizeHeight,
        sizeDepth: action.data.sizeDepth,
      }
    case ActionTypes.COMPLETE_EDIT:
      return { ...state, 
        pageLoading: false, 
        formMode: Constants.FORM_READONLY_MODE,   //set form to read only to hide inputs
        editStatus: { isSuccess: true, data: action.data, operation:action.operation } 
    }
    case ActionTypes.FAIL_EDIT:
      return { 
        ...state, 
        pageLoading: false, 
        editStatus: { isSuccess: false, message: action.message, operation:action.operation } 
    }
    case ActionTypes.COMPLETE_REMOVE_SPACE_IMG:
      return { 
        ...state, 
        pageLoading: false,
        imgPath: null,
        imgFile: null,
        editStatus: { 
          isSuccess: true, 
          data: null, 
          message: null, 
          operation:Constants.OPERATION_REMOVE_IMG} 
      }
    case ActionTypes.FAIL_REMOVE_SPACE_IMG:
      return { 
        ...state, 
        pageLoading: false,
        editStatus: { 
          isSuccess: false, 
          data:null,
          message: action.message, 
          operation:Constants.OPERATION_REMOVE_IMG 
        } 
      }
    case ActionTypes.PAGE_LOADING:
      return { ...state, 
        pageLoading: true, 
      }
    case ActionTypes.UPDATE_FORM_MODE:
      return {...state,
          pageLoading:false,
          formMode: action.mode,
          spaceId: null,
          name: '',
          colorCode: '',
          imgFile: null,
          imgPath: null,
          tags:null,
          location: '',
          sizeUnit: null,
          sizeWidth: null,
          sizeHeight: null,
          sizeDepth: null,
      }

    default:
      return state
  }
}
