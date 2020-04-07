import { Container } from 'typedi';
import LoggerInstance from './logger';

export default ({ models }: { models: { name: string; model: any }[] }) => {
  try {
    //put all models in container for later usage
    models.forEach(m => {
      Container.set(m.name, m.model);
    });
    LoggerInstance.info('✌️ Mongoose Models injected into container');

  } catch (e) {
    LoggerInstance.error('🔥 Error on dependency injector loader: %o', e);
    throw e;
  }
};
