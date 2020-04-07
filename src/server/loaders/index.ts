import expressLoader from './express';
import dependencyInjectorLoader from './dependencyInjector';
import mongooseLoader from './mongoose';
import { Container } from 'typedi';
import Logger from './logger';
import sequelize from './sequelize';

export default async ({ expressApp }) => {
  
  await sequelize.sync();
  Logger.info('✌️ Postgresql DB loaded and connected!');

  const mongoConnection = await mongooseLoader();
  Logger.info('✌️ DB loaded and connected!'); 
  
  Container.set('logger', Logger)
  Logger.info('✌️ Logger injected into container');

  await dependencyInjectorLoader({
    models: [
      //mongo
      {name: 'userModel',model: require('../models/user').default}, //userModel
      {name: 'itemModel',model: require('../models/item').default}, //itemModel
    ]
  });
  Logger.info('✌️ Dependency Injector loaded');

  await expressLoader({ app: expressApp });
  Logger.info('✌️ Express loaded');
};
