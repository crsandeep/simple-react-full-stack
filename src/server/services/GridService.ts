import { Sequelize, Repository } from 'sequelize-typescript';
import { Service, Container } from 'typedi';
import GridTrans from '../interfaces/GridTrans';
import winston from 'winston';

//test for postgresql and sequelize
import Grid from '../models/Grid'

@Service()
export default class GridService {
  private logger:winston.Logger;
  private gridRepo:Repository<Grid>;
  constructor() {  
    this.logger = Container.get<winston.Logger>('logger');
    this.gridRepo = Container.get<Sequelize>('sequelize').getRepository<Grid>(Grid);
  }

  public async getGridBySpaceId(spaceId: number): Promise<Grid[]> {
    try{
      const gridRecordList = await this.gridRepo.findAll({
        where:{spaceId: spaceId},
        order: [
          ['gridId', 'ASC'],
        ]
      });
      return gridRecordList;
    } catch (e) {
      this.logger.error('Fail to get grid list, reason: %o ', e.message);
      throw e;
    }
  }

  public async addGrid(gridTrans: GridTrans): Promise<Grid> {
    try {
      this.logger.debug('add grid record');

      const gridRecord = await this.gridRepo.create(gridTrans);

      if (!gridRecord) {
        this.logger.error('Fail to create grid');
        throw new Error('Grid cannot be created');
      }

      return gridRecord;
    } catch (e) {
      this.logger.error('Fail to add grid, reason: %o ', e.message);
      throw e;
    }
  }

  public async updateGrid(gridTrans: GridTrans): Promise<Grid> {
    try {
      const filter = {
        where: {gridId:gridTrans.gridId}
      }

      this.logger.debug('update grid record, gridId: %o', gridTrans.gridId);
      const gridRecord = await this.gridRepo.findOne(filter);

      if (!gridRecord) {
        this.logger.error('Fail to find grid, gridId %o ', gridTrans.gridId);
        throw new Error('Grid not found');
      }

      const update = {
        name: gridTrans.name,
      };

      //update record
      const options = {
        where: {gridId:gridTrans.gridId},
        returning: true,
        plain: true
      };

      let updResult:any = await this.gridRepo.update(update, options);

      if (!updResult) {
        this.logger.error('Fail to update grid');
        throw new Error('Grid cannot be updated');
      }

      return updResult[1];
    } catch (e) {
      this.logger.error('Fail to update grid, gridId: %o, reason: %o ', gridTrans.gridId, e.message);
      throw e;
    }
  }

  public async deleteGrid(gridId: number): Promise<Grid> {
    try {
      this.logger.debug('delete grid record, gridId: %o', gridId);
      const gridRecord = await this.gridRepo.findOne({where: {gridId: gridId}});

      if (!gridRecord) {
        this.logger.error('Fail to find grid, gridId %o ', gridId);
        throw new Error('Grid not found');
      }

      const options = {
        where: {gridId:gridId},
        limit: 1,
      };

      
      let delOper = await this.gridRepo.destroy(options);

      if (!delOper) {
        this.logger.error('Fail to delete grid, gridId %o ', gridId);
        throw new Error('Fail to delete grid');
      }

      return gridRecord;
    } catch (e) {
      this.logger.error('Fail to delete grid, gridId: %o, reason: %o ', gridId, e.message);
      throw e;
    }
  }
}
