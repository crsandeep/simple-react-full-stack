
import mongoose from 'mongoose';
export interface IUser extends mongoose.Document {
    _id: string;
    name: string;
    email: string;
    password: string;
    salt: string;
  }
  
  export interface IUserInputDTO {
    name: ['name'];
    email: ['email'];
    password: ['password'];
  }
  