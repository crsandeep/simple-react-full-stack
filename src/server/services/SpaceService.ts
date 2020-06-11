import { Sequelize, Repository } from 'sequelize-typescript';
import { Service, Container } from 'typedi';
import winston from 'winston';
import config from '../config';
import SpaceTrans from '../interfaces/SpaceTrans';
import * as fileUtil from '../util/fileUtil';

import Grid from '../models/Grid';
import Item from '../models/Item';
import Space from '../models/Space';
import OperationResult from '../util/operationResult';
import MessageCd from '../Constants/MessageCd';

@Service()
export default class SpaceService {
  private logger:winston.Logger;

  private spaceRepo:Repository<Space>;

  private gridRepo: Repository<Grid>;

  private itemRepo: Repository<Item>;

  constructor() {
    this.logger = Container.get<winston.Logger>('logger');

    this.gridRepo = Container.get<Sequelize>('sequelize').getRepository<Grid>(Grid);
    this.itemRepo = Container.get<Sequelize>('sequelize').getRepository<Item>(Item);
    this.spaceRepo = Container.get<Sequelize>('sequelize').getRepository<Space>(Space);
  }

  public async getSpaceByUserId(userId: number): Promise<OperationResult> {
    try {
      this.logger.debug('getSpaceByUserId');
      const operResult = new OperationResult();
      const spaceRecordList = await this.spaceRepo.findAll({
        where: { userId },
        include: [{
          model: this.gridRepo,
          as: 'grids',
          attributes: ['gridId'],
          include: [{
            model: this.itemRepo,
            as: 'items',
            attributes: ['itemId', 'tags']
          }]
        }],
        order: [
          ['spaceId', 'ASC']
        ]
      });

      operResult.setSuccess(spaceRecordList);
      return operResult;
    } catch (e) {
      this.logger.error('Fail to get space list, reason: %o ', e.message);
      throw e;
    }
  }

  public async getSpaceById(spaceId: number): Promise<OperationResult> {
    try {
      this.logger.debug('getSpaceById');
      const operResult = new OperationResult();
      const spaceRecord = await this.spaceRepo.findOne({ where: { spaceId } });
      operResult.setSuccess(spaceRecord);
      return operResult;
    } catch (e) {
      this.logger.error('Fail to get space, reason: %o ', e.message);
      throw e;
    }
  }


  public async addSpace(spaceTrans: SpaceTrans): Promise<OperationResult> {
    try {
      this.logger.debug('addSpace');
      const operResult = new OperationResult();

      // move file to new path
      if (spaceTrans.imgPath != null) {
        const newFilePath = fileUtil.moveFileToPath(spaceTrans.imgPath, config.fileUpload.imgSpacePath);
        spaceTrans.imgPath = newFilePath;
      }

      const spaceRecord = await this.spaceRepo.create(spaceTrans);

      if (!spaceRecord) {
        this.logger.error('Fail to create space');
        operResult.setFail(MessageCd.SPACE_CREATE_SPACE_FAILED_UNKNOWN, 'Fail to create space');
        return operResult;
      }

      operResult.setSuccess(spaceRecord);
      return operResult;
    } catch (e) {
      this.logger.error('Fail to add space, reason: %o ', e.message);
      throw e;
    }
  }

  public async updateSpace(spaceTrans: SpaceTrans): Promise<OperationResult> {
    try {
      this.logger.debug('updateSpace');
      const operResult = new OperationResult();

      const filter = {
        where: { spaceId: spaceTrans.spaceId }
      };

      this.logger.debug('update space record, spaceId: %o', spaceTrans.spaceId);
      const spaceRecord = await this.spaceRepo.findOne(filter);

      if (!spaceRecord) {
        this.logger.error('Fail to find space, spaceId %o ', spaceTrans.spaceId);
        operResult.setFail(MessageCd.SPACE_UPDATE_SPACE_FAILED_NOT_FOUND, 'Fail to find space');
        return operResult;
      }

      // handle image file
      if (spaceTrans.imgPath != null) {
        // if new image file is uploaded
        // move file to new path
        const newFilePath = fileUtil.moveFileToPath(spaceTrans.imgPath, config.fileUpload.imgSpacePath);
        spaceTrans.imgPath = newFilePath;
      } else {
        // no new image uploaded
        // copy image path from existing
        spaceTrans.imgPath = spaceRecord.imgPath;
      }

      const update = {
        name: spaceTrans.name,
        imgPath: spaceTrans.imgPath,
        location: spaceTrans.location
      };

      // update record
      const options = {
        where: { spaceId: spaceTrans.spaceId },
        returning: true,
        plain: true
      };

      const updResult:any = await this.spaceRepo.update(update, options);

      if (!updResult) {
        this.logger.error('Fail to update space');
        operResult.setFail(MessageCd.SPACE_UPDATE_SPACE_FAILED_UNKNOWN, 'Fail to update space');
        return operResult;
      }

      // remove images between new and old is different
      if (updResult && spaceTrans.imgPath !== spaceRecord.imgPath) {
        fileUtil.clearUploadFile(spaceRecord.imgPath);
      }
      operResult.setSuccess(updResult[1]);
      return operResult;
    } catch (e) {
      this.logger.error('Fail to update space, spaceId: %o, reason: %o ', spaceTrans.spaceId, e.message);
      throw e;
    }
  }

  public async deleteSpace(spaceId: number): Promise<OperationResult> {
    try {
      this.logger.debug('delete space record, spaceId: %o', spaceId);

      const operResult = new OperationResult();
      const spaceRecord = await this.spaceRepo.findOne({ where: { spaceId } });

      if (!spaceRecord) {
        this.logger.error('Fail to find space, spaceId %o ', spaceId);
        operResult.setFail(MessageCd.SPACE_DELETE_SPACE_FAILED_NOT_FOUND, 'Fail to find space');
        return operResult;
      }

      const options = {
        where: { spaceId },
        limit: 1
      };

      const delOper = await this.spaceRepo.destroy(options);

      if (delOper) {
        if (spaceRecord.imgPath != null) {
          fileUtil.clearUploadFile(spaceRecord.imgPath);
        }
      } else {
        this.logger.error('Fail to delete space, spaceId %o ', spaceId);
        operResult.setFail(MessageCd.SPACE_DELETE_SPACE_FAILED_UNKNOWN, 'Fail to delete space');
        return operResult;
      }

      operResult.setSuccess(spaceRecord);
      return operResult;
    } catch (e) {
      this.logger.error('Fail to delete space, spaceId: %o, reason: %o ', spaceId, e.message);
      throw e;
    }
  }


  public async deleteSpaceImage(spaceId: number): Promise<OperationResult> {
    let result: boolean = false;
    try {
      this.logger.debug('deleteSpaceImage, spaceId: %o', spaceId);

      const operResult = new OperationResult();

      const update = { imgPath: null };

      this.logger.debug('delete space image, spaceId %o', spaceId);
      const spaceRecord = await this.spaceRepo.findOne({ where: { spaceId } });

      if (!spaceRecord) {
        this.logger.error('Fail to find space, spaceId %o ', spaceId);
        operResult.setFail(MessageCd.SPACE_UPDATE_SPACE_REMOVE_IMG_FAILED_NOT_FOUND, 'Fail to find space');
        return operResult;
      }

      // image already null, return directly
      if (spaceRecord.imgPath == null) {
        operResult.setSuccess(true);
        return operResult;
      }

      // update record
      const options = {
        where: { spaceId }
      };

      const updResult:any = await this.spaceRepo.update(update, options);

      if (!updResult) {
        this.logger.error('Fail to update space image to null');
        operResult.setFail(MessageCd.SPACE_UPDATE_SPACE_REMOVE_IMG_FAILED, 'Fail to clear space image');
        return operResult;
      }

      // remove old img
      result = fileUtil.clearUploadFile(spaceRecord.imgPath);

      operResult.setSuccess(result);
      return operResult;
    } catch (e) {
      this.logger.error('Fail to delete space image, spaceId: %o, reason: %o ', spaceId, e.message);
      throw e;
    }
  }
}
