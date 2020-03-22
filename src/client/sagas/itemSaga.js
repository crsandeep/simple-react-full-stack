import { put, call, takeEvery} from 'redux-saga/effects';
import * as Service from '../services/Item';
import * as Actions from '../actions/Item';
import * as ActionTypes from '../actionTypes/Item';
import * as Constants from '../constants/Item';

export function* handleGetItemList({spaceId}) {
    try {
        yield put(Actions.startLoading());
        const operResult = yield call(Service.getItemList, spaceId);
        if(operResult.isSuccess){
            yield put(Actions.getItemList(operResult.data));
        }else{
            yield put(Actions.getItemList(null));
        }
    } catch (error) {
        yield put(Actions.getItemList(null));
    }
}

export function* handleGetItem({itemId}) {
    try {
        yield put(Actions.startLoading());
        const operResult = yield call(Service.getItem, itemId);
        if(operResult.isSuccess){
            yield put(Actions.getItem(operResult.data));
        }else{
            yield put(Actions.getItem(null));
        }
    } catch (error) {
        yield put(Actions.getItem(null));
    }
}

export function* handleDeleteItem({spaceId, itemId}) {
    try {
        yield put(Actions.startLoading());
        const operResult = yield call(Service.deleteItem, itemId);
        if(operResult.isSuccess){
            yield put(Actions.completeEdit(operResult.data, Constants.OPERATION_DELETE));

            //trigger reload list
            yield call(handleGetItemList,{spaceId});
        }else{
            yield put(Actions.failEdit(operResult.message, Constants.OPERATION_DELETE));
        }

    } catch (error) {
        yield put(Actions.failEdit(error.message, Constants.OPERATION_DELETE));
    }
}

export function* handleAddItem({item ,fileMap}) {
    try {
        yield put(Actions.startLoading());
        const operResult = yield call(Service.addItem, item, fileMap);
        const spaceId = item.spaceId;
        if(operResult.isSuccess){
            yield put(Actions.completeEdit(operResult.data, Constants.OPERATION_SAVE));

            //trigger reload list
            yield call(handleGetItemList,{spaceId});
        }else{
            yield put(Actions.failEdit(operResult.message, Constants.OPERATION_SAVE));
        }

    } catch (error) {
        yield put(Actions.failEdit(error.message, Constants.OPERATION_SAVE));
    }
}

export function* handleUpdateItem({item,fileMap}) {
    try {
        yield put(Actions.startLoading());
        const operResult = yield call(Service.updateItem, item,fileMap);
        const spaceId = item.spaceId;
        if(operResult.isSuccess){
            yield put(Actions.completeEdit(operResult.data, Constants.OPERATION_UPDATE));

            //trigger reload list
            yield call(handleGetItemList,{spaceId});
        }else{
            yield put(Actions.failEdit(operResult.message, Constants.OPERATION_UPDATE));
        }

    } catch (error) {
        yield put(Actions.failEdit(error.message, Constants.OPERATION_UPDATE));
    }
}


export function* handleRemoveItemImg({itemId}) {
    try {
        yield put(Actions.startLoading());
        const operResult = yield call(Service.removeItemImg, itemId);
        if(operResult.isSuccess){
            yield put(Actions.completeRemoveItemImg(operResult.data));
        }else{
            yield put(Actions.failRemoveItemImg(operResult.message));
        }
    } catch (error) {
        yield put(Actions.failRemoveItemImg(error.message));
    }
}


export function* watchGetItemList() {
    yield takeEvery(ActionTypes.SAGA_GET_ITEM_LIST, handleGetItemList);
}

export function* watchGetItem() {
    yield takeEvery(ActionTypes.SAGA_GET_ITEM, handleGetItem);
}

export function* watchAddItem() {
    yield takeEvery(ActionTypes.SAGA_ADD_ITEM, handleAddItem);
}

export function* watchUpdateItem() {
    yield takeEvery(ActionTypes.SAGA_UPDATE_ITEM, handleUpdateItem);
}

export function* watchDeleteItem() {
    yield takeEvery(ActionTypes.SAGA_DELETE_ITEM, handleDeleteItem);
}

export function* watchRemoveItemImg() {
    yield takeEvery(ActionTypes.SAGA_REMOVE_ITEM_IMG, handleRemoveItemImg);
}
