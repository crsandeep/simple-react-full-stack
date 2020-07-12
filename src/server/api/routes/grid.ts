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


  function formatSuccess(payload: any, message: string = null): object {
    // eslint-disable-next-line object-shorthand
    return { isSuccess: true, payload, message };
  }

  function formatGrid(gridRecord: Grid): GridTrans {
    const outputGrid:any = {};

    const excludeAttr:string[] = ['creationDate',
      'updatedOn',
      'space', // special handle
      'items'
    ];

    if (gridRecord == null) {
      return outputGrid;
    }

    try {
      // copy value from db object to transmission object
      // eslint-disable-next-line dot-notation
      for (const [key, value] of Object.entries(gridRecord['dataValues'])) {
        if (excludeAttr.indexOf(key) < 0) {
          // non exclude field
          outputGrid[key] = value;
        }
      }

      // special fill from db
      // copy img path
      if (gridRecord.space != null && gridRecord.space.imgPath != null) {
        outputGrid.imgPath = gridRecord.space.imgPath.replace(config.publicFolder, '');
      } else {
        outputGrid.imgPath = null;
      }

      // prepare items tags list
      let tagList: string[] = null;
      let catList: string[] = null;
      let itemCount:number = null;
      let tempArr: string[] = null;

      if (gridRecord.items != null) {
        itemCount = gridRecord.items.length;
        tagList = [];
        catList = [];

        for (const item of gridRecord.items) {
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

          if (item.category != null) {
            if (catList.indexOf(item.category) < 0) {
              catList.push(item.category);
            }
          }
        }
      }

      // copy other fields
      outputGrid.layout = JSON.parse(gridRecord.layout);
      outputGrid.itemCats = catList;
      outputGrid.itemTags = tagList;
      outputGrid.itemCount = itemCount;

      return outputGrid;
    } catch (e) {
      logger.error(
        'Fail to prepare output grid list , reason: %o ',
        e.message
      );
      throw e;
    }
  }

  function formatGridList(gridRecordList: (Grid)[]): GridTrans[] {
    if (gridRecordList == null) {
      const empty:any = {};
      return empty;
    }

    try {
      const outputList: GridTrans[] = [];
      if (gridRecordList != null) {
        for (const grid of gridRecordList) {
          outputList.push(formatGrid(grid));
        }
      }
      return outputList;
    } catch (e) {
      logger.error('Fail to prepare output grid list , reason: %o ', e.message);
      throw e;
    }
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
        grids: Joi.array().items(Joi.object({
          spaceId: Joi.number().required(),
          gridId: Joi.number().allow(null),
          layout: Joi.object({
            x: Joi.number().required(),
            y: Joi.number().required(),
            w: Joi.number().required(),
            h: Joi.number().required(),
            i: Joi.string().required(),
            minW: Joi.number()
          })
        }))
      })
    }),
    async (req: Request, res: Response, next: NextFunction) => {
      logger.debug('Calling addGrid endpoint');

      try {
        const input: GridTrans[] = req.body.grids;
        const gridRecord: Grid[] = await gridService.saveGrid(input);
        const result: GridTrans[] = formatGridList(gridRecord);
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
        const result: GridTrans = formatGrid(gridRecord); // pass in as list
        return res.status(200).json(formatSuccess(result));
      } catch (e) {
        logger.error('🔥 error: %o', e);
        return next(e);
      }
    }
  );
};
