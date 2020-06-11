import * as ActionTypes from '../actionTypes/Auth';

export const startLoading = () => ({
  type: ActionTypes.PAGE_LOADING
});

export const sagaRegister = values => ({
  type: ActionTypes.SAGA_REGISTER,
  values
});

export const registerSuccess = (operResult, operationCd) => ({
  type: ActionTypes.REGISTER_COMPLETE,
  operResult,
  operationCd
});

export const registerFail = (operResult, operationCd) => ({
  type: ActionTypes.REGISTER_FAIL,
  operResult,
  operationCd
});


export const sagaLogin = values => ({
  type: ActionTypes.SAGA_LOGIN,
  values
});

export const loginSuccess = (operResult, operationCd) => ({
  type: ActionTypes.LOGIN_COMPLETE,
  operResult,
  operationCd
});

export const loginFail = (operResult, operationCd) => ({
  type: ActionTypes.LOGIN_FAIL,
  operResult,
  operationCd
});
