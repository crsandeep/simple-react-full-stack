import { Service, Inject, Container } from 'typedi';
import config from '../config';
import { IItem, IItemInputDTO } from '../interfaces/IItem';
import { Document, Model } from 'mongoose';
// import { EventDispatcher, EventDispatcherInterface } from '../decorators/eventDispatcher';
// import events from '../subscribers/events';
import moment from 'moment';
import * as fileUtil from '../util/fileUtil';
import winston from 'winston';

//test for postgresql and sequelize
import Item  from '../models-seq/Item'
import Space from '../models-seq/Space'

@Service()
export default class ItemService {
  private logger:winston.Logger;
  private itemModel:Model<IItem & Document>;
  
  constructor() {  
    this.logger = Container.get<winston.Logger>('logger');
    this.itemModel = Container.get<Model<IItem & Document>>('itemModel');
  }

  public async getItemBySpaceId2(spaceId: number): Promise<Item[]> {
    const itemRecordList = await Item.findAll({
      where:{spaceId: spaceId},
      order: [
        ['itemId', 'ASC'],
      ]
    });
    return itemRecordList;
  }

  public async getItemById2(itemId: number): Promise<Item> {
    try{
      const itemRecord = await Item.findOne({where: {itemId: itemId}});
      return itemRecord;
    } catch (e) {
      this.logger.error('Fail to add item, reason: %o ', e.message);
      throw e;
    }
  }


  public async addItem2(itemInputDTO: IItemInputDTO): Promise<Item> {
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
      
      const itemRecord = await Item.create(itemInputDTO);

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

  public async updateItem2(itemInputDTO: IItemInputDTO): Promise<Item> {
    try {
      const filter = {
        where: {itemId:itemInputDTO.itemId}
      }

      this.logger.debug('update item record, itemId: %o', itemInputDTO.itemId);
      const itemRecord = await Item.findOne(filter);

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

      let updResult:any = await Item.update(update, options);

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
      this.logger.error('Fail to delete item, itemId: %o, reason: %o ', itemInputDTO.itemId, e.message);
      throw e;
    }
  }

  public async deleteItem2(itemId: number): Promise<Item> {
    try {
      this.logger.debug('delete item record, itemId: %o', itemId);
      const itemRecord = await Item.findOne({where: {itemId: itemId}});

      if (!itemRecord) {
        this.logger.error('Fail to find item, itemId %o ', itemId);
        throw new Error('Item not found');
      }

      const options = {
        where: {itemId:itemId},
        limit: 1,
      };

      
      let delOper = await Item.destroy(options);

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

  
  public async deleteItemImage2(itemId: number): Promise<boolean> {
    let result: boolean = false;
    try {
      const filter = { itemId: itemId };
      const update = { imgPath: null };

      this.logger.debug('delete item image, itemId %o', itemId);
      const itemRecord = await Item.findOne({where: {itemId: itemId}});

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

      let updResult:any = await Item.update(update, options);

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
