import * as ApiUtil from '../utils/apiUtil';

export async function searchItem(values) {
  let url = ApiUtil.API_ITEM.SEARCH_ITEM + values.keyword;
  url += `/${(values.category.length > 0 ? values.category : 'NULL')}`;
  url += `/${(values.colorCode.length > 0 ? values.colorCode : 'NULL')}`;
  url += `/${(values.location.length > 0 ? values.location : 'NULL')}`;
  url += `/${(values.tags.length > 0 ? values.tags : 'NULL')}`;

  const result = await ApiUtil.invokeApi(
    ApiUtil.API_INVOKE_TYPE_GET,
    url,
    values,
    null
  );
  return result;
}
