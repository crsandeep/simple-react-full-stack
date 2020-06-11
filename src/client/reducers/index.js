import { combineReducers } from 'redux';
import Item from './Item';
import Space from './Space';
import Grid from './Grid';
import Search from './Search';
import Auth from './Auth';

const allReducers = combineReducers({
  Item,
  Space,
  Grid,
  Search,
  Auth
});

export default allReducers;
