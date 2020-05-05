import {
  Router, Request, Response, NextFunction
} from 'express';
import { Container } from 'typedi';
import winston from 'winston';
import { celebrate, Joi } from 'celebrate';
import { number } from 'prop-types';
import GridTrans from '../../interfaces/GridTrans';
import GridService from '../../services/GridService';
import Grid from '../../models/Grid';
import config from '../../config';

const route = Router();

export default (app: Router) => {
  // initial setup
  const logger: winston.Logger = Container.get('logger');
  const gridService = Container.get(GridService);

  function formatGridList(gridRecordList: Grid[]): GridTrans {
    logger.debug('format grid list');

    if (gridRecordList == null || gridRecordList.length === 0) {
      const empty: any = {};
      return empty;
    }

    try {
      const gridTrans: any = { layouts: [], spaceId: number, imgPath: String };

      // copy space id from 1st return element
      gridTrans.spaceId = gridRecordList[0].spaceId;

      // copy img path from 1st return element
      if (gridRecordList[0].space.imgPath != null) {
        gridTrans.imgPath = gridRecordList[0].space.imgPath.replace(config.publicFolder, '');
      } else {
        gridTrans.imgPath = null;
      }

      // copy all layout into gridTrans.layout
      for (const grid of gridRecordList) {
        // prepare items tags list
        const tagList: string[] = [];
        for (const item of grid.items) {
          if (item.tags != null) {
            tagList.push(item.tags);
          }
        }

        // convert as json object
        const layout = JSON.parse(grid.layout);
        layout.tagsList = tagList;
        gridTrans.layouts.push(layout);
      }

      return gridTrans;
    } catch (e) {
      logger.error(
        'Fail to prepare output grid list , reason: %o ',
        e.message
      );
      throw e;
    }
  }

  function formatSuccess(payload: any, message: string = null): object {
    // eslint-disable-next-line object-shorthand
    return { isSuccess: true, payload, message };
  }

  app.use('/grid', route);

  route.get(
    '/space/:spaceId',
    celebrate({
      params: Joi.object({
        spaceId: Joi.number().required()
      })
    }),
    async (req: Request, res: Response, next: NextFunction) => {
      logger.debug('Calling getGridBySpaceId endpoint');

      try {
        const spaceId: number = parseInt(req.params.spaceId, 10);
        const gridRecordList: Grid[] = await gridService.getGridBySpaceId(
          spaceId
        );
        const result: GridTrans = formatGridList(gridRecordList);
        return res.status(200).json(formatSuccess(result));
      } catch (e) {
        logger.error('🔥 error: %o', e);
        return next(e);
      }
    }
  );

  route.post(
    '/',
    celebrate({
      body: Joi.object({
        spaceId: Joi.number().required(),
        layouts: Joi.array().items(Joi.object({
          x: Joi.number().required(),
          y: Joi.number().required(),
          w: Joi.number().required(),
          h: Joi.number().required(),
          i: Joi.string().required()
        }))
      })
    }),
    async (req: Request, res: Response, next: NextFunction) => {
      logger.debug('Calling addGrid endpoint');

      try {
        const input: GridTrans = req.body;
        const gridRecord: Grid[] = await gridService.saveGrid(input);
        const result: GridTrans = formatGridList(gridRecord);
        return res.status(201).json(formatSuccess(result));
      } catch (e) {
        logger.error('🔥 error: %o', e);
        return next(e);
      }
    }
  );

  route.delete(
    '/:gridId',
    celebrate({
      params: Joi.object({
        gridId: Joi.number().required()
      })
    }),
    async (req: Request, res: Response, next: NextFunction) => {
      logger.debug('Calling deleteGrid endpoint');

      try {
        const gridId: number = parseInt(req.params.gridId, 10);
        const gridRecord: Grid = await gridService.deleteGrid(gridId);
        const result: GridTrans = formatGridList([gridRecord]); // pass in as list
        return res.status(200).json(formatSuccess(result));
      } catch (e) {
        logger.error('🔥 error: %o', e);
        return next(e);
      }
    }
  );
};
