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
import {Item as ItemModelCont } from '../models-seq/Item'
import {Space as SpaceModelCont } from '../models-seq/Space'

@Service()
export default class ItemService {
  private logger:winston.Logger;
  private itemModel:Model<IItem & Document>;
  constructor(
    // @Inject('itemModel') private itemModel: Model<IItem & Document>,
    // @Inject('logger') privte logger:winston.Logger;
    // @EventDispatcher() private eventDispatcher: EventDispatcherInterface,
  ) {  
    this.logger = Container.get<winston.Logger>('logger');
    this.itemModel = Container.get<Model<IItem & Document>>('itemModel');
  }

  public async getItemById(itemId: number): Promise<{ itemRecord: IItem & Document}> {
    try{
      const itemRecord = await this.itemModel.findOne({ 'itemId': itemId });
      
      const result = await ItemModelCont.findOne({where: {itemId: itemId}});
      console.log('GET itemRecord '+JSON.stringify(result));

      return {itemRecord};
    } catch (e) {
      this.logger.error('Fail to add item, reason: %o ', e.message);
      throw e;
    }
  }


  public async addItem(itemInputDTO: IItemInputDTO): Promise<{ itemRecord: IItem & Document }> {
    try {
      this.logger.debug('add item record');

      // //move file to new path
      // if(itemInputDTO.imgPath!=null){
      //   const newFilePath = fileUtil.moveFileToPath(itemInputDTO.imgPath, config.fileUpload.imgItemPath);
      //   itemInputDTO.imgPath = newFilePath;
      // };

      // //set reminder complete
      // if (itemInputDTO.reminderDtm != null) {
      //   //assume reminder not yet complete
      //   itemInputDTO.reminderComplete = false;
      // } else {
      //   itemInputDTO.reminderComplete = null;
      // }
      
      const itemRecord = await this.itemModel.create({
        ...itemInputDTO,
      });

      if (!itemRecord) {
        this.logger.error('Fail to create item');
        throw new Error('Item cannot be created');
      }
      // this.eventDispatcher.dispatch(events.user.signUp, { user: itemRecord });

      let data = {};
      for (let [key, value] of Object.entries(itemInputDTO)) {
        data[key] = value
      }

      // const space = await SpaceModelCont.create({
      //   "spaceId": null,
      //   "name": "Space 1",
      //   "colorCode": "yellow",
      //   "imgPath": null,
      //   "tags": "business",
      //   "location": "clothes"
      // });
      // console.log('space  '+JSON.stringify(space));

      const item = await ItemModelCont.create(
        data
      //   {
      //     "itemId": null,
      //     "spaceId": 1,
      //     "name": "item 4",
      //     "tags": "business",
      //     "category": "clothes",
      //     "colorCode": "yellow",
      //     "description": "Testing 123",
      //     "imgPath": null,
      //     "reminderDtm": "2020-03-27T03:17:09",
      //     "reminderComplete": null
      // }
      );
      console.log('item  '+JSON.stringify(item));
      
      return { itemRecord };
    } catch (e) {
      this.logger.error('Fail to add item, reason: %o ', e.message);
      throw e;
    }
  }


  //--------------------------------------------------------------------

  public async getItemBySpaceId(spaceId: number): Promise<{ itemRecordList: (IItem& Document)[] }> {
    const itemRecordList = await this.itemModel.find({ 'spaceId': spaceId });
    return { itemRecordList };
  }

  // public async getItemById(itemId: number): Promise<{ itemRecord: IItem & Document}> {
  //   try{
  //     const itemRecord = await this.itemModel.findOne({ 'itemId': itemId });
  //     return { itemRecord };
  //   } catch (e) {
  //     this.logger.error('Fail to add item, reason: %o ', e.message);
  //     throw e;
  //   }
  // }


  // public async addItem(itemInputDTO: IItemInputDTO): Promise<{ itemRecord: IItem & Document }> {
  //   try {
  //     this.logger.debug('add item record');

  //     //move file to new path
  //     if(itemInputDTO.imgPath!=null){
  //       const newFilePath = fileUtil.moveFileToPath(itemInputDTO.imgPath, config.fileUpload.imgItemPath);
  //       itemInputDTO.imgPath = newFilePath;
  //     };

  //     //set reminder complete
  //     if (itemInputDTO.reminderDtm != null) {
  //       //assume reminder not yet complete
  //       itemInputDTO.reminderComplete = false;
  //     } else {
  //       itemInputDTO.reminderComplete = null;
  //     }
      
  //     const itemRecord = await this.itemModel.create({
  //       ...itemInputDTO,
  //     });

  //     if (!itemRecord) {
  //       this.logger.error('Fail to create item');
  //       throw new Error('Item cannot be created');
  //     }

  //     // this.eventDispatcher.dispatch(events.user.signUp, { user: itemRecord });
  //     return { itemRecord };
  //   } catch (e) {
  //     this.logger.error('Fail to add item, reason: %o ', e.message);
  //     throw e;
  //   }
  // }

  public async updateItem(itemInputDTO: IItemInputDTO): Promise<{ updResult: IItem & Document }> {
    try {
      const filter = { itemId: itemInputDTO.itemId };

      this.logger.debug('update item record, itemId: %o', itemInputDTO.itemId);
      const itemRecord = await this.itemModel.findOne(filter).select(['imgPath', 'reminderDtm', 'reminderComplete']);

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
      let updResult = await this.itemModel.findOneAndUpdate(filter, update, {
        new: true,
        upsert: false
      });

      //remove images between new and old is different
      if (updResult && itemInputDTO.imgPath !== itemRecord.imgPath) {
        fileUtil.clearUploadFile(itemRecord.imgPath);
      }
      return { updResult };
    } catch (e) {
      this.logger.error('Fail to delete item, itemId: %o, reason: %o ', itemInputDTO.itemId, e.message);
      throw e;
    }
  }

  public async deleteItem(itemId: number): Promise<{ itemRecord: IItem & Document  }> {
    try {
      this.logger.debug('delete item record, itemId: %o', itemId);
      const itemRecord = await this.itemModel.findOne({ 'itemId': itemId });

      if (!itemRecord) {
        this.logger.error('Fail to find item, itemId %o ', itemId);
        throw new Error('Item not found');
      }

      let delOper = await itemRecord.remove();
      if (delOper.$isDeleted) {
        if (itemRecord.imgPath != null) {
          fileUtil.clearUploadFile(itemRecord.imgPath);
        }
      }
      return { itemRecord };
    } catch (e) {
      this.logger.error('Fail to delete item, itemId: %o, reason: %o ', itemId, e.message);
      throw e;
    }
  }

  public async deleteItemImage(itemId: number): Promise<{ result: boolean }> {
    let result: boolean = false;
    try {
      const filter = { itemId: itemId };
      const update = { imgPath: null };

      this.logger.debug('delete item image, itemId %o', itemId);
      const itemRecord = await this.itemModel.findOne(filter).select(['imgPath']);

      if (!itemRecord) {
        this.logger.error('Fail to find item, itemId %o ', itemId);
        throw new Error('Item not found, %o');
      }
      if (itemRecord.imgPath == null) {
        this.logger.error('Fail to find item image, itemId %o ', itemId);
        throw new Error('Item image not found');
      }

      //update record
      const updResult = await this.itemModel.findOneAndUpdate(filter, update, {
        new: true,
        upsert: false
      });

      //remove old img 
      if (updResult) {
        result = fileUtil.clearUploadFile(itemRecord.imgPath);
      }

      return { result };
    } catch (e) {
      this.logger.error('Fail to delete item image, itemId: %o, reason: %o ', itemId, e.message);
      throw e;
    }
  }

}
