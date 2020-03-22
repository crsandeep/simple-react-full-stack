import * as ActionTypes from '../../src/client/actionTypes/Item';
import * as Actions from '../../src/client/actions/Item';
import * as Constants from '../../src/client/constants/Item';

const spaceId = 10;
const itemId = 99;
const name = 'Test Name';
const operation = Constants.OPERATION_SAVE;
const message ='Test Messsage';
const mode = Constants.FORM_EDIT_MODE;

describe('Test Actions', () => {
  let expectedAction = null;
  const item = {itemId:itemId, name:name};
  const fileMap = {file:'test'};
  const data = [{item:item}];

    it('Should create action to Saga to Get Item List',()=>{
      expectedAction= {
        type: ActionTypes.SAGA_GET_ITEM_LIST,
        spaceId: spaceId,
      };
      expect(Actions.sagaGetItemList(spaceId)).toEqual(expectedAction);
    });

    it('Should create action to Saga to Get Item',()=>{
      expectedAction= {
        type: ActionTypes.SAGA_GET_ITEM,
        itemId: itemId,
      };
      expect(Actions.sagaGetItem(itemId)).toEqual(expectedAction);
    });

    it('Should create action to Saga to Add Item',()=>{
      expectedAction= {
        type: ActionTypes.SAGA_ADD_ITEM,
        item: item,
        fileMap: fileMap
      };
      expect(Actions.sagaAddItem(item,fileMap)).toEqual(expectedAction);
    });

    it('Should create action to Saga to Update Item',()=>{
      expectedAction= {
        type: ActionTypes.SAGA_UPDATE_ITEM,
        item: item,
        fileMap: fileMap
      };
      expect(Actions.sagaUpdateItem(item,fileMap)).toEqual(expectedAction);
    });

    it('Should create action to Saga to Remove Item Image',()=>{
      expectedAction= {
        type: ActionTypes.SAGA_REMOVE_ITEM_IMG,
        itemId: itemId,
      };
      expect(Actions.sagaRemoveItemImg(itemId)).toEqual(expectedAction);

    });

    it('Should create action to Saga to Delete Item',()=>{
      expectedAction= {
        type: ActionTypes.SAGA_DELETE_ITEM,
        spaceId: spaceId,
        itemId: itemId,
      };
      expect(Actions.sagaDeleteItem(spaceId, itemId)).toEqual(expectedAction);
    });

    it('Should create action to Start loading spinner',()=>{
      expectedAction= {
        type: ActionTypes.PAGE_LOADING
      };
      expect(Actions.startLoading()).toEqual(expectedAction);
    });

    it('Should create action to get Item List',()=>{
      expectedAction= {
        type: ActionTypes.GET_ITEM_LIST,
        data: data
      };
      expect(Actions.getItemList(data)).toEqual(expectedAction);
    });

    it('Should create action to get Item',()=>{
      expectedAction= {
        type: ActionTypes.GET_ITEM,
        data: data
      };
      expect(Actions.getItem(data)).toEqual(expectedAction);
    });

    it('Should create action to complete edit Item',()=>{
      expectedAction= {
        type: ActionTypes.COMPLETE_EDIT,
        data: data,
        operation:operation
      };
      expect(Actions.completeEdit(data, operation)).toEqual(expectedAction);

    });

    it('Should create action to fail edit Item',()=>{
      expectedAction= {
        type: ActionTypes.FAIL_EDIT,
        message: message,
        operation:operation
      };
      expect(Actions.failEdit(message, operation)).toEqual(expectedAction);

    });

    it('Should create action to update form mode',()=>{
      expectedAction= {
        type: ActionTypes.UPDATE_FORM_MODE,
        mode: mode,
      };
      expect(Actions.updateFormMode(mode)).toEqual(expectedAction);

    });

    it('Should create action to completet remove Item Image',()=>{
      expectedAction= {
        type: ActionTypes.COMPLETE_REMOVE_ITEM_IMG,
      };
      expect(Actions.completeRemoveItemImg()).toEqual(expectedAction);

    });

    it('Should create action to fail remove Item Image',()=>{
      expectedAction= {
        type: ActionTypes.FAIL_REMOVE_ITEM_IMG,
      };
      expect(Actions.failRemoveItemImg()).toEqual(expectedAction);
    })
});
