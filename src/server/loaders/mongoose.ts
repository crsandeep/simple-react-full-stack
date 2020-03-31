import mongoose from 'mongoose';
import { Db } from 'mongodb';
import config from '../config';
import { Container } from 'typedi';
import LoggerInstance from './logger';
import AutoIncrementFactory from 'mongoose-sequence';

export default async (): Promise<Db> => {
  const connection = await mongoose.connect(config.databaseURL, { useNewUrlParser: true, useCreateIndex: true });
  Container.set('mongooseConn', connection.connection);
  LoggerInstance.info('✌️ mongooseConn injected into container');
  
  const AutoIncrement = require('mongoose-sequence')(mongoose);
  Container.set('autoIncrement', AutoIncrement);
  LoggerInstance.info('✌️ autoIncrement injected into container');
  return connection.connection.db;
};
