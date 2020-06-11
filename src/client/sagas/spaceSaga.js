import { put, call, takeEvery } from 'redux-saga/effects';
import * as Service from '../services/Space';
import * as Actions from '../actions/Space';
import * as ActionTypes from '../actionTypes/Space';
import * as Constants from '../constants/Space';

export function* handleGetSpaceList({ userId }) {
  try {
    yield put(Actions.startLoading());
    const operResult = yield call(Service.getSpaceList, userId);
    if (operResult.isSuccess) {
      yield put(Actions.getSpaceList(operResult.payload, Constants.OPERATION_GET));
    } else {
      yield put(Actions.getSpaceList(null, Constants.OPERATION_GET));
    }
  } catch (error) {
    yield put(Actions.getSpaceList(null, Constants.OPERATION_GET));
  }
}

export function* handleGetSpace({ spaceId }) {
  try {
    yield put(Actions.startLoading());
    const operResult = yield call(Service.getSpace, spaceId);
    if (operResult.isSuccess) {
      yield put(Actions.getSpace(operResult.payload, Constants.OPERATION_GET));
    } else {
      yield put(Actions.getSpace(null, Constants.OPERATION_GET));
    }
  } catch (error) {
    yield put(Actions.getSpace(null, Constants.OPERATION_GET));
  }
}

export function* handleDeleteSpace({ userId, spaceId }) {
  try {
    yield put(Actions.startLoading());
    const operResult = yield call(Service.deleteSpace, spaceId);
    if (operResult.isSuccess) {
      yield put(Actions.completeEdit(operResult.payload, Constants.OPERATION_DELETE));

      // trigger reload list
      yield call(handleGetSpaceList, { userId });
    } else {
      yield put(Actions.failEdit(operResult.message, Constants.OPERATION_DELETE));
    }
  } catch (error) {
    yield put(Actions.failEdit(error.message, Constants.OPERATION_DELETE));
  }
}

export function* handleAddSpace({ space, fileMap }) {
  try {
    yield put(Actions.startLoading());
    const operResult = yield call(Service.addSpace, space, fileMap);
    const { userId } = space;
    if (operResult.isSuccess) {
      yield put(Actions.completeEdit(operResult.payload, Constants.OPERATION_SAVE));

      // trigger reload list
      yield call(handleGetSpaceList, { userId });
    } else {
      yield put(Actions.failEdit(operResult.message, Constants.OPERATION_SAVE));
    }
  } catch (error) {
    yield put(Actions.failEdit(error.message, Constants.OPERATION_SAVE));
  }
}

export function* handleUpdateSpace({ space, fileMap }) {
  try {
    yield put(Actions.startLoading());
    const operResult = yield call(Service.updateSpace, space, fileMap);
    const { userId } = space;
    if (operResult.isSuccess) {
      yield put(Actions.completeEdit(operResult.payload, Constants.OPERATION_UPDATE));

      // trigger reload list
      yield call(handleGetSpaceList, { userId });
    } else {
      yield put(Actions.failEdit(operResult.message, Constants.OPERATION_UPDATE));
    }
  } catch (error) {
    yield put(Actions.failEdit(error.message, Constants.OPERATION_UPDATE));
  }
}


export function* handleRemoveSpaceImg({ spaceId }) {
  try {
    yield put(Actions.startLoading());
    const operResult = yield call(Service.removeSpaceImg, spaceId);
    if (operResult.isSuccess) {
      yield put(Actions.completeRemoveSpaceImg(operResult.payload, Constants.OPERATION_REMOVE_IMG));
    } else {
      yield put(Actions.failRemoveSpaceImg(operResult.message, Constants.OPERATION_REMOVE_IMG));
    }
  } catch (error) {
    yield put(Actions.failRemoveSpaceImg(error.message, Constants.OPERATION_REMOVE_IMG));
  }
}


export function* watchGetSpaceList() {
  yield takeEvery(ActionTypes.SAGA_GET_SPACE_LIST, handleGetSpaceList);
}

export function* watchGetSpace() {
  yield takeEvery(ActionTypes.SAGA_GET_SPACE, handleGetSpace);
}

export function* watchAddSpace() {
  yield takeEvery(ActionTypes.SAGA_ADD_SPACE, handleAddSpace);
}

export function* watchUpdateSpace() {
  yield takeEvery(ActionTypes.SAGA_UPDATE_SPACE, handleUpdateSpace);
}

export function* watchDeleteSpace() {
  yield takeEvery(ActionTypes.SAGA_DELETE_SPACE, handleDeleteSpace);
}

export function* watchRemoveSpaceImg() {
  yield takeEvery(ActionTypes.SAGA_REMOVE_SPACE_IMG, handleRemoveSpaceImg);
}

export default {
  watchGetSpaceList,
  watchGetSpace,
  watchAddSpace,
  watchUpdateSpace,
  watchDeleteSpace,
  watchRemoveSpaceImg
};
