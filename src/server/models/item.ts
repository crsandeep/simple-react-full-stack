import { IItem } from '../interfaces/IItem';
import mongoose from 'mongoose';
import {MongooseAutoIncrementID} from 'mongoose-auto-increment-reworked';

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
      required: [true, 'Please enter itemId'],
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
//   next()
// })
Item.plugin(MongooseAutoIncrementID.plugin,{modelName: 'Item', field: 'itemId'})

export default mongoose.model<IItem>('Item', Item);
