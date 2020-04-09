import expressLoader from './express';
import { Container } from 'typedi';
import Logger from './logger';
import sequelize from './sequelize';

export default async ({ expressApp }) => {
  
  await sequelize.sync();
  Logger.info('✌️ Postgresql DB loaded and connected!');

  Container.set('logger', Logger)
  Logger.info('✌️ Logger injected into container');

  await expressLoader({ app: expressApp });
  Logger.info('✌️ Express loaded');
};
 