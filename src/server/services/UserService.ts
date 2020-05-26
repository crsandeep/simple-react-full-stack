import { Sequelize, Repository } from 'sequelize-typescript';
import { Service, Container } from 'typedi';
import winston from 'winston';
import jwt from 'jsonwebtoken';
import * as bcrypt from 'bcryptjs';
import config from '../config';
import AuthTrans from '../interfaces/AuthTrans';
import UserTrans from '../interfaces/UserTrans';

import User from '../models/User';
import Constants from '../Constants/Role';

@Service()
export default class UserService {
  private logger:winston.Logger;

  private userRepo:Repository<User>;


  constructor() {
    this.logger = Container.get<winston.Logger>('logger');
    this.userRepo = Container.get<Sequelize>('sequelize').getRepository<User>(User);
  }

  public async signUp(userTrans: UserTrans): Promise<User> {
    try {
      const userRecord = await this.userRepo.findOne({ where: { email: userTrans.email } });
      if (userRecord) {
        this.logger.error('Fail to create user, email already registered');
        throw new Error('User cannot be created, user already exist');
      }

      userTrans.role = Constants.ROLE_BASIC_USER;
      userTrans.password = bcrypt.hashSync(userTrans.password, 8);
      const newUser = await this.userRepo.create(userTrans);

      return newUser;
    } catch (e) {
      this.logger.error('Fail to create user, reason: %o ', e.message);
      throw e;
    }
  }

  public async login(userTrans: UserTrans): Promise<AuthTrans> {
    try {
      const userRecord = await this.userRepo.findOne({ where: { email: userTrans.email } });
      if (!userRecord) {
        this.logger.error('Email or password incorrect');
        throw new Error('Email or password incorrect');
      }

      // check password with hash
      const isPswdValid = bcrypt.compareSync(userTrans.password, userRecord.password);
      if (!isPswdValid) {
        this.logger.error('Email or password incorrect');
        throw new Error('Email or password incorrect');
      }

      // return object
      const authTrans: AuthTrans = {};
      authTrans.isAuthenticated = true;
      authTrans.email = userRecord.email;
      authTrans.userId = userRecord.userId;
      authTrans.token = jwt.sign({ userId: userRecord.userId, email: userRecord.email }, config.jwtSecret, { expiresIn: config.tokenExpireMins });

      return authTrans;
    } catch (e) {
      this.logger.error('Fail to login, reason: %o ', e.message);
      throw e;
    }
  }
}
