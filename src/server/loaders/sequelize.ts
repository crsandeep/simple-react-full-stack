import {Sequelize} from 'sequelize-typescript';
import Item from '../models/Item';
import Space from '../models/Space';
import User from '../models/User';

let env = process.env.NODE_ENV || 'development';
//load config from json
let dbConfig = require('../config/sequelize-config.json')[env];

const sequelize:Sequelize =  new Sequelize(dbConfig);

sequelize.addModels([Item,Space,User]);

export default sequelize;
 