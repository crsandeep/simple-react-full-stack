import { all, fork } from 'redux-saga/effects';
import itemSaga from './itemSaga';

export default function* rootSaga() {
    yield all([
        ...Object.values(itemSaga)
    ].map(fork));
}