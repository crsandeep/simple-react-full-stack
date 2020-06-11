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
import MessageCd from '../Constants/MessageCd';

import OperationResult from '../util/operationResult';

@Service()
export default class UserService {
  private logger:winston.Logger;

  private userRepo:Repository<User>;


  constructor() {
    this.logger = Container.get<winston.Logger>('logger');
    this.userRepo = Container.get<Sequelize>('sequelize').getRepository<User>(User);
  }

  public async register(userTrans: UserTrans): Promise<OperationResult> {
    try {
      const operResult = new OperationResult();
      const userRecord = await this.userRepo.findOne({ where: { email: userTrans.email } });
      if (userRecord) {
        this.logger.error('Fail to create user, Email already registered');
        operResult.setFail(MessageCd.USER_EMAIL_ALREADY_EXIST, 'Fail to create user, Email already registered');
        return operResult;
      }

      userTrans.role = Constants.ROLE_BASIC_USER;
      userTrans.password = bcrypt.hashSync(userTrans.password, 8);
      const newUser = await this.userRepo.create(userTrans);
      operResult.setSuccess(newUser);
      return operResult;
    } catch (e) {
      this.logger.error('Fail to create user, reason: %o ', e.message);
      throw e;
    }
  }

  public async login(userTrans: UserTrans): Promise<OperationResult> {
    try {
      const operResult = new OperationResult();
      const userRecord = await this.userRepo.findOne({ where: { email: userTrans.email } });

      if (!userRecord) {
        this.logger.error('Email or password incorrect');
        operResult.setFail(MessageCd.USER_LOGIN_INVALID_CREDENTIAL, 'Fail to login, Email or password incorrect');
        return operResult;
      }

      // check password with hash
      const isPswdValid = bcrypt.compareSync(userTrans.password, userRecord.password);
      if (!isPswdValid) {
        this.logger.error('Email or password incorrect');
        operResult.setFail(MessageCd.USER_LOGIN_INVALID_CREDENTIAL, 'Fail to login, Email or password incorrect');
        return operResult;
      }

      // create JWT token
      const authTrans: AuthTrans = {};
      authTrans.isAuthenticated = true;
      authTrans.name = userRecord.name;
      authTrans.userId = userRecord.userId;

      // sign token
      authTrans.token = jwt.sign(
        { userId: userRecord.userId, name: userRecord.name },
        config.jwtSecret, { expiresIn: config.tokenExpireMins }
      );

      operResult.setSuccess(authTrans);
      return operResult;
    } catch (e) {
      this.logger.error('Fail to login, reason: %o ', e.message);
      throw e;
    }
  }
}
