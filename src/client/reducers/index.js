import { combineReducers } from 'redux'
import Item from './Item'
import Space from './Space'

const allReducers = combineReducers({
    Item,
    Space
})

export default allReducers