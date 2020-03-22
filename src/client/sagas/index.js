import { all, fork } from 'redux-saga/effects';
import {watchGetItemList,watchGetItem,watchAddItem,watchUpdateItem,watchDeleteItem,watchRemoveItemImg} from './itemSaga';

export default function* rootSaga() {
    yield all([
        watchGetItemList,watchGetItem,watchAddItem,watchUpdateItem,watchDeleteItem,watchRemoveItemImg   //item
    ].map(fork));
}