import { Container } from 'typedi';
import expressLoader from './express';
import Logger from './logger';
import sequelize from './sequelize';

export default async ({ expressApp }) => {
  await sequelize.sync({ });
  Container.set('sequelize', sequelize);
  Logger.info('✌️ Postgresql DB loaded and connected!');

  Container.set('logger', Logger);
  Logger.info('✌️ Logger injected into container');

  await expressLoader({ app: expressApp });
  Logger.info('✌️ Express loaded');
};
