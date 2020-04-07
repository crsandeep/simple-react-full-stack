import expressLoader from './express';
import dependencyInjectorLoader from './dependencyInjector';
import mongooseLoader from './mongoose';
import Logger from './logger';

import sequelize from '../models-seq/';

export default async ({ expressApp }) => {
  
  await sequelize.sync();
  Logger.info('✌️ Postgresql DB loaded and connected!');

  const mongoConnection = await mongooseLoader();
  Logger.info('✌️ DB loaded and connected!'); 
  
  await dependencyInjectorLoader({
    models: [
      {name: 'userModel',model: require('../models/user').default}, //userModel
      {name: 'itemModel',model: require('../models/item').default}, //itemModel
    ]
  });
  Logger.info('✌️ Dependency Injector loaded');

  await expressLoader({ app: expressApp });
  Logger.info('✌️ Express loaded');
};
