import * as ApiUtil from '../utils/apiUtil';


export async function getGridList(spaceId) {
  const result = await ApiUtil.invokeApi(
    ApiUtil.API_INVOKE_TYPE_GET,
    ApiUtil.API_GRID.GET_GRID_LIST_BY_SPACE_ID + spaceId,
    null
  );
  return result;
}

export async function saveGrids(grids) {
  const result = await ApiUtil.invokeApi(
    ApiUtil.API_INVOKE_TYPE_POST,
    ApiUtil.API_GRID.SAVE_GRIDS,
    grids
  );
  return result;
}

export async function deleteGrid(gridId) {
  const result = await ApiUtil.invokeApi(
    ApiUtil.API_INVOKE_TYPE_DELETE,
    ApiUtil.API_GRID.DELETE_GRID + gridId,
    null
  );
  return result;
}
