import { Sequelize } from 'sequelize-typescript';
import Item from '../models/Item';
import Space from '../models/Space';
import User from '../models/User';
import Grid from '../models/Grid';
import SeqConfig from '../config/sequelize-config.json';

const env = process.env.NODE_ENV || 'development';
const dbConfig = SeqConfig[env];

const sequelize:Sequelize = new Sequelize(dbConfig);

sequelize.addModels([Item, Space, User, Grid]);

export default sequelize;
