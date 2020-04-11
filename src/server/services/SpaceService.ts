import { Sequelize, Repository } from 'sequelize-typescript';
import { Service, Container } from 'typedi';
import config from '../config';
import SpaceTrans from '../interfaces/SpaceTrans';
import * as fileUtil from '../util/fileUtil';
import winston from 'winston';

//test for postgresql and sequelize
import Space from '../models/Space'

@Service()
export default class SpaceService {
  private logger:winston.Logger;
  private spaceRepo:Repository<Space>;
  constructor() {  
    this.logger = Container.get<winston.Logger>('logger');
    this.spaceRepo = Container.get<Sequelize>('sequelize').getRepository<Space>(Space);
  }

  public async getSpaceByUserId(userId: number): Promise<Space[]> {
    try{
      const spaceRecordList = await this.spaceRepo.findAll({
        where:{userId: userId},
        order: [
          ['spaceId', 'ASC'],
        ]
      });
      return spaceRecordList;
    } catch (e) {
      this.logger.error('Fail to get space list, reason: %o ', e.message);
      throw e;
    }
  }

  public async getSpaceById(spaceId: number): Promise<Space> {
    try{
      const spaceRecord = await this.spaceRepo.findOne({where: {spaceId: spaceId}});
      return spaceRecord;
    } catch (e) {
      this.logger.error('Fail to get space, reason: %o ', e.message);
      throw e;
    }
  }


  public async addSpace(spaceTrans: SpaceTrans): Promise<Space> {
    try {
      this.logger.debug('add space record');

      //move file to new path
      if(spaceTrans.imgPath!=null){
        const newFilePath = fileUtil.moveFileToPath(spaceTrans.imgPath, config.fileUpload.imgSpacePath);
        spaceTrans.imgPath = newFilePath;
      };

      const spaceRecord = await this.spaceRepo.create(spaceTrans);

      if (!spaceRecord) {
        this.logger.error('Fail to create space');
        throw new Error('Space cannot be created');
      }

      return spaceRecord;
    } catch (e) {
      this.logger.error('Fail to add space, reason: %o ', e.message);
      throw e;
    }
  }

  public async updateSpace(spaceTrans: SpaceTrans): Promise<Space> {
    try {
      const filter = {
        where: {spaceId:spaceTrans.spaceId}
      }

      this.logger.debug('update space record, spaceId: %o', spaceTrans.spaceId);
      const spaceRecord = await this.spaceRepo.findOne(filter);

      if (!spaceRecord) {
        this.logger.error('Fail to find space, spaceId %o ', spaceTrans.spaceId);
        throw new Error('Space not found');
      }

      //handle image file
      if(spaceTrans.imgPath!=null){
        //if new image file is uploaded
        //move file to new path
        const newFilePath = fileUtil.moveFileToPath(spaceTrans.imgPath, config.fileUpload.imgSpacePath);
        spaceTrans.imgPath = newFilePath;
      }else{
        //no new image uploaded
        //copy image path from existing
        spaceTrans.imgPath = spaceRecord.imgPath;
      }

      const update = {
        name: spaceTrans.name,
        colorCode: spaceTrans.colorCode,
        imgPath: spaceTrans.imgPath,
        tags: spaceTrans.tags,
        location: spaceTrans.location,
        sizeUnit : spaceTrans.sizeUnit,
        sizeWidth : spaceTrans.sizeWidth,
        sizeHeight : spaceTrans.sizeHeight,
        sizeDepth : spaceTrans.sizeDepth,
        drawerCount : spaceTrans.drawerCount,
      };

      //update record
      const options = {
        where: {spaceId:spaceTrans.spaceId},
        returning: true,
        plain: true
      };

      let updResult:any = await this.spaceRepo.update(update, options);

      if (!updResult) {
        this.logger.error('Fail to update space');
        throw new Error('Space cannot be updated');
      }

      //remove images between new and old is different
      if (updResult && spaceTrans.imgPath !== spaceRecord.imgPath) {
        fileUtil.clearUploadFile(spaceRecord.imgPath);
      }
      return updResult[1];
    } catch (e) {
      this.logger.error('Fail to update space, spaceId: %o, reason: %o ', spaceTrans.spaceId, e.message);
      throw e;
    }
  }

  public async deleteSpace(spaceId: number): Promise<Space> {
    try {
      this.logger.debug('delete space record, spaceId: %o', spaceId);
      const spaceRecord = await this.spaceRepo.findOne({where: {spaceId: spaceId}});

      if (!spaceRecord) {
        this.logger.error('Fail to find space, spaceId %o ', spaceId);
        throw new Error('Space not found');
      }

      const options = {
        where: {spaceId:spaceId},
        limit: 1,
      };

      
      let delOper = await this.spaceRepo.destroy(options);

      if (delOper) {
        if (spaceRecord.imgPath != null) {
          fileUtil.clearUploadFile(spaceRecord.imgPath);
        }
      }
      return spaceRecord;
    } catch (e) {
      this.logger.error('Fail to delete space, spaceId: %o, reason: %o ', spaceId, e.message);
      throw e;
    }
  }

  
  public async deleteSpaceImage(spaceId: number): Promise<boolean> {
    let result: boolean = false;
    try {
      const filter = { spaceId: spaceId };
      const update = { imgPath: null };

      this.logger.debug('delete space image, spaceId %o', spaceId);
      const spaceRecord = await this.spaceRepo.findOne({where: {spaceId: spaceId}});

      if (!spaceRecord) {
        this.logger.error('Fail to find space, spaceId %o ', spaceId);
        throw new Error('Space not found, %o');
      }

      if (spaceRecord.imgPath == null) {
        this.logger.error('Fail to find space image, spaceId %o ', spaceId);
        throw new Error('Space image not found');
      }

      //update record
      const options = {
        where: {spaceId:spaceId},
      };

      let updResult:any = await this.spaceRepo.update(update, options);

      if (!updResult) {
        this.logger.error('Fail to update space image to null');
        throw new Error('Space image cannot be updated to null');
      }

      //remove old img 
      result = fileUtil.clearUploadFile(spaceRecord.imgPath);

      return result;
    } catch (e) {
      this.logger.error('Fail to delete space image, spaceId: %o, reason: %o ', spaceId, e.message);
      throw e;
    }
  }

}
