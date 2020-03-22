import { runSaga } from 'redux-saga';
import { takeEvery } from 'redux-saga/effects';
import * as ActionTypes from '../../src/client/actionTypes/Item';
import * as Actions from '../../src/client/actions/Item';
import * as Constants from '../../src/client/constants/Item';
import * as Saga from '../../src/client/sagas/itemSaga';
import * as Service from '../../src/client/services/Item';

const spaceId = 10;
const itemId = 99;
const message ='Test Messsage';


describe('Test get item list', () => {
  //fixed para
  const sagaWatcherFn = Saga.watchGetItemList;  //watcher
  const sagaWatcherActionType = ActionTypes.SAGA_GET_ITEM_LIST;   //watcher
  const sagaFn = Saga.handleGetItemList;  //saga
  const serviceFnName = 'getItemList';    //service
  const data = {itemId:itemId};
  const inputItem = spaceId;

  //temp para for each test
  let disActionsArr = null;
  let spyFn = null;

  async function runSagaHelper(){
    return await runSaga(
      {
        dispatch: (action) => disActionsArr.push(action)  //dispatch action
      },
      sagaFn, //Saga Fn Name
      inputItem,   //input para
    );
  };

  beforeEach(()=>{
    disActionsArr = [];
    spyFn = jest.spyOn(Service, serviceFnName);  //update item
  });

  afterEach(()=>{
    spyFn.mockClear();
  });

  //start testing
  it('should wait for every get item list and invoke further call', () => {
    const watcher = sagaWatcherFn();
    expect(watcher.next().value).toEqual(takeEvery(sagaWatcherActionType, sagaFn));
    expect(watcher.next().done).toBeTruthy();
  });

  it('Should handle get Item list (Success)', async ()=>{
    const operResult = { isSuccess:true, data: data}; //success
    const expectDisActionsArr = [
      Actions.startLoading(),
      Actions.getItemList(operResult.data),
    ];
    
    //stub actions
    spyFn.mockImplementation(() => Promise.resolve(operResult));
    await runSagaHelper();

    expect(spyFn).toHaveBeenCalledTimes(1);
    expect(disActionsArr).toEqual(expectDisActionsArr);
  })

  it('Should handle get Item list (Fail)', async ()=>{
    const operResult = { isSuccess:false, data:null, message: message};//fail
    const expectDisActionsArr = [
      Actions.startLoading(),
      Actions.getItemList(operResult.data),
    ];
    
    //stub actions
    spyFn.mockImplementation(() => Promise.resolve(operResult));
    await runSagaHelper();

    expect(spyFn).toHaveBeenCalledTimes(1);
    expect(disActionsArr).toEqual(expectDisActionsArr);
  })

  it('Should handle get Item list(Exception)', async ()=>{
    const error = {message:message} //error
    const expectDisActionsArr = [
      Actions.startLoading(),
      Actions.getItemList(null),
    ];

    //prepare stub actions
    spyFn.mockImplementation(() => Promise.reject(error));  //error
    await runSagaHelper();

    expect(spyFn).toHaveBeenCalledTimes(1);
    expect(disActionsArr).toEqual(expectDisActionsArr);
  })
});

describe('Test get item', () => {
  //fixed para
  const sagaWatcherFn = Saga.watchGetItem;  //watcher
  const sagaWatcherActionType = ActionTypes.SAGA_GET_ITEM;   //watcher
  const sagaFn = Saga.handleGetItem;  //saga
  const serviceFnName = 'getItem';    //service
  const data = {itemId:itemId};
  const inputItem = itemId;

  //temp para for each test
  let disActionsArr = null;
  let spyFn = null;

  async function runSagaHelper(){
    return await runSaga(
      {
        dispatch: (action) => disActionsArr.push(action)  //dispatch action
      },
      sagaFn, //Saga Fn Name
      inputItem,   //input para
    );
  };

  beforeEach(()=>{
    disActionsArr = [];
    spyFn = jest.spyOn(Service, serviceFnName);  //update item
  });

  afterEach(()=>{
    spyFn.mockClear();
  });

  //start testing
  it('should wait for every get item and invoke further call', () => {
    const watcher = sagaWatcherFn();
    expect(watcher.next().value).toEqual(takeEvery(sagaWatcherActionType, sagaFn));
    expect(watcher.next().done).toBeTruthy();
  });

  it('Should handle get Item (Success)', async ()=>{
    const operResult = { isSuccess:true, data: data}; //success
    const expectDisActionsArr = [
      Actions.startLoading(),
      Actions.getItem(operResult.data),
    ];
    
    //stub actions
    spyFn.mockImplementation(() => Promise.resolve(operResult));
    await runSagaHelper();

    expect(spyFn).toHaveBeenCalledTimes(1);
    expect(disActionsArr).toEqual(expectDisActionsArr);
  })

  it('Should handle get Item (Fail)', async ()=>{
    const operResult = { isSuccess:false, data:null, message: message};//fail
    const expectDisActionsArr = [
      Actions.startLoading(),
      Actions.getItem(operResult.data),
    ];
    
    //stub actions
    spyFn.mockImplementation(() => Promise.resolve(operResult));
    await runSagaHelper();

    expect(spyFn).toHaveBeenCalledTimes(1);
    expect(disActionsArr).toEqual(expectDisActionsArr);
  })

  it('Should handle get Item (Exception)', async ()=>{
    const error = {message:message} //error
    const expectDisActionsArr = [
      Actions.startLoading(),
      Actions.getItem(null),
    ];

    //prepare stub actions
    spyFn.mockImplementation(() => Promise.reject(error));  //error
    await runSagaHelper();

    expect(spyFn).toHaveBeenCalledTimes(1);
    expect(disActionsArr).toEqual(expectDisActionsArr);
  })
});

describe('Test update item', () => {
  //fixed para
  const sagaWatcherFn = Saga.watchUpdateItem;
  const sagaWatcherActionType = ActionTypes.SAGA_UPDATE_ITEM; 
  const sagaFn = Saga.handleUpdateItem;  //saga
  const servicefnName = 'updateItem';    //service
  const constantsFnUpdate = Constants.OPERATION_UPDATE; //edit mode
  const data = {itemId:itemId, spaceId:spaceId};
  const inputItem = {item: data};
  const inputFileMap = null;

  //temp para for each test
  let disActionsArr = null;
  let spyFn = null;

  async function runSagaHelper(){
    return await runSaga(
      {
        dispatch: (action) => disActionsArr.push(action)  //dispatch action
      },
      sagaFn, //Saga Fn Name
      inputItem,   //input para
      inputFileMap //input para
    );
  };

  beforeEach(()=>{
    disActionsArr = [];
    spyFn = jest.spyOn(Service, servicefnName);  //update item
  });

  afterEach(()=>{
    spyFn.mockClear();
  });

  //start testing
  it('should wait for every update item action and call handleUpdateItem', () => {
    const watcher = sagaWatcherFn();
    expect(watcher.next().value).toEqual(takeEvery(sagaWatcherActionType, sagaFn));
    expect(watcher.next().done).toBeTruthy();
  });

  it('Should handle update Item (Success)', async ()=>{
    const operResult = { isSuccess:true, data: data}; //success
    const expectDisActionsArr = [
      Actions.startLoading(),
      Actions.completeEdit(operResult.data,constantsFnUpdate),
      Actions.startLoading(), //todo: remove and add detection for further reload
      Actions.getItemList(null) //todo: remove and add detection for further reload
    ];
    
    //stub actions
    spyFn.mockImplementation(() => Promise.resolve(operResult));
    await runSagaHelper();

    expect(spyFn).toHaveBeenCalledTimes(1);
    expect(disActionsArr).toEqual(expectDisActionsArr);
  })

  it('Should handle update Item (Fail)', async ()=>{
    const operResult = { isSuccess:false, message: message};//fail
    const expectDisActionsArr = [
      Actions.startLoading(),
      Actions.failEdit(operResult.message,constantsFnUpdate),
    ];
    
    //stub actions
    spyFn.mockImplementation(() => Promise.resolve(operResult));
    await runSagaHelper();

    expect(spyFn).toHaveBeenCalledTimes(1);
    expect(disActionsArr).toEqual(expectDisActionsArr);
  })

  it('Should handle update Item (Exception)', async ()=>{
    const error = {message:message} //error
    const expectDisActionsArr = [
      Actions.startLoading(),
      Actions.failEdit(error.message,constantsFnUpdate),
    ];

    //prepare stub actions
    spyFn.mockImplementation(() => Promise.reject(error));  //error
    await runSagaHelper();

    expect(spyFn).toHaveBeenCalledTimes(1);
    expect(disActionsArr).toEqual(expectDisActionsArr);
  })
});

describe('Test handle remove item image', () => {
  //fixed para
  const sagaWatcherFn = Saga.watchRemoveItemImg;  //saga
  const sagaWatcherActionType = ActionTypes.SAGA_REMOVE_ITEM_IMG; 
  const sagaFn = Saga.handleRemoveItemImg;  //saga
  const data = null;
  const serviceFnName = 'removeItemImg';    //service
  const inputItemId = itemId;

  //temp para for each test
  let disActionsArr = null;
  let spyFn = null;

  async function runSagaHelper(){
    return await runSaga(
      {
        dispatch: (action) => disActionsArr.push(action)  //dispatch action
      },
      sagaFn, //Saga Fn Name
      inputItemId,   //input para
    );
  };

  beforeEach(()=>{
    disActionsArr = [];
    spyFn = jest.spyOn(Service, serviceFnName);  //create spy func
  });

  afterEach(()=>{
    spyFn.mockClear();
  });

  //start testing
  it('should wait for every remove item image action and call handleRemoveItemImg', () => {
    const watcher = sagaWatcherFn();
    expect(watcher.next().value).toEqual(takeEvery(sagaWatcherActionType, sagaFn));
    expect(watcher.next().done).toBeTruthy();
  });

  it('Should handle remove Item image (Success)', async ()=>{
    const operResult = { isSuccess:true, data: data}; //success
    const expectDisActionsArr = [
      Actions.startLoading(),
      Actions.completeRemoveItemImg(operResult.data),
    ];
    
    //stub actions
    spyFn.mockImplementation(() => Promise.resolve(operResult));
    await runSagaHelper();

    expect(spyFn).toHaveBeenCalledTimes(1);
    expect(disActionsArr).toEqual(expectDisActionsArr);
  })

  it('Should handle remove Item image (Fail)', async ()=>{
    const operResult = { isSuccess:false, message: message};//fail
    const expectDisActionsArr = [
      Actions.startLoading(),
      Actions.failRemoveItemImg(operResult.message),
    ];
    
    //stub actions
    spyFn.mockImplementation(() => Promise.resolve(operResult));
    await runSagaHelper();

    expect(spyFn).toHaveBeenCalledTimes(1);
    expect(disActionsArr).toEqual(expectDisActionsArr);
  })

  it('Should handle update Item image (Exception)', async ()=>{
    const error = {message:message} //error
    const expectDisActionsArr = [
      Actions.startLoading(),
      Actions.failRemoveItemImg(error.message),
    ];

    //prepare stub actions
    spyFn.mockImplementation(() => Promise.reject(error));  //error
    await runSagaHelper();

    expect(spyFn).toHaveBeenCalledTimes(1);
    expect(disActionsArr).toEqual(expectDisActionsArr);
  })
});

describe('Test delete item', () => {
  //fixed para
  const sagaWatcherFn = Saga.watchDeleteItem;  //watcher
  const sagaWatcherActionType = ActionTypes.SAGA_DELETE_ITEM;   //watcher
  const sagaFn = Saga.handleDeleteItem;  //saga
  const serviceFnName = 'deleteItem';    //service
  const constantsFnDelete = Constants.OPERATION_DELETE; //edit mode
  const data = {itemId:itemId};
  const inputItem = itemId;

  //temp para for each test
  let disActionsArr = null;
  let spyFn = null;

  async function runSagaHelper(){
    return await runSaga(
      {
        dispatch: (action) => disActionsArr.push(action)  //dispatch action
      },
      sagaFn, //Saga Fn Name
      inputItem,   //input para
    );
  };

  beforeEach(()=>{
    disActionsArr = [];
    spyFn = jest.spyOn(Service, serviceFnName);  //update item
  });

  afterEach(()=>{
    spyFn.mockClear();
  });

  //start testing
  it('should wait for every delete item and invoke further call', () => {
    const watcher = sagaWatcherFn();
    expect(watcher.next().value).toEqual(takeEvery(sagaWatcherActionType, sagaFn));
    expect(watcher.next().done).toBeTruthy();
  });

  it('Should handle delete Item (Success)', async ()=>{
    const operResult = { isSuccess:true, data: data}; //success
    const expectDisActionsArr = [
      Actions.startLoading(),
      Actions.completeEdit(operResult.data,constantsFnDelete),
      Actions.startLoading(), //todo: remove and add detection for further reload
      Actions.getItemList(null) //todo: remove and add detection for further reload
    ];
    
    //stub actions
    spyFn.mockImplementation(() => Promise.resolve(operResult));
    await runSagaHelper();

    expect(spyFn).toHaveBeenCalledTimes(1);
    expect(disActionsArr).toEqual(expectDisActionsArr);
  })

  it('Should handle delete Item (Fail)', async ()=>{
    const operResult = { isSuccess:false, data:null, message: message};//fail
    const expectDisActionsArr = [
      Actions.startLoading(),
      Actions.failEdit(operResult.message,constantsFnDelete),
    ];
    
    //stub actions
    spyFn.mockImplementation(() => Promise.resolve(operResult));
    await runSagaHelper();

    expect(spyFn).toHaveBeenCalledTimes(1);
    expect(disActionsArr).toEqual(expectDisActionsArr);
  })

  it('Should handle delete Item (Exception)', async ()=>{
    const error = {message:message} //error
    const expectDisActionsArr = [
      Actions.startLoading(),
      Actions.failEdit(error.message,constantsFnDelete),
    ];

    //prepare stub actions
    spyFn.mockImplementation(() => Promise.reject(error));  //error
    await runSagaHelper();

    expect(spyFn).toHaveBeenCalledTimes(1);
    expect(disActionsArr).toEqual(expectDisActionsArr);
  })
});


//---------------


describe('Test add item', () => {
  //fixed para
  const sagaWatcherFn = Saga.watchAddItem;  //watcher
  const sagaWatcherActionType = ActionTypes.SAGA_ADD_ITEM;   //watcher
  const sagaFn = Saga.handleAddItem;  //saga
  const serviceFnName = 'addItem';    //service
  const constantsFnSave = Constants.OPERATION_SAVE; //edit mode
  const data = {itemId:itemId, spaceId:spaceId};
  const inputItem = {item:data};

  //temp para for each test
  let disActionsArr = null;
  let spyFn = null;

  async function runSagaHelper(){
    return await runSaga(
      {
        dispatch: (action) => disActionsArr.push(action)  //dispatch action
      },
      sagaFn, //Saga Fn Name
      inputItem,   //input para
    );
  };

  beforeEach(()=>{
    disActionsArr = [];
    spyFn = jest.spyOn(Service, serviceFnName);  //update item
  });

  afterEach(()=>{
    spyFn.mockClear();
  });

  //start testing
  it('should wait for every add item and invoke further call', () => {
    const watcher = sagaWatcherFn();
    expect(watcher.next().value).toEqual(takeEvery(sagaWatcherActionType, sagaFn));
    expect(watcher.next().done).toBeTruthy();
  });

  it('Should handle add Item (Success)', async ()=>{
    const operResult = { isSuccess:true, data: data}; //success
    const expectDisActionsArr = [
      Actions.startLoading(),
      Actions.completeEdit(operResult.data,constantsFnSave),
      Actions.startLoading(), //todo: remove and add detection for further reload
      Actions.getItemList(null) //todo: remove and add detection for further reload
    ];
    
    //stub actions
    spyFn.mockImplementation(() => Promise.resolve(operResult));
    await runSagaHelper();

    expect(spyFn).toHaveBeenCalledTimes(1);
    expect(disActionsArr).toEqual(expectDisActionsArr);
  })

  it('Should handle add Item (Fail)', async ()=>{
    const operResult = { isSuccess:false, data:null, message: message};//fail
    const expectDisActionsArr = [
      Actions.startLoading(),
      Actions.failEdit(operResult.message,constantsFnSave),
    ];
    
    //stub actions
    spyFn.mockImplementation(() => Promise.resolve(operResult));
    await runSagaHelper();

    expect(spyFn).toHaveBeenCalledTimes(1);
    expect(disActionsArr).toEqual(expectDisActionsArr);
  })

  it('Should handle add Item (Exception)', async ()=>{
    const error = {message:message} //error
    const expectDisActionsArr = [
      Actions.startLoading(),
      Actions.failEdit(error.message,constantsFnSave),
    ];

    //prepare stub actions
    spyFn.mockImplementation(() => Promise.reject(error));  //error
    await runSagaHelper();

    expect(spyFn).toHaveBeenCalledTimes(1);
    expect(disActionsArr).toEqual(expectDisActionsArr);
  })
});