import {
  Router, Request, Response, NextFunction
} from 'express';
import { Container } from 'typedi';
import winston from 'winston';
import { celebrate, Joi } from 'celebrate';
import passport from 'passport';
import config from '../../config';
import User from '../../models/User';
import AuthTrans from '../../interfaces/AuthTrans';
import UserTrans from '../../interfaces/UserTrans';
import UserService from '../../services/UserService';

const route = Router();

export default (app: Router) => {
  // initial setup
  const logger:winston.Logger = Container.get('logger');
  const userService = Container.get(UserService);


  function formatSuccess(payload:any, message:string = null):object {
    return { isSuccess: true, payload, message };
  }

  function formatUser(userRecord: User): UserTrans {
    const outputItem:any = {};

    const excludeAttr:string[] = ['creationDate',
      'updatedOn',
      'password'
    ];

    if (userRecord == null) {
      const empty:any = {};
      return empty;
    }

    try {
      // copy value from db object to transmission object
      // eslint-disable-next-line dot-notation
      for (const [key, value] of Object.entries(userRecord['dataValues'])) {
        if (excludeAttr.indexOf(key) < 0) {
          // non exclude field
          outputItem[key] = value;
        }
      }

      return outputItem;
    } catch (e) {
      logger.error('Fail to prepare output item , reason: %o ', e.message);
      throw e;
    }
  }

  app.use('/auth', route);

  route.post(
    '/signUp',
    celebrate({
      body: Joi.object({
        email: Joi.string().required(),
        name: Joi.string().required(),
        password: Joi.string().required()
      })
    }),
    async (req: Request, res: Response, next: NextFunction) => {
      logger.debug('Calling singUp endpoint');

      try {
        const input:UserTrans = req.body;
        const userRecord:User = await userService.signUp(input);
        const result = formatUser(userRecord);
        return res.status(200).json(formatSuccess(result));
      } catch (e) {
        logger.error('🔥 error: %o', e);
        return next(e);
      }
    }
  );

  route.post(
    '/login',
    celebrate({
      body: Joi.object({
        email: Joi.string().required(),
        password: Joi.string().required()
      })
    }),
    async (req: Request, res: Response, next: NextFunction) => {
      logger.debug('Calling login endpoint');
      const input:UserTrans = req.body;

      try {
        const authRecord:AuthTrans = await userService.login(input);
        return res.status(200).json(formatSuccess(authRecord));
      } catch (e) {
        logger.error('🔥 error: %o', e);
        return next(e);
      }
    }
  );


  route.get(
    '/public',
    async (req: Request, res: Response, next: NextFunction) => {
      logger.debug(`Calling public endpoint${JSON.stringify(req.user)}`);
      res.send('Success');
    }
  );

  route.get(
    '/restricted',
    passport.authenticate('jwt', { session: false }),
    async (req: Request, res: Response, next: NextFunction) => {
      logger.debug(`Calling restricted endpoint${JSON.stringify(req.user)}`);
      const currUser = req.user as User;

      logger.debug(`${currUser.userId} - ${currUser.email}`);

      res.send('Success');
    }
  );
};
