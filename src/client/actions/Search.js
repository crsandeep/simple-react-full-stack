import * as ActionTypes from '../actionTypes/Search';


export const sagaSearchItem = values => ({
  type: ActionTypes.SAGA_SEARCH_ITEM,
  values
});

export const startLoading = () => ({
  type: ActionTypes.PAGE_LOADING
});

export const searchItem = (data, operation) => ({
  type: ActionTypes.SEARCH_ITEM,
  data,
  operation
});
