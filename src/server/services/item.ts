import { Service, Inject } from 'typedi';
import config from '../config';
import { IItem, IItemInputDTO } from '../interfaces/IItem';
import { Document, Model } from 'mongoose';
// import { EventDispatcher, EventDispatcherInterface } from '../decorators/eventDispatcher';
// import events from '../subscribers/events';
import fs from 'fs';
import moment from 'moment';

@Service()
export default class ItemService {
  constructor(
      @Inject('itemModel') private itemModel : Model<IItem & Document>,
      @Inject('logger') private logger,
      // @EventDispatcher() private eventDispatcher: EventDispatcherInterface,
  ) {}

  public async getItemBySpaceId(spaceId: number): Promise<{ result: IItem[]}> {
    const itemRecordList = await this.itemModel.find({ 'spaceId':spaceId });
    let result: any[] = [];

    if (itemRecordList!=null) {
      itemRecordList.map((item)=>{
        result.push(this.prepareOutputItem(item));
      });
    }
    return {result} ;
  }

  public async getItemById(itemId: number): Promise<{ result: IItem}> {
    const itemRecord = await this.itemModel.findOne({ 'itemId':itemId });
    let result:any = {};

    if (itemRecord) {
      result = this.prepareOutputItem(itemRecord);
    }
    
    return {result} ;
  }

  
  public async addItem(userInputDTO: IItemInputDTO): Promise<{ result: IItem}> {
    try {
      this.logger.silly('Creating user db record');
      const itemRecord = await this.itemModel.create({
        ...userInputDTO,
      });

      if (!itemRecord) {
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

  public async deleteItem(itemId: number): Promise<{ result: IItem}> {
    try {
      this.logger.debug('delete item record, %o', itemId);
      const itemRecord = await this.itemModel.findOne({'itemId':itemId});

      if (!itemRecord) {
        throw new Error('Item not found');
      }

      let delOper = await itemRecord.remove();
      if(delOper.$isDeleted){
        if(itemRecord.imgPath!=null){
          this.clearUploadFile(itemRecord.imgPath);
        }
      }

      const result: any = this.prepareOutputItem(itemRecord);
      return { result };
    } catch (e) {
      this.logger.error('Fail to delete item, itemId: %o, reason: %o ', itemId, e.message);
      throw e;
    }
  }

  private prepareOutputItem(itemRecord: IItem & Document):{item: IItem} {
    if(itemRecord == null) return null;

    try{
      this.logger.debug('prepare output item');

      let item = itemRecord.toObject();
      Reflect.deleteProperty(item, 'createdAt');
      Reflect.deleteProperty(item, 'updatedAt');
      Reflect.deleteProperty(item, '__v');
      Reflect.deleteProperty(item, '_id');
      return item;
    } catch (e) {
      this.logger.error(e);
      throw e;
    }
  }

  private clearUploadFile(path:string):void{
    try {
        if(path!=null){
            fs.unlinkSync(path)
            this.logger.debug('Itme image removed, path: %o '+ path);
        }
    } catch(err) {
        this.logger.error('Fail to delete item image file, path: %o, reason: %o ', path, err.message);
    }
}
}
