
import mongoose from 'mongoose';
export interface IItem extends mongoose.Document {
    _id: string;
    spaceId: number;
    itemId: number;
    name: string;
    colorCode: string;
    imgPath: string;
    tags: string;
    description: string;
    category: string;
    reminderDtm: Date;
    reminderComplete: boolean;
  }
  
  export interface IItemInputDTO {
    spaceId:['spaceId'];
    itemId:['itemId'];
    name:['name'];
    colorCode:['colorCode'];
    imgPath:['imgPath'];
    tags:['tags'];
    description:['description'];
    category:['category'];
    reminderDtm: ['reminderDtm'];
    reminderComplete: ['reminderComplete'];
  }
  