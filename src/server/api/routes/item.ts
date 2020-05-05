import {
  Router, Request, Response, NextFunction
} from 'express';
import { Container } from 'typedi';
import winston from 'winston';
import { celebrate, Joi } from 'celebrate';
import multer from 'multer';
import ItemTrans from '../../interfaces/ItemTrans';
import ItemService from '../../services/ItemService';
import * as multerOptions from '../../config/multer';
import config from '../../config';
import Item from '../../models/Item';
import grid from './grid';

const route = Router();

export default (app: Router) => {
  // initial setup
  // prepare file upload
  const multerUpload = multer({
    storage: multer.diskStorage(multerOptions.storageOptions),
    limits: multerOptions.fileSizeFilter,
    fileFilter: multerOptions.fileTypeFilter
  });
  const logger:winston.Logger = Container.get('logger');
  const itemService = Container.get(ItemService);


  function formatSuccess(payload:any, message:string = null):object {
    return { isSuccess: true, payload, message };
  }


  function formatItem(itemRecord: Item): ItemTrans {
    logger.debug('format item');
    const outputItem:any = {};

    const excludeAttr:string[] = ['creationDate',
      'updatedOn',
      'grid' // special handle for grid
    ];

    if (itemRecord == null) {
      const empty:any = {};
      return empty;
    }

    try {
      // remove image path for display
      if (itemRecord.imgPath != null) {
        itemRecord.imgPath = itemRecord.imgPath.replace(config.publicFolder, '');
      }

      // copy value from db object to transmission object
      // eslint-disable-next-line dot-notation
      for (const [key, value] of Object.entries(itemRecord['dataValues'])) {
        if (excludeAttr.indexOf(key) < 0) {
          // non exclude field
          outputItem[key] = value;
        }
      }

      // special handle for grid
      let spaceName = null;
      let spaceLocation = null;
      if (itemRecord.grid != null && itemRecord.grid.space != null) {
        if (itemRecord.grid.space.name != null) {
          spaceName = itemRecord.grid.space.name;
        }
        if (itemRecord.grid.space.location != null) {
          spaceLocation = itemRecord.grid.space.location;
        }
      }
      outputItem.spaceName = spaceName;
      outputItem.spaceLocation = spaceLocation;

      return outputItem;
    } catch (e) {
      logger.error('Fail to prepare output item , reason: %o ', e.message);
      throw e;
    }
  }

  function formatItemList(itemRecordList: (Item)[]): ItemTrans[] {
    logger.debug('format item list');

    if (itemRecordList == null) {
      const empty:any = {};
      return empty;
    }

    try {
      const outputItemList: ItemTrans[] = [];
      if (itemRecordList != null) {
        for (const item of itemRecordList) {
          outputItemList.push(formatItem(item));
        }
      }
      return outputItemList;
    } catch (e) {
      logger.error('Fail to prepare output item list , reason: %o ', e.message);
      throw e;
    }
  }


  app.use('/item', route);

  route.get(
    '/:itemId',
    celebrate({
      params: Joi.object({
        itemId: Joi.number().required()
      })
    }),
    async (req: Request, res: Response, next: NextFunction) => {
      logger.debug('Calling getItemById endpoint');

      try {
        const itemId:number = parseInt(req.params.itemId, 10);
        const itemRecord:Item = await itemService.getItemById(itemId);
        const result:ItemTrans = formatItem(itemRecord);
        return res.status(200).json(formatSuccess(result));
      } catch (e) {
        logger.error('🔥 error: %o', e);
        return next(e);
      }
    }
  );


  route.get(
    '/grid/:gridId',
    celebrate({
      params: Joi.object({
        gridId: Joi.number().required()
      })
    }),
    async (req: Request, res: Response, next: NextFunction) => {
      logger.debug('Calling getItemByGridId endpoint');

      try {
        const gridId:number = parseInt(req.params.gridId, 10);
        const itemRecordList:Item[] = await itemService.getItemByGridId(gridId);
        const result:ItemTrans[] = formatItemList(itemRecordList);
        return res.status(200).json(formatSuccess(result));
      } catch (e) {
        logger.error('🔥 error: %o', e);
        return next(e);
      }
    }
  );

  route.post(
    '/',
    multerUpload.single('imgFile'),
    celebrate({
      body: Joi.object({
        gridId: Joi.number().required(),
        itemId: Joi.number().allow(null),
        name: Joi.string().required(),
        colorCode: Joi.string().required(),
        imgPath: Joi.string().allow(null),
        tags: Joi.string().allow(null),
        description: Joi.string().allow(null),
        category: Joi.string().required(),
        reminderDtm: Joi.date().allow(null),
        reminderComplete: Joi.boolean().allow(null)
      })
    }),
    async (req: Request, res: Response, next: NextFunction) => {
      logger.debug('Calling addItem endpoint');

      try {
        const input:ItemTrans = req.body;
        input.imgPath = (req.file != null ? req.file.path : null);
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
        gridId: Joi.number().required(),
        itemId: Joi.number().required(),
        name: Joi.string().required(),
        colorCode: Joi.string().required(),
        imgPath: Joi.string().allow(null),
        tags: Joi.string().allow(null),
        description: Joi.string().allow(null),
        category: Joi.string().required(),
        reminderDtm: Joi.date().allow(null),
        reminderComplete: Joi.boolean().allow(null)
      })
    }),
    async (req: Request, res: Response, next: NextFunction) => {
      logger.debug('Calling updateItem endpoint');

      try {
        const input:ItemTrans = req.body;
        input.itemId = parseInt(req.params.itemId, 10);
        input.imgPath = (req.file != null ? req.file.path : null);
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
        itemId: Joi.number().required()
      })
    }),
    async (req: Request, res: Response, next: NextFunction) => {
      logger.debug('Calling deleteItem endpoint');

      try {
        const itemId:number = parseInt(req.params.itemId, 10);
        const itemRecord:Item = await itemService.deleteItem(itemId);
        const result:ItemTrans = formatItem(itemRecord);
        return res.status(200).json(formatSuccess(result));
      } catch (e) {
        logger.error('🔥 error: %o', e);
        return next(e);
      }
    }
  );


  route.delete(
    '/image/:itemId',
    celebrate({
      params: Joi.object({
        itemId: Joi.number().required()
      })
    }),
    async (req: Request, res: Response, next: NextFunction) => {
      logger.debug('Calling delete item image endpoint');

      try {
        const itemId:number = parseInt(req.params.itemId, 10);
        const result:boolean = await itemService.deleteItemImage(itemId);
        return res.status(200).json(formatSuccess(result));
      } catch (e) {
        logger.error('🔥 error: %o', e);
        return next(e);
      }
    }
  );
};
