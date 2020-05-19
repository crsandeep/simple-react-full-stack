import {
  Router, Request, Response, NextFunction
} from 'express';
import { Container } from 'typedi';
import winston from 'winston';
import { celebrate, Joi } from 'celebrate';
import multer from 'multer';
import SpaceTrans from '../../interfaces/SpaceTrans';
import SpaceService from '../../services/SpaceService';
import * as multerOptions from '../../config/multer';
import config from '../../config';
import Space from '../../models/Space';

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
  const spaceService = Container.get(SpaceService);


  function formatSuccess(payload:any, message:string = null):object {
    return { isSuccess: true, payload, message };
  }

  function formatSpace(spaceRecord: Space): SpaceTrans {
    logger.debug('format space');
    const outputSpace:any = {};

    const excludeAttr:string[] = ['creationDate', 'updatedOn', 'grids'];

    if (spaceRecord == null) {
      const empty:any = {};
      return empty;
    }

    try {
      // remove image path for display
      if (spaceRecord.imgPath != null) {
        spaceRecord.imgPath = spaceRecord.imgPath.replace(config.publicFolder, '');
      }

      // copy value from db object to transmission object
      // eslint-disable-next-line dot-notation
      for (const [key, value] of Object.entries(spaceRecord['dataValues'])) {
        if (excludeAttr.indexOf(key) < 0) {
          // non exclude field
          outputSpace[key] = value;
        }
      }

      // prepare grids and item tags
      let tagList: string[] = null;
      let gridCount:number = 0;
      let itemCount:number = 0;
      let tempArr: string[] = null;
      if (spaceRecord.grids != null) {
        gridCount = spaceRecord.grids.length;

        tagList = [];
        for (const grid of spaceRecord.grids) {
          // get grid's each item
          if (grid.items != null) {
            itemCount += grid.items.length;

            for (const item of grid.items) {
              // prepare unique tag list
              if (item.tags != null) {
                // tags stored in comma format, split to get unqiue value
                tempArr = item.tags.split(',');
                for (const tag of tempArr) {
                  if (tagList.indexOf(tag.trim()) < 0) {
                    tagList.push(tag.trim());
                  }
                }
              }
            }
          }
        }
      }
      outputSpace.gridCount = gridCount;
      outputSpace.itemCount = itemCount;
      outputSpace.itemTags = tagList;

      return outputSpace;
    } catch (e) {
      logger.error('Fail to prepare output space , reason: %o ', e.message);
      throw e;
    }
  }

  function formatSpaceList(spaceRecordList: (Space)[]): SpaceTrans[] {
    logger.debug('format space list');

    if (spaceRecordList == null) {
      const empty:any = {};
      return empty;
    }

    try {
      const outputSpaceList: SpaceTrans[] = [];
      if (spaceRecordList != null) {
        spaceRecordList.map((space) => {
          outputSpaceList.push(formatSpace(space));
        });
      }
      return outputSpaceList;
    } catch (e) {
      logger.error('Fail to prepare output space list , reason: %o ', e.message);
      throw e;
    }
  }

  app.use('/space', route);

  route.get(
    '/:spaceId',
    celebrate({
      params: Joi.object({
        spaceId: Joi.number().required()
      })
    }),
    async (req: Request, res: Response, next: NextFunction) => {
      logger.debug('Calling getSpaceById endpoint');

      try {
        const spaceId:number = parseInt(req.params.spaceId, 10);
        const spaceRecord:Space = await spaceService.getSpaceById(spaceId);
        const result:SpaceTrans = formatSpace(spaceRecord);
        return res.status(200).json(formatSuccess(result));
      } catch (e) {
        logger.error('🔥 error: %o', e);
        return next(e);
      }
    }
  );


  route.get(
    '/user/:userId',
    celebrate({
      params: Joi.object({
        userId: Joi.number().required()
      })
    }),
    async (req: Request, res: Response, next: NextFunction) => {
      logger.debug('Calling getSpaceByUserId endpoint');

      try {
        const userId:number = parseInt(req.params.userId, 10);
        const spaceRecordList:Space[] = await spaceService.getSpaceByUserId(userId);
        const result:SpaceTrans[] = formatSpaceList(spaceRecordList);
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
        userId: Joi.number().required(),
        spaceId: Joi.number().allow(null),
        name: Joi.string().required(),
        imgPath: Joi.string().allow(null),
        location: Joi.string().required()
      })
    }),
    async (req: Request, res: Response, next: NextFunction) => {
      logger.debug('Calling addSpace endpoint');

      try {
        const input:SpaceTrans = req.body;
        input.imgPath = (req.file != null ? req.file.path : null);
        const spaceRecord:Space = await spaceService.addSpace(input);
        const result:SpaceTrans = formatSpace(spaceRecord);
        return res.status(201).json(formatSuccess(result));
      } catch (e) {
        logger.error('🔥 error: %o', e);
        return next(e);
      }
    }
  );

  route.put(
    '/:spaceId',
    multerUpload.single('imgFile'),
    celebrate({
      body: Joi.object({
        userId: Joi.number().required(),
        spaceId: Joi.number().allow(null),
        name: Joi.string().required(),
        imgPath: Joi.string().allow(null),
        location: Joi.string().required()
      })
    }),
    async (req: Request, res: Response, next: NextFunction) => {
      logger.debug('Calling updateSpace endpoint');

      try {
        const input:SpaceTrans = req.body;
        input.spaceId = parseInt(req.params.spaceId, 10);
        input.imgPath = (req.file != null ? req.file.path : null);
        const updResult:Space = await spaceService.updateSpace(input);
        const result:SpaceTrans = formatSpace(updResult);
        return res.status(201).json(formatSuccess(result));
      } catch (e) {
        logger.error('🔥 error: %o', e);
        return next(e);
      }
    }
  );


  route.delete(
    '/:spaceId',
    celebrate({
      params: Joi.object({
        spaceId: Joi.number().required()
      })
    }),
    async (req: Request, res: Response, next: NextFunction) => {
      logger.debug('Calling deleteSpace endpoint');

      try {
        const spaceId:number = parseInt(req.params.spaceId, 10);
        const spaceRecord:Space = await spaceService.deleteSpace(spaceId);
        const result:SpaceTrans = formatSpace(spaceRecord);
        return res.status(200).json(formatSuccess(result));
      } catch (e) {
        logger.error('🔥 error: %o', e);
        return next(e);
      }
    }
  );


  route.delete(
    '/image/:spaceId',
    celebrate({
      params: Joi.object({
        spaceId: Joi.number().required()
      })
    }),
    async (req: Request, res: Response, next: NextFunction) => {
      logger.debug('Calling delete space image endpoint');

      try {
        const spaceId:number = parseInt(req.params.spaceId, 10);
        const result:boolean = await spaceService.deleteSpaceImage(spaceId);
        return res.status(200).json(formatSuccess(result));
      } catch (e) {
        logger.error('🔥 error: %o', e);
        return next(e);
      }
    }
  );
};
