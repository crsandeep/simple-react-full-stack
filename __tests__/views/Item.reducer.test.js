import * as ActionTypes from '../../src/client/actionTypes/Item';
import * as Constants from '../../src/client/constants/Item';
import Reducer from '../../src/client/reducers/Item';

const itemId = 99;
const name = 'Test Name';
const operation = Constants.OPERATION_SAVE;
const message ='Test Messsage';
const mode = Constants.FORM_EDIT_MODE;
const colorCode = 'Test Yellow';
const tags= 'Test Winter';
const description = 'Test description';
const category = 'Test Bedroom 1';
const reminderDtm = new Date();

describe('Test Reducers', () => {
  const item = {
      itemId: itemId,
      name: name,
      colorCode: colorCode,
      imageUrl: null,
      imgFile: null,
      imgDisplayUrl: null,
      tags: tags,
      description: description,
      category: category,
      reminderDtm: reminderDtm,
  };
  const data = item;
  const initialValues = {
    formMode: Constants.FORM_READONLY_MODE,
    pageLoading: false,
    validating: true,
    itemList: [],
    editStatus: { isSuccess: null, data: null, message: null, operation:null },
    itemId: null,
    name: '',
    colorCode: '',
    imageUrl: '',
    imgFile: null,
    imgDisplayUrl: null,
    tags:'',
    description: '',
    category: '',
    reminderDtm: null
  };

  let expectedValues=null;

    it('Should return the initial state',()=>{
      expect(Reducer(undefined, {})).toEqual(initialValues)
    });

    it('Should handle get item list',()=>{
      expectedValues = {
        pageLoading:false,
        itemList:item
      };

      expect(Reducer([], {
        type: ActionTypes.GET_ITEM_LIST,
        data: item
      })).toEqual(
        expectedValues,
        initialValues
      )
    });

    it('Should handle get item',()=>{
      expectedValues = item;
      expectedValues.pageLoading=false;
      expectedValues.formMode= mode;

      expect(Reducer([], {
        type: ActionTypes.GET_ITEM,
        data: item
      })).toEqual(
        expectedValues,
        initialValues
      )
    });
    

    it('Should handle complete edit item',()=>{
      expectedValues = {
        pageLoading:false,
        formMode: Constants.FORM_READONLY_MODE,
        editStatus: { isSuccess: true, data: data, operation:operation } 
      };

      expect(Reducer([], {
        type: ActionTypes.COMPLETE_EDIT,
        data: data,
        operation: operation
      })).toEqual(
        expectedValues,
        initialValues
      )
    });

    it('Should handle fail edit item',()=>{
      expectedValues = {
        pageLoading:false,
        editStatus: { isSuccess: false, message: message, operation:operation }
      };

      expect(Reducer([], {
        type: ActionTypes.FAIL_EDIT,
        message: message,
        operation: operation
      })).toEqual(
        expectedValues,
        initialValues
      )
    });

    it('Should complete remove item image',()=>{
      expectedValues = {
        pageLoading:false,
        imgDisplayUrl: null,
        imgFile: null,
        editStatus: { isSuccess: true, data: null, message:null, operation:Constants.OPERATION_REMOVE_IMG } 
      };

      expect(Reducer([], {
        type: ActionTypes.COMPLETE_REMOVE_ITEM_IMG,
      })).toEqual(
        expectedValues,
        initialValues
      )
    });

    it('Should fail remove item image',()=>{
      expectedValues = {
        pageLoading:false,
        editStatus: { isSuccess: false, data: null, message:message, operation:Constants.OPERATION_REMOVE_IMG } 
      };

      expect(Reducer([], {
        type: ActionTypes.FAIL_REMOVE_ITEM_IMG,
        message: message,
      })).toEqual(
        expectedValues,
        initialValues
      )
    });

    it('Should handle page loading',()=>{
      expectedValues = {
        pageLoading:true,
      };

      expect(Reducer([], {
        type: ActionTypes.PAGE_LOADING,
      })).toEqual(
        expectedValues,
        initialValues
      )
    });

    it('Should handle update form mode',()=>{
      expectedValues = {
        pageLoading:false,
        formMode: mode,
        itemId: null,
        name: '',
        colorCode: '',
        imageUrl: '',
        imgFile: null,
        imgDisplayUrl:null,
        tags:'',
        description: '',
        category: '',
        reminderDtm: null,
      };

      expect(Reducer([], {
        type: ActionTypes.UPDATE_FORM_MODE,
        mode: mode,
      })).toEqual(
        expectedValues,
        initialValues
      )
    });
  
});



