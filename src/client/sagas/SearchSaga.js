import { put, call, takeEvery } from 'redux-saga/effects';
import * as Service from '../services/Search';
import * as Actions from '../actions/Search';
import * as ActionTypes from '../actionTypes/Search';
import * as Constants from '../constants/Search';

export function* handleSearchItem({ values }) {
  try {
    yield put(Actions.startLoading());
    const operResult = yield call(Service.searchItem, values);
    if (operResult.isSuccess) {
      yield put(Actions.searchItem(operResult.payload, Constants.OPERATION_SEARCH));
    } else {
      yield put(Actions.searchItem(null, Constants.OPERATION_SEARCH));
    }
  } catch (error) {
    yield put(Actions.searchItem(null, Constants.OPERATION_SEARCH));
  }
}

export function* watchSearchItem() {
  yield takeEvery(ActionTypes.SAGA_SEARCH_ITEM, handleSearchItem);
}

export default {
  watchSearchItem
};
