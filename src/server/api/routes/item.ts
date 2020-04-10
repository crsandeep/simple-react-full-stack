import { Router, Request, Response, NextFunction } from 'express';
import { Container } from 'typedi';
import winston from 'winston';
import { celebrate, Joi } from 'celebrate';
import multer from 'multer';
import ItemTrans  from '../../interfaces/ItemTrans';
import ItemService from '../../services/item';
import * as multerOptions from '../../config/multer';
import config from '../../config';
import Item from '../../models/Item';
const route = Router();

export default (app: Router) => {
  //initial setup
  //prepare file upload
  const multerUpload = multer({ 
     storage: multer.diskStorage(multerOptions.storageOptions),
     limits: multerOptions.fileSizeFilter,
     fileFilter: multerOptions.fileTypeFilter
  });
  const logger:winston.Logger = Container.get('logger');  
  const itemService = Container.get(ItemService);  

  app.use('/item', route);
  
  route.get(
    '/:itemId',
    celebrate({
      params: Joi.object({
        itemId: Joi.number().required(),
      }),
    }),
    async (req: Request, res: Response, next: NextFunction) => {
      logger.debug('Calling getItemById endpoint');

      try {
        const itemId:number = parseInt(req.params.itemId,10);
        const itemRecord:Item = await itemService.getItemById(itemId);
        const result:ItemTrans = formatItem(itemRecord);
        return res.status(200).json(formatSuccess(result));
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
      logger.debug('Calling getItemBySpaceId endpoint')

      try {
        const spaceId:number = parseInt(req.params.spaceId,10);
        const itemRecordList:Item[] = await itemService.getItemBySpaceId(spaceId);
        const result:ItemTrans[] = formatItemList(itemRecordList);
        return res.status(200).json(formatSuccess(result));
      } catch (e) {
        logger.error('🔥 error: %o', e);
        return next(e);
      }
  });
  
  route.post(
    '/',
    multerUpload.single('imgFile'),
    celebrate({
      body: Joi.object({
        spaceId: Joi.number().required(),
        itemId: Joi.number().allow(null),
        name: Joi.string().required(),
        colorCode: Joi.string().required(),
        imgPath: Joi.string().allow(null),
        tags: Joi.string().allow(null),
        description: Joi.string().allow(null),
        category: Joi.string().required(),
        reminderDtm: Joi.date().allow(null),
        reminderComplete: Joi.boolean().allow(null),
      }),
    }),
    async (req: Request, res: Response, next: NextFunction) => {
      logger.debug('Calling addItem endpoint');

      try {
        let input:ItemTrans = req.body;
        input.imgPath = (req.file!=null?req.file.path:null);
        const itemRecord:Item = await itemService.addItem(input);
        const result:ItemTrans = formatItem(itemRecord);
        return res.status(201).json(formatSuccess(result));
      } catch (e) {
        logger.error('🔥 error: %o', e);
        return next(e);
      }
    }
  );

  route.put(
    '/:itemId',
    multerUpload.single('imgFile'),
    celebrate({
      body: Joi.object({
        spaceId: Joi.number().required(),
        itemId: Joi.number().required(),
        name: Joi.string().required(),
        colorCode: Joi.string().required(),
        imgPath: Joi.string().allow(null),
        tags: Joi.string().allow(null),
        description: Joi.string().allow(null),
        category: Joi.string().required(),
        reminderDtm: Joi.date().allow(null),
        reminderComplete: Joi.boolean().allow(null),
      }),
    }),
    async (req: Request, res: Response, next: NextFunction) => {
      logger.debug('Calling updateItem endpoint')

      try {
        let input:ItemTrans = req.body;
        input.itemId = parseInt(req.params.itemId);
        input.imgPath = (req.file!=null?req.file.path:null);
        const updResult:Item = await itemService.updateItem(input);
        const result:ItemTrans = formatItem(updResult);
        return res.status(201).json(formatSuccess(result));
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
      logger.debug('Calling deleteItem endpoint')

      try {
        const itemId:number = parseInt(req.params.itemId,10);
        const itemRecord:Item = await itemService.deleteItem(itemId);
        const result:ItemTrans = formatItem(itemRecord);
        return res.status(200).json(formatSuccess(result));
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
      logger.debug('Calling delete item image endpoint')

      try {
        const itemId:number = parseInt(req.params.itemId,10);
        const result:boolean = await itemService.deleteItemImage(itemId);
        return res.status(200).json(formatSuccess(result));
      } catch (e) {
        logger.error('🔥 error: %o', e);
        return next(e);
      }
  });

  function formatSuccess(payload:any, message:string = null):object{
    return {isSuccess:true, payload: payload, message: message};
  }

  function formatItemList(itemRecordList: (Item)[]): ItemTrans[] {
    logger.debug('format item list');

    if (itemRecordList == null) {
      let empty:any = {};
      return empty;
    }

    try {
      let outputItemList: ItemTrans[] = [];
      if (itemRecordList != null) {
        itemRecordList.map((item) => {
          outputItemList.push(formatItem(item));
        });
      }
      return outputItemList;
    } catch (e) {
      logger.error('Fail to prepare output item list , reason: %o ', e.message);
      throw e;
    }
  }

  function formatItem(itemRecord: Item): ItemTrans {
    logger.debug('format item');
    let outputItem:any = {};

    const excludeAttr:string[] = ['creationDate','updatedOn'];

    if (itemRecord == null) {
      let empty:any = {};
      return empty;
    }

    try {
      //remove image path for display
      if(itemRecord.imgPath!=null){
        itemRecord.imgPath = itemRecord.imgPath.replace(config.publicFolder,'');
      }

      //copy value from db object to transmission object
      for (let [key, value] of Object.entries(itemRecord['dataValues'])) {
        if(excludeAttr.indexOf(key)<0){
          //non exclude field
          outputItem[key] = value;
        }
      }

      return outputItem;
    } catch (e) {
      logger.error('Fail to prepare output item , reason: %o ', e.message);
      throw e;
    }
  }

};
