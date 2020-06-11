import { Sequelize, Repository } from 'sequelize-typescript';
import { Container } from 'typedi';
import { Strategy, ExtractJwt, StrategyOptions } from 'passport-jwt';
import winston from 'winston';
import config from '../config';
// import User from '../models/user.model'
import User from '../models/User';

const ops: StrategyOptions = {
  jwtFromRequest: ExtractJwt.fromAuthHeaderAsBearerToken(),
  secretOrKey: config.jwtSecret
};

// validate userId in JWT token is exist in database
export default new Strategy(ops, async (payload, done) => {
  const logger = Container.get<winston.Logger>('logger');

  try {
    logger.debug('Calling passport Strategy to retrieve user from DB by userId');
    const UserRepo:Repository<User> = Container.get<Sequelize>('sequelize').getRepository<User>(User);

    // check user exist in db
    const userRecord = await UserRepo.findOne({ attributes: ['userId', 'name', 'role'], where: { userId: payload.userId } });
    if (userRecord) {
      return done(null, userRecord);
    }
    done(null, false);
  } catch (e) {
    logger.error('Fail to get user, reason: %o ', e.message);
    throw e;
  }
});
