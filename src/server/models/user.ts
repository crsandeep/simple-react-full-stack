import { IUser } from '../interfaces/IUser';
import mongoose from 'mongoose';

const User = new mongoose.Schema(
  {
    name: {
      type: String,
      required: [true, 'Please enter a full name'],
      index: true,
    },

    email: {
      type: String,
      lowercase: true,
      unique: true,
      index: true,
    },

    password: String,

    salt: String,

    role: {
      type: String,
      default: 'user',
    },
  },
  { timestamps: true },
);

User.pre<IUser>("save", function(next) {
  const user = this;
  console.log("saving: %s (%s)", this.name, this.email)
  next()
})

export default mongoose.model<IUser>('User', User);
