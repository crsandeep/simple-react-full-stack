import * as ApiUtil from '../utils/apiUtil';

export async function register(values) {
  const result = await ApiUtil.invokeApi(
    ApiUtil.API_INVOKE_TYPE_POST,
    ApiUtil.API_AUTH.REGISTER,
    values
  );
  return result;
}


export async function login(values) {
  const result = await ApiUtil.invokeApi(
    ApiUtil.API_INVOKE_TYPE_POST,
    ApiUtil.API_AUTH.LOGIN,
    values,
    null
  );
  return result;
}
