import { Sequelize, Repository } from 'sequelize-typescript';
import { Service, Inject, Container } from 'typedi';
import config from '../config';
import ItemTrans from '../interfaces/ItemTrans';
// import { EventDispatcher, EventDispatcherInterface } from '../decorators/eventDispatcher';
// import events from '../subscribers/events';
import moment from 'moment';
import * as fileUtil from '../util/fileUtil';
import winston from 'winston';

//test for postgresql and sequelize
import Item  from '../models/Item'
import Space from '../models/Space'

@Service()
export default class ItemService {
  private logger:winston.Logger;
  private itemRepo:Repository<Item>;
  constructor() {  
    this.logger = Container.get<winston.Logger>('logger');
    this.itemRepo = Container.get<Sequelize>('sequelize').getRepository<Item>(Item);
  }

  public async getItemBySpaceId(spaceId: number): Promise<Item[]> {
    try{
      const itemRecordList = await this.itemRepo.findAll({
        where:{spaceId: spaceId},
        order: [
          ['itemId', 'ASC'],
        ]
      });
      return itemRecordList;
    } catch (e) {
      this.logger.error('Fail to get item list, reason: %o ', e.message);
      throw e;
    }
  }

  public async getItemById(itemId: number): Promise<Item> {
    try{
      const itemRecord = await this.itemRepo.findOne({where: {itemId: itemId}});
      return itemRecord;
    } catch (e) {
      this.logger.error('Fail to get item, reason: %o ', e.message);
      throw e;
    }
  }


  public async addItem(itemInputDTO: ItemTrans): Promise<Item> {
    try {
      this.logger.debug('add item record');

      //move file to new path
      if(itemInputDTO.imgPath!=null){
        const newFilePath = fileUtil.moveFileToPath(itemInputDTO.imgPath, config.fileUpload.imgItemPath);
        itemInputDTO.imgPath = newFilePath;
      };

      //set reminder complete
      if (itemInputDTO.reminderDtm != null) {
        //assume reminder not yet complete
        itemInputDTO.reminderComplete = false;
      } else {
        itemInputDTO.reminderComplete = null;
      }
      
      const itemRecord = await this.itemRepo.create(itemInputDTO);

      if (!itemRecord) {
        this.logger.error('Fail to create item');
        throw new Error('Item cannot be created');
      }
      // this.eventDispatcher.dispatch(events.user.signUp, { user: itemRecord });

      return itemRecord;
    } catch (e) {
      this.logger.error('Fail to add item, reason: %o ', e.message);
      throw e;
    }
  }

  public async updateItem(itemInputDTO: ItemTrans): Promise<Item> {
    try {
      const filter = {
        where: {itemId:itemInputDTO.itemId}
      }

      this.logger.debug('update item record, itemId: %o', itemInputDTO.itemId);
      const itemRecord = await this.itemRepo.findOne(filter);

      if (!itemRecord) {
        this.logger.error('Fail to find item, itemId %o ', itemInputDTO.itemId);
        throw new Error('Item not found');
      }

      //prepare reminder completed
      if (itemInputDTO.reminderDtm != null) {
        //assume reminder not yet complete
        itemInputDTO.reminderComplete = false;

        //check if remind dtm has not change
        if (itemRecord.reminderDtm != null) {
          const oldRemind = moment(itemRecord.reminderDtm);
          const newRemind = moment(itemInputDTO.reminderDtm);
          if (oldRemind.diff(newRemind, 'seconds', true) === 0) {
            //no change
            itemInputDTO.reminderComplete = itemInputDTO.reminderComplete;
          }
        }
      } else {
        itemInputDTO.reminderComplete = null;
      }

      //handle image file
      if(itemInputDTO.imgPath!=null){
        //if new image file is uploaded
        //move file to new path
        const newFilePath = fileUtil.moveFileToPath(itemInputDTO.imgPath, config.fileUpload.imgItemPath);
        itemInputDTO.imgPath = newFilePath;
      }else{
        //no new image uploaded
        //copy image path from existing
        itemInputDTO.imgPath = itemRecord.imgPath;
      }

      const update = {
        name: itemInputDTO.name,
        colorCode: itemInputDTO.colorCode,
        imgPath: itemInputDTO.imgPath,
        tags: itemInputDTO.tags,
        description: itemInputDTO.description,
        category: itemInputDTO.category,
        reminderDtm: itemInputDTO.reminderDtm,
        reminderComplete: itemInputDTO.reminderComplete,
      };

      //update record
      const options = {
        where: {itemId:itemInputDTO.itemId},
        returning: true,
        plain: true
      };

      let updResult:any = await this.itemRepo.update(update, options);

      if (!updResult) {
        this.logger.error('Fail to update item');
        throw new Error('Item cannot be updated');
      }

      //remove images between new and old is different
      if (updResult && itemInputDTO.imgPath !== itemRecord.imgPath) {
        fileUtil.clearUploadFile(itemRecord.imgPath);
      }
      return updResult[1];
    } catch (e) {
      this.logger.error('Fail to update item, itemId: %o, reason: %o ', itemInputDTO.itemId, e.message);
      throw e;
    }
  }

  public async deleteItem(itemId: number): Promise<Item> {
    try {
      this.logger.debug('delete item record, itemId: %o', itemId);
      const itemRecord = await this.itemRepo.findOne({where: {itemId: itemId}});

      if (!itemRecord) {
        this.logger.error('Fail to find item, itemId %o ', itemId);
        throw new Error('Item not found');
      }

      const options = {
        where: {itemId:itemId},
        limit: 1,
      };

      
      let delOper = await this.itemRepo.destroy(options);

      if (delOper) {
        if (itemRecord.imgPath != null) {
          fileUtil.clearUploadFile(itemRecord.imgPath);
        }
      }
      return itemRecord;
    } catch (e) {
      this.logger.error('Fail to delete item, itemId: %o, reason: %o ', itemId, e.message);
      throw e;
    }
  }

  
  public async deleteItemImage(itemId: number): Promise<boolean> {
    let result: boolean = false;
    try {
      const filter = { itemId: itemId };
      const update = { imgPath: null };

      this.logger.debug('delete item image, itemId %o', itemId);
      const itemRecord = await this.itemRepo.findOne({where: {itemId: itemId}});

      if (!itemRecord) {
        this.logger.error('Fail to find item, itemId %o ', itemId);
        throw new Error('Item not found, %o');
      }

      if (itemRecord.imgPath == null) {
        this.logger.error('Fail to find item image, itemId %o ', itemId);
        throw new Error('Item image not found');
      }

      //update record
      const options = {
        where: {itemId:itemId},
      };

      let updResult:any = await this.itemRepo.update(update, options);

      if (!updResult) {
        this.logger.error('Fail to update item image to null');
        throw new Error('Item image cannot be updated to null');
      }

      //remove old img 
      result = fileUtil.clearUploadFile(itemRecord.imgPath);

      return result;
    } catch (e) {
      this.logger.error('Fail to delete item image, itemId: %o, reason: %o ', itemId, e.message);
      throw e;
    }
  }

}
