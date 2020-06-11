import { put, call, takeEvery } from 'redux-saga/effects';
import * as Service from '../services/Auth';
import * as Actions from '../actions/Auth';
import * as ActionTypes from '../actionTypes/Auth';
import * as Constants from '../constants/Auth';
import * as MessageCd from '../constants/MessageCd';
import OperationResult from '../utils/operationResult';

export function* handleRegister({ values }) {
  try {
    yield put(Actions.startLoading());
    const operResult = yield call(Service.register, values);
    if (operResult.isSuccess) {
      yield put(Actions.registerSuccess(operResult, Constants.OPERATION_REGISTER));
    } else {
      yield put(Actions.registerFail(operResult, Constants.OPERATION_REGISTER));
    }
  } catch (error) {
    yield put(Actions.registerFail(MessageCd.GLOBAL_UNKNOWN_ERROR, error.message, Constants.OPERATION_REGISTER));
  }
}

export function* watchRegister() {
  yield takeEvery(ActionTypes.SAGA_REGISTER, handleRegister);
}


export function* handleLogin({ values }) {
  try {
    yield put(Actions.startLoading());
    const operResult = yield call(Service.login, values);
    if (operResult.isSuccess) {
      yield put(Actions.loginSuccess(operResult, Constants.OPERATION_LOGIN));
    } else {
      yield put(Actions.loginFail(operResult, Constants.OPERATION_LOGIN));
    }
  } catch (error) {
    const operResult = new OperationResult();
    operResult.setFail(MessageCd.GLOBAL_UNKNOWN_ERROR, error.message);
    yield put(Actions.loginFail(operResult, Constants.OPERATION_LOGIN));
  }
}

export function* watchLogin() {
  yield takeEvery(ActionTypes.SAGA_LOGIN, handleLogin);
}


export default {
  watchRegister,
  watchLogin
};
