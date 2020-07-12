import { Sequelize, Repository } from 'sequelize-typescript';

import { Service, Container } from 'typedi';

import winston from 'winston';
import GridTrans from '../interfaces/GridTrans';

// test for postgresql and sequelize

import Grid from '../models/Grid';
import Item from '../models/Item';
import Space from '../models/Space';

@Service()
export default class GridService {
  private logger: winston.Logger;

  private gridRepo: Repository<Grid>;

  private itemRepo: Repository<Item>;

  private spaceRepo: Repository<Space>;

  constructor() {
    this.logger = Container.get<winston.Logger>('logger');

    this.gridRepo = Container.get<Sequelize>('sequelize').getRepository<Grid>(Grid);
    this.itemRepo = Container.get<Sequelize>('sequelize').getRepository<Item>(Item);
    this.spaceRepo = Container.get<Sequelize>('sequelize').getRepository<Space>(Space);
  }

  public async getGridBySpaceId(spaceId: number): Promise<Grid[]> {
    try {
      // get assoicated item tags
      const gridRecordList = await this.gridRepo.findAll({
        where: { spaceId },
        include: [{
          model: this.itemRepo,
          as: 'items',
          attributes: ['itemId', 'tags', 'category']
        }, {
          model: this.spaceRepo,
          as: 'space',
          attributes: ['imgPath']
        }],
        order: [['gridId', 'ASC']]
      });

      return gridRecordList;
    } catch (e) {
      this.logger.error('Fail to get grid list, reason: %o ', e.message);

      throw e;
    }
  }

  public async saveGrid(gridTransList: GridTrans[]): Promise<Grid[]> {
    try {
      this.logger.debug('save grid record');

      let gridItem: any;
      let result = null;
      let idx: number;
      const gridList: Promise<Grid>[] = [];

      // add all grids to db
      for (const gridTrans of gridTransList) {
        // prepare grid by for each layout
        gridItem = {
          spaceId: gridTrans.spaceId,
          layout: gridTrans.layout,
          gridId: gridTrans.gridId
        };

        if (gridTrans.gridId === null) {
          // new grid
          result = this.addGrid(gridItem);
        } else {
          // existing grid
          result = this.updateGrid(gridItem);
        }

        if (!result) {
          this.logger.error('Fail to save grid');
          throw new Error('Grid cannot be saved');
        }

        // store as list for return
        gridList.push(result);
      }

      // wait for all complete
      await Promise.all(gridList);

      // instead of returing save/update result directly
      // return gridList by using select function to populate item tags
      return await this.getGridBySpaceId(gridTransList[0].spaceId);
    } catch (e) {
      this.logger.error('Fail to save grid, reason: %o ', e.message);

      throw e;
    }
  }

  public async addGrid(grid: any): Promise<Grid> {
    try {
      this.logger.debug('add grid record');

      if (grid.layout === null) {
        this.logger.error('Fail to create grid');
        throw new Error('Grid cannot be created');
      }

      const tempLayout = Object.assign({}, grid.layout); // copy json for later update i value
      grid.layout = JSON.stringify(grid.layout); // convert json to string for storing purpose

      const result = await this.gridRepo.create(grid);

      if (!result) {
        this.logger.error('Fail to create grid');
        throw new Error('Grid cannot be created');
      }

      // update grid id for new grid item
      tempLayout.i = `${result.gridId}`; // convert integer to string
      result.layout = tempLayout;
      const updResult = this.updateGrid(result);

      if (!updResult) {
        this.logger.error('Fail to update grid id in layout');
        throw new Error('Grid cannot be created');
      }

      return updResult;
    } catch (e) {
      this.logger.error('Fail to add grid, reason: %o ', e.message);

      throw e;
    }
  }

  public async updateGrid(grid: any): Promise<Grid> {
    try {
      const filter = {
        where: { gridId: grid.gridId }
      };

      this.logger.debug('update grid record, gridId: %o', grid.gridId);

      const gridRecord = await this.gridRepo.findOne(filter);

      if (!gridRecord) {
        this.logger.error('Fail to find grid, gridId %o ', grid.gridId);
        throw new Error('Grid not found');
      }

      const update = {
        layout: JSON.stringify(grid.layout) // convert json to string for storing purpose
      };

      // update record
      const options = {
        where: { gridId: grid.gridId },
        returning: true,
        plain: true
      };

      const updResult: any = await this.gridRepo.update(update, options);

      if (!updResult) {
        this.logger.error('Fail to update grid');

        throw new Error('Grid cannot be updated');
      }

      return updResult[1];
    } catch (e) {
      this.logger.error(
        'Fail to update grid, gridId: %o, reason: %o ',
        grid.gridId,
        e.message
      );

      throw e;
    }
  }

  public async deleteGrid(gridId: number): Promise<Grid> {
    try {
      this.logger.debug('delete grid record, gridId: %o', gridId);

      const gridRecord = await this.gridRepo.findOne({ where: { gridId } });

      if (!gridRecord) {
        this.logger.error('Fail to find grid, gridId %o ', gridId);

        throw new Error('Grid not found');
      }

      const options = {
        where: { gridId },
        limit: 1
      };

      const delOper = await this.gridRepo.destroy(options);

      if (!delOper) {
        this.logger.error('Fail to delete grid, gridId %o ', gridId);
        throw new Error('Fail to delete grid');
      }

      return gridRecord;
    } catch (e) {
      this.logger.error(
        'Fail to delete grid, gridId: %o, reason: %o ',
        gridId,
        e.message
      );

      throw e;
    }
  }
}
