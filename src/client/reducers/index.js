import { combineReducers } from 'redux';
import Item from './Item';
import Space from './Space';
import Grid from './Grid';
import Search from './Search';

const allReducers = combineReducers({
  Item,
  Space,
  Grid,
  Search
});

export default allReducers;
