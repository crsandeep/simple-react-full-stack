import { Service, Inject } from 'typedi';
import config from '../config';
import { IItem, IItemInputDTO } from '../interfaces/IItem';
import { Document, Model } from 'mongoose';
// import { EventDispatcher, EventDispatcherInterface } from '../decorators/eventDispatcher';
// import events from '../subscribers/events';
import moment from 'moment';
import * as fileUtil from '../util/fileUtil';

@Service()
export default class ItemService {
  constructor(
    @Inject('itemModel') private itemModel: Model<IItem & Document>,
    @Inject('logger') private logger,
    // @EventDispatcher() private eventDispatcher: EventDispatcherInterface,
  ) { }

  public async getItemBySpaceId(spaceId: number): Promise<{ result: IItem[] }> {
    const itemRecordList = await this.itemModel.find({ 'spaceId': spaceId });
    let result: any[] = [];

    if (itemRecordList != null) {
      itemRecordList.map((item) => {
        result.push(this.prepareOutputItem(item));
      });
    }
    return { result };
  }

  public async getItemById(itemId: number): Promise<{ result: IItem }> {
    const itemRecord = await this.itemModel.findOne({ 'itemId': itemId });
    let result: any = {};

    if (itemRecord) {
      result = this.prepareOutputItem(itemRecord);
    }

    return { result };
  }


  public async addItem(itemInputDTO: IItemInputDTO): Promise<{ result: IItem }> {
    try {
      this.logger.debug('add item record');

      //move file to new path
      if(itemInputDTO.imgPath!=null){
        const newFilePath = fileUtil.moveFileToPath(itemInputDTO.imgPath, config.fileUpload.imgItemPath);
        itemInputDTO.imgPath = newFilePath;
      };

      const itemRecord = await this.itemModel.create({
        ...itemInputDTO,
      });

      if (!itemRecord) {
        this.logger.error('Fail to create item');
        throw new Error('Item cannot be created');
      }

      // this.eventDispatcher.dispatch(events.user.signUp, { user: itemRecord });

      const result: any = this.prepareOutputItem(itemRecord);
      return { result };
    } catch (e) {
      this.logger.error('Fail to add item, reason: %o ', e.message);
      throw e;
    }
  }

  public async updateItem(itemInputDTO: IItemInputDTO): Promise<{ result: IItem }> {
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

      //move file to new path
      if(itemInputDTO.imgPath!=null){
        const newFilePath = fileUtil.moveFileToPath(itemInputDTO.imgPath, config.fileUpload.imgItemPath);
        itemInputDTO.imgPath = newFilePath;
      };

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

      const result: any = this.prepareOutputItem(updResult);

      return { result };
    } catch (e) {
      this.logger.error('Fail to delete item, itemId: %o, reason: %o ', itemInputDTO.itemId, e.message);
      throw e;
    }
  }

  public async deleteItem(itemId: number): Promise<{ result: IItem }> {
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

      const result: any = this.prepareOutputItem(itemRecord);
      return { result };
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

  private prepareOutputItem(itemRecord: IItem & Document): { item: IItem } {
    if (itemRecord == null) return null;

    try {
      this.logger.debug('prepare output item');

      let item = itemRecord.toObject();
      Reflect.deleteProperty(item, 'createdAt');
      Reflect.deleteProperty(item, 'updatedAt');
      Reflect.deleteProperty(item, '__v');
      Reflect.deleteProperty(item, '_id');
      return item;
    } catch (e) {
      this.logger.error('Fail to prepare output item , reason: %o ', e.message);
      throw e;
    }
  }
}
