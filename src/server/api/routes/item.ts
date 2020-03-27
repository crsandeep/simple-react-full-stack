import { Router, Request, Response, NextFunction } from 'express';
import { Container } from 'typedi';
import ItemService from '../../services/item';
import winston from 'winston';
import { IItemInputDTO } from '../../interfaces/IItem';
import { celebrate, Joi } from 'celebrate';
import multer from 'multer';
import config from '../../config';
import path from 'path';
import {v4 as uuid} from 'uuid';

const route = Router();


//multer file upload
var storage = multer.diskStorage({
  destination: function (req, file, cb) {
    cb(null, config.fileUpload.tempPath);
  },
  filename: function (req, file, cb) {
    cb(null, uuid() + path.extname(file.originalname))
  }
})
var upload = multer({ storage: storage });

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
        spaceId: Joi.number().allow(null),
        itemId: Joi.number().allow(null),
        name: Joi.string().required(),
        colorCode: Joi.string(),
        imgPath: Joi.string().allow(null),
        tags: Joi.string().allow(null),
        description: Joi.string().allow(null),
        category: Joi.string(),
        reminderDtm: Joi.date().allow(null),
        reminderComplete: Joi.boolean().allow(null),
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

  
  
  // route.put(
  //   '/file/',   
  //   celebrate({
  //     body: Joi.object({
  //       itemId: Joi.number().allow(null),
  //     })
  //   }),
  //   upload.single('imgFile'),
  //   async (req: Request, res: Response, next: NextFunction) => {
  //     const logger:winston.Logger = Container.get('logger');    
  //     logger.debug('Calling file endpoint');

  //     let input = req.body as IItemInputDTO;
  //     input.imgPath = req.file.path;
  //     logger.debug('Calling file endpoint, %o',input);

  //     const itemService = Container.get(ItemService);
  //     const { result } = await itemService.addItem(req.body as IItemInputDTO);

  //     return res.status(201).json({ result });
  //   }
  // );


  route.put(
    '/:itemId',
    celebrate({
      body: Joi.object({
        spaceId: Joi.number().allow(null),
        itemId: Joi.number().required(),
        name: Joi.string().required(),
        colorCode: Joi.string(),
        imgPath: Joi.string().allow(null),
        tags: Joi.string().allow(null),
        description: Joi.string().allow(null),
        category: Joi.string(),
        reminderDtm: Joi.date().allow(null),
        reminderComplete: Joi.boolean().allow(null),
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
