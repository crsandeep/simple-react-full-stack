import { all, fork } from 'redux-saga/effects';
import itemSaga from './itemSaga';
import spaceSaga from './spaceSaga';

export default function* rootSaga() {
    yield all([
        ...Object.values(itemSaga),
        ...Object.values(spaceSaga)
    ].map(fork));
}