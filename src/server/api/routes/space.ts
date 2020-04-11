import { Router, Request, Response, NextFunction } from 'express';
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
  //initial setup
  //prepare file upload
  const multerUpload = multer({ 
     storage: multer.diskStorage(multerOptions.storageOptions),
     limits: multerOptions.fileSizeFilter,
     fileFilter: multerOptions.fileTypeFilter
  });
  const logger:winston.Logger = Container.get('logger');  
  const spaceService = Container.get(SpaceService);  

  app.use('/space', route);
  
  route.get(
    '/:spaceId',
    celebrate({
      params: Joi.object({
        spaceId: Joi.number().required(),
      }),
    }),
    async (req: Request, res: Response, next: NextFunction) => {
      logger.debug('Calling getSpaceById endpoint');

      try {
        const spaceId:number = parseInt(req.params.spaceId,10);
        const spaceRecord:Space = await spaceService.getSpaceById(spaceId);
        const result:SpaceTrans = formatSpace(spaceRecord);
        return res.status(200).json(formatSuccess(result));
      } catch (e) {
        logger.error('🔥 error: %o', e);
        return next(e);
      }
  });

  
  route.get(
    '/user/:userId',
    celebrate({
      params: Joi.object({
        userId: Joi.number().required(),
      }),
    }),
    async (req: Request, res: Response, next: NextFunction) => {
      logger.debug('Calling getSpaceByUserId endpoint')

      try {
        const userId:number = parseInt(req.params.userId,10);
        const spaceRecordList:Space[] = await spaceService.getSpaceByUserId(userId);
        const result:SpaceTrans[] = formatSpaceList(spaceRecordList);
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
        userId: Joi.number().required(),
        spaceId: Joi.number().allow(null),
        name: Joi.string().required(),
        colorCode: Joi.string().required(),
        imgPath: Joi.string().allow(null),
        tags: Joi.string().allow(null),
        location: Joi.string().required(),
        sizeUnit: Joi.string().allow(null),
        sizeWidth: Joi.number().allow(null),
        sizeHeight: Joi.number().allow(null),
        sizeDepth: Joi.number().allow(null),
      }),
    }),
    async (req: Request, res: Response, next: NextFunction) => {
      logger.debug('Calling addSpace endpoint');

      try {
        let input:SpaceTrans = req.body;
        input.imgPath = (req.file!=null?req.file.path:null);
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
        colorCode: Joi.string().required(),
        imgPath: Joi.string().allow(null),
        tags: Joi.string().allow(null),
        location: Joi.string().required(),
        sizeUnit: Joi.string().allow(null),
        sizeWidth: Joi.number().allow(null),
        sizeHeight: Joi.number().allow(null),
        sizeDepth: Joi.number().allow(null),
      }),
    }),
    async (req: Request, res: Response, next: NextFunction) => {
      logger.debug('Calling updateSpace endpoint')

      try {
        let input:SpaceTrans = req.body;
        input.spaceId = parseInt(req.params.spaceId);
        input.imgPath = (req.file!=null?req.file.path:null);
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
        spaceId: Joi.number().required(),
      }),
    }),
    async (req: Request, res: Response, next: NextFunction) => {
      logger.debug('Calling deleteSpace endpoint')

      try {
        const spaceId:number = parseInt(req.params.spaceId,10);
        const spaceRecord:Space = await spaceService.deleteSpace(spaceId);
        const result:SpaceTrans = formatSpace(spaceRecord);
        return res.status(200).json(formatSuccess(result));
      } catch (e) {
        logger.error('🔥 error: %o', e);
        return next(e);
      }
  });

  
  route.delete(
    '/image/:spaceId',
    celebrate({
      params: Joi.object({
        spaceId: Joi.number().required(),
      }),
    }),
    async (req: Request, res: Response, next: NextFunction) => {
      logger.debug('Calling delete space image endpoint')

      try {
        const spaceId:number = parseInt(req.params.spaceId,10);
        const result:boolean = await spaceService.deleteSpaceImage(spaceId);
        return res.status(200).json(formatSuccess(result));
      } catch (e) {
        logger.error('🔥 error: %o', e);
        return next(e);
      }
  });

  function formatSuccess(payload:any, message:string = null):object{
    return {isSuccess:true, payload: payload, message: message};
  }

  function formatSpaceList(spaceRecordList: (Space)[]): SpaceTrans[] {
    logger.debug('format space list');

    if (spaceRecordList == null) {
      let empty:any = {};
      return empty;
    }

    try {
      let outputSpaceList: SpaceTrans[] = [];
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

  function formatSpace(spaceRecord: Space): SpaceTrans {
    logger.debug('format space');
    let outputSpace:any = {};

    const excludeAttr:string[] = ['creationDate','updatedOn'];

    if (spaceRecord == null) {
      let empty:any = {};
      return empty;
    }

    try {
      //remove image path for display
      if(spaceRecord.imgPath!=null){
        spaceRecord.imgPath = spaceRecord.imgPath.replace(config.publicFolder,'');
      }

      //copy value from db object to transmission object
      for (let [key, value] of Object.entries(spaceRecord['dataValues'])) {
        if(excludeAttr.indexOf(key)<0){
          //non exclude field
          outputSpace[key] = value;
        }
      }

      return outputSpace;
    } catch (e) {
      logger.error('Fail to prepare output space , reason: %o ', e.message);
      throw e;
    }
  }

};
