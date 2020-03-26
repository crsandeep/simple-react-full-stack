import { Router, Request, Response, NextFunction } from 'express';
import { Container } from 'typedi';
import ItemService from '../../services/item';
import winston from 'winston';
import { IItemInputDTO } from '../../interfaces/IItem';
import { celebrate, Joi } from 'celebrate';

const route = Router();

export default (app: Router) => {
  app.use('/item', route);

  route.get('/', (req: Request, res: Response) => {
    return res.json({ message: "Hello world" }).status(200);
  });


  route.get(
    '/:itemId',
    celebrate({
      params: Joi.object({
        itemId: Joi.number().required(),
      }),
    }),
    async (req: Request, res: Response, next: NextFunction) => {
      const logger:winston.Logger = Container.get('logger');    
      logger.debug('Calling getItemById endpoint');

      try {
        const itemId = parseInt(req.params.itemId,10);
        const itemService = Container.get(ItemService);
        const { result } = await itemService.getItemById(itemId);
        return res.status(201).json({ result });
      } catch (e) {
        logger.error('🔥 error: %o', e);
        return next(e);
      }
  });
  
  route.post(
    '/',
    celebrate({
      body: Joi.object({
        spaceId: Joi.number(),
        itemId: Joi.number().required(),
        name: Joi.string().required(),
        colorCode: Joi.string(),
        imgPath: Joi.string(),
        tags: Joi.string(),
        description: Joi.string(),
        category: Joi.string(),
        reminderDtm: Joi.date(),
        reminderComplete: Joi.boolean(),
      }),
    }),
    async (req: Request, res: Response, next: NextFunction) => {
      const logger:winston.Logger = Container.get('logger');    
      logger.debug('Calling addItem endpoint');

      try {
        const itemService = Container.get(ItemService);
        const { result } = await itemService.addItem(req.body as IItemInputDTO);
        return res.status(201).json({ result });
      } catch (e) {
        logger.error('🔥 error: %o', e);
        return next(e);
      }
    }
  );

  route.put(
    '/:itemId',
    celebrate({
      body: Joi.object({
        spaceId: Joi.number(),
        itemId: Joi.number().required(),
        name: Joi.string().required(),
        colorCode: Joi.string(),
        imgPath: Joi.string(),
        tags: Joi.string(),
        description: Joi.string(),
        category: Joi.string(),
        reminderDtm: Joi.date(),
        reminderComplete: Joi.boolean(),
      }),
    }),
    async (req: Request, res: Response, next: NextFunction) => {
      const logger:winston.Logger = Container.get('logger');    
      logger.debug('Calling updateItem endpoint')

      try {
        const itemService = Container.get(ItemService);
        const { result } = await itemService.updateItem(req.body as IItemInputDTO);
        return res.status(201).json({ result });
      } catch (e) {
        logger.error('🔥 error: %o', e);
        return next(e);
      }
    }
  );


  route.delete(
    '/:itemId',
    celebrate({
      params: Joi.object({
        itemId: Joi.number().required(),
      }),
    }),
    async (req: Request, res: Response, next: NextFunction) => {
      const logger:winston.Logger = Container.get('logger');    
      logger.debug('Calling deleteItem endpoint')

      try {
        const itemId = parseInt(req.params.itemId,10);
        const itemService = Container.get(ItemService);
        const { result } = await itemService.deleteItem(itemId);
        return res.status(201).json({ result });
      } catch (e) {
        logger.error('🔥 error: %o', e);
        return next(e);
      }
  });


  route.delete(
    '/image/:itemId',
    celebrate({
      params: Joi.object({
        itemId: Joi.number().required(),
      }),
    }),
    async (req: Request, res: Response, next: NextFunction) => {
      const logger:winston.Logger = Container.get('logger');    
      logger.debug('Calling delete item image endpoint')

      try {
        const itemId = parseInt(req.params.itemId,10);
        const itemService = Container.get(ItemService);
        const { result } = await itemService.deleteItemImage(itemId);
        return res.status(201).json({ result });
      } catch (e) {
        logger.error('🔥 error: %o', e);
        return next(e);
      }
  });

  route.get(
    '/space/:spaceId',
    celebrate({
      params: Joi.object({
        spaceId: Joi.number().required(),
      }),
    }),
    async (req: Request, res: Response, next: NextFunction) => {
      const logger:winston.Logger = Container.get('logger');    
      logger.debug('Calling getItemBySpaceId endpoint')

      try {
        const spaceId = parseInt(req.params.spaceId,10);
        const itemService = Container.get(ItemService);
        const { result } = await itemService.getItemBySpaceId(spaceId);
        return res.status(201).json({ result });
      } catch (e) {
        logger.error('🔥 error: %o', e);
        return next(e);
      }
  });
};
