import { combineReducers } from 'redux';
import Item from './Item';
import Space from './Space';
import Grid from './Grid';

const allReducers = combineReducers({
  Item,
  Space,
  Grid
});

export default allReducers;
