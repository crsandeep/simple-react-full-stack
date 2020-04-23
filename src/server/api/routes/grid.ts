import {
  Router, Request, Response, NextFunction
} from 'express';
import { Container } from 'typedi';
import winston from 'winston';
import { celebrate, Joi } from 'celebrate';
import GridTrans from '../../interfaces/GridTrans';
import GridService from '../../services/GridService';
import config from '../../config';
import Grid from '../../models/Grid';

const route = Router();

export default (app: Router) => {
  // initial setup
  const logger: winston.Logger = Container.get('logger');
  const gridService = Container.get(GridService);

  function formatGrid(gridRecord: Grid): GridTrans {
    logger.debug('format grid');
    const outputGrid: any = {};

    const excludeAttr: string[] = ['creationDate', 'updatedOn'];

    if (gridRecord == null) {
      const empty: any = {};
      return empty;
    }

    try {
      // copy value from db object to transmission object
      for (const [key, value] of Object.entries(gridRecord['dataValues'])) {
        if (excludeAttr.indexOf(key) < 0) {
          // non exclude field
          outputGrid[key] = value;
        }
      }

      return outputGrid;
    } catch (e) {
      logger.error('Fail to prepare output grid , reason: %o ', e.message);
      throw e;
    }
  }

  function formatGridList(gridRecordList: Grid[]): GridTrans[] {
    logger.debug('format grid list');

    if (gridRecordList == null) {
      const empty: any = {};
      return empty;
    }

    try {
      let outputGridList: GridTrans[] = [];
      if (gridRecordList != null) {
        outputGridList = gridRecordList.map(grid => formatGrid(grid));
      }
      return outputGridList;
    } catch (e) {
      logger.error(
        'Fail to prepare output grid list , reason: %o ',
        e.message
      );
      throw e;
    }
  }

  function formatSuccess(payload: any, message: string = null): object {
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
        const result: GridTrans[] = formatGridList(gridRecordList);
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
        gridId: Joi.number().allow(null),
        name: Joi.string().required()
      })
    }),
    async (req: Request, res: Response, next: NextFunction) => {
      logger.debug('Calling addGrid endpoint');

      try {
        const input: GridTrans = req.body;
        const gridRecord: Grid = await gridService.addGrid(input);
        const result: GridTrans = formatGrid(gridRecord);
        return res.status(201).json(formatSuccess(result));
      } catch (e) {
        logger.error('🔥 error: %o', e);
        return next(e);
      }
    }
  );

  route.put(
    '/:gridId',
    celebrate({
      body: Joi.object({
        spaceId: Joi.number().required(),
        gridId: Joi.number().required(),
        name: Joi.string().required()
      })
    }),
    async (req: Request, res: Response, next: NextFunction) => {
      logger.debug('Calling updateGrid endpoint');

      try {
        const input: GridTrans = req.body;
        input.gridId = parseInt(req.params.gridId, 10);
        const updResult: Grid = await gridService.updateGrid(input);
        const result: GridTrans = formatGrid(updResult);
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
        const result: GridTrans = formatGrid(gridRecord);
        return res.status(200).json(formatSuccess(result));
      } catch (e) {
        logger.error('🔥 error: %o', e);
        return next(e);
      }
    }
  );
};
