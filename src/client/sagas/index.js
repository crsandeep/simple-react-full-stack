import { all, fork } from 'redux-saga/effects';
import itemSaga from './ItemSaga';
import spaceSaga from './SpaceSaga';
import gridSaga from './GridSaga';
import searchSaga from './SearchSaga';

export default function* rootSaga() {
  yield all([
    ...Object.values(itemSaga),
    ...Object.values(spaceSaga),
    ...Object.values(gridSaga),
    ...Object.values(searchSaga)
  ].map(fork));
}
