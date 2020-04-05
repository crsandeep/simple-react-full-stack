import * as ActionTypes from '../actionTypes/Item'
import * as Constants from '../constants/Item';

const initialState = {
  formMode: Constants.FORM_READONLY_MODE,
  pageLoading: false,
  validating: true,
  itemList: [],
  editStatus: { isSuccess: null, data: null, message: null, operation:null },

  //form field
  itemId: null,
  name: '',
  colorCode: '',
  imgFile: null,
  imgPath: null,
  tags:null,
  description: null,
  category: '',
  reminderDtm: null
};
 
export default function Item (state = initialState, action) {
  switch (action.type) {
    case ActionTypes.GET_ITEM_LIST:
      return {
          ...state,
          pageLoading: false, 
          itemList: action.data
        }
    case ActionTypes.GET_ITEM:
      return { ...state, 
        formMode: Constants.FORM_EDIT_MODE, //set form to edit
        pageLoading: false, 
        itemId: action.data.itemId,
        name: action.data.name,
        colorCode: action.data.colorCode,
        imgFile: null,
        imgPath: action.data.imgPath,
        tags: action.data.tags,
        description: action.data.description,
        category: action.data.category,
        reminderDtm: action.data.reminderDtm,
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
    case ActionTypes.COMPLETE_REMOVE_ITEM_IMG:
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
    case ActionTypes.FAIL_REMOVE_ITEM_IMG:
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
          itemId: null,
          name: '',
          colorCode: '',
          imgFile: null,
          imgPath:null,
          tags:null,
          description: null,
          category: '',
          reminderDtm: null,
      }

    default:
      return state
  }
}
