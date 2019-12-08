import mongoose from 'mongoose';

const recordingSchema = new mongoose.Schema({
  date: {
    type: String,
  },
  title:{
    type: String,
  },
  frames:{
    type:String
  }
});

const Recording = mongoose.model('Recording', recordingSchema);

export default Recording;
