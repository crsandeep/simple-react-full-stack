import { Router, Request, Response } from 'express';
import { Container } from 'typedi';
import winston from 'winston';

const route = Router();

export default (app: Router) => {
  app.use('/item', route);

  route.get('/', (req: Request, res: Response) => {
    return res.json({ message: "Hello world" }).status(200);
  });

  route.get('/:itemId', (req: Request, res: Response) => {
    const logger:winston.Logger = Container.get('logger');    
    logger.debug('Item Id: %o', req.params.itemId)

    return res.json({ itemId: req.params.itemId }).status(200);
  });
};
