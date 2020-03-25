import { Service, Inject } from 'typedi';
import config from '../config';
import { IUser, IUserInputDTO } from '../interfaces/IUser';
import { Document, Model } from 'mongoose';
// import { EventDispatcher, EventDispatcherInterface } from '../decorators/eventDispatcher';
// import events from '../subscribers/events';

@Service()
export default class UserService {
  constructor(
      @Inject('userModel') private userModel : Model<IUser & Document>,
      @Inject('logger') private logger,
      // @EventDispatcher() private eventDispatcher: EventDispatcherInterface,
  ) {}

  public async SignIn(email: string, password: string): Promise<{ user: IUser}> {
    const userRecord = await this.userModel.findOne({ email });
    if (!userRecord) {
      throw new Error('User not registered');
    }

      const user = userRecord.toObject();
      Reflect.deleteProperty(user, 'password');
      Reflect.deleteProperty(user, 'salt');
      return { user };
  }

  
  public async SignUp(userInputDTO: IUserInputDTO): Promise<{ user: IUser}> {
    try {
      this.logger.silly('Creating user db record');
      const userRecord = await this.userModel.create({
        ...userInputDTO,
        salt: 'testing salt',
      });

      if (!userRecord) {
        throw new Error('User cannot be created');
      }
      this.logger.silly('Sending welcome email');

      // this.eventDispatcher.dispatch(events.user.signUp, { user: userRecord });

      const user = userRecord.toObject();
      Reflect.deleteProperty(user, 'password');
      Reflect.deleteProperty(user, 'salt');
      return { user };
    } catch (e) {
      this.logger.error(e);
      throw e;
    }
  }
}
