import { Service, Inject } from 'typedi';
import config from '../config';
import { IItem, IItemInputDTO } from '../interfaces/IItem';
import { Document, Model } from 'mongoose';
// import { EventDispatcher, EventDispatcherInterface } from '../decorators/eventDispatcher';
// import events from '../subscribers/events';

@Service()
export default class ItemService {
  constructor(
      @Inject('itemModel') private itemModel : Model<IItem & Document>,
      @Inject('logger') private logger,
      // @EventDispatcher() private eventDispatcher: EventDispatcherInterface,
  ) {}

  public async getItemById(itemId: number): Promise<{ result: IItem}> {
    const itemRecord = await this.itemModel.findOne({ 'itemId':itemId });
    let result = null;
    if (itemRecord) {
      result = itemRecord.toObject();
      // Reflect.deleteProperty(item, 'password');
      // Reflect.deleteProperty(item, 'salt');
    }else{
      result = {};
    }
    return {result} ;
  }

  
  public async addItem(userInputDTO: IItemInputDTO): Promise<{ result: IItem}> {
    try {
      this.logger.silly('Creating user db record');
      const itemRecord = await this.itemModel.create({
        ...userInputDTO,
        // salt: 'testing salt',
      });

      if (!itemRecord) {
        throw new Error('Item cannot be created');
      }

      // this.eventDispatcher.dispatch(events.user.signUp, { user: itemRecord });

      const result = itemRecord.toObject();
      // Reflect.deleteProperty(user, 'password');
      // Reflect.deleteProperty(user, 'salt');
      return { result };
    } catch (e) {
      this.logger.error(e);
      throw e;
    }
  }
}
