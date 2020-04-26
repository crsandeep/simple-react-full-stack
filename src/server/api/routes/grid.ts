import {
  Router, Request, Response, NextFunction
} from 'express';
import { Container } from 'typedi';
import winston from 'winston';
import { celebrate, Joi } from 'celebrate';
import GridTrans from '../../interfaces/GridTrans';
import GridService from '../../services/GridService';
import Grid from '../../models/Grid';

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
      const gridTrans: any = { layouts: [] };
      let layoutObj: any;

      // copy space id
      gridTrans.spaceId = gridRecordList[0].spaceId;

      // copy all layout into gridTrans.layout
      for (const grid of gridRecordList) {
        // convert as json object
        layoutObj = JSON.parse(grid.layout);

        // copy grid id into i as key
        layoutObj.i = grid.gridId;

        gridTrans.layouts.push(layoutObj);
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
          i: Joi.number().required(),
          minW: Joi.number().required(),
          maxW: Joi.number().required(),
          minH: Joi.number().required(),
          maxH: Joi.number().required(),
          moved: Joi.boolean().required(),
          static: Joi.boolean().required()
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
