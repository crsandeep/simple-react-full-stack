import { Router, Request, Response, NextFunction } from 'express';
import { Container } from 'typedi';
import UserService from '../../services/user';
import winston from 'winston';
import { IUserInputDTO } from '../../interfaces/IUser';
import { celebrate, Joi } from 'celebrate';

const route = Router();

export default (app: Router) => {
  app.use('/user', route);

  route.get('/', (req: Request, res: Response) => {
    return res.json({ message: "Hello world" }).status(200);
  });

  route.get(
    '/:itemId',
    async (req: Request, res: Response, next: NextFunction) => {
    const logger:winston.Logger = Container.get('logger');    
    logger.debug('Calling Sign-In endpoint with body: %o, %o', req.body, req.params)

    try {
      const email:string ='test@test.com';
      const password:string ='test123';
      const UserServiceInstance = Container.get(UserService);
      const { user } = await UserServiceInstance.SignIn(email, password);
      return res.status(201).json({ user });
    } catch (e) {
      logger.error('🔥 error: %o', e);
      return next(e);
    }

  });
  
  route.post(
    '/',
    celebrate({
      body: Joi.object({
        name: Joi.string().required(),
        email: Joi.string().required(),
        password: Joi.string().required(),
      }),
    }),
    async (req: Request, res: Response, next: NextFunction) => {
      const logger:winston.Logger = Container.get('logger');    
      logger.debug('Calling Sign-In endpoint with body: %o, %o', req.body, req.params)

      try {
        const UserServiceInstance = Container.get(UserService);
        const { user } = await UserServiceInstance.SignUp(req.body as IUserInputDTO);
        return res.status(201).json({ user });
      } catch (e) {
        logger.error('🔥 error: %o', e);
        return next(e);
      }
    }
  );
};
