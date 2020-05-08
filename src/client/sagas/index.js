import { all, fork } from 'redux-saga/effects';
import itemSaga from './itemSaga';
import spaceSaga from './spaceSaga';
import gridSaga from './gridSaga';

export default function* rootSaga() {
  yield all([
    ...Object.values(itemSaga),
    ...Object.values(spaceSaga),
    ...Object.values(gridSaga)
  ].map(fork));
}
