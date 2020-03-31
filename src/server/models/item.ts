import { IItem } from '../interfaces/IItem';
import mongoose from 'mongoose';
import {MongooseAutoIncrementID} from 'mongoose-auto-increment-reworked';
import { Container } from 'typedi';

const Item = new mongoose.Schema(
  {
    spaceId: {
      type: Number,
      //required: [true, 'Please enter space Id'],
    },
    itemId: {
      type: Number,
      unique: true,
      index: true,
      // required: [true, 'Please enter itemId'], //not necessary, will be auto increased by plugin
    },
    name: {
      type: String,
      required: [true, 'Please enter name'],
    },
    colorCode: {
      type: String,
      //required: [true, 'Please enter colorCode'],
    },
    imgPath: {
      type: String,
    },
    tags: {
      type: String,
    },
    description: {
      type: String,
      //required: [true, 'Please enter description'],
    },
    category: {
      type: String,
      //required: [true, 'Please enter category'],
    },
    reminderDtm: {
      type: Date,
    },
    reminderComplete: {
      type: Boolean,
    },
  },
  { timestamps: true },
);

// Item.pre<IItem>("save", function(next) {
  // next()
// })

;
const AutoIncrement:any = Container.get('autoIncrement')
Item.plugin(AutoIncrement, {inc_field: 'itemId'});
// Item.plugin(MongooseAutoIncrementID.plugin,{modelName: 'Item', field: 'itemId', resetCount: 'reset'})

export default mongoose.model<IItem>('Item', Item);
