import dotenv from 'dotenv';

const envFound = dotenv.config();
if (!envFound) {
  throw new Error("Couldn't find .env file");
}

export default {
  /**
   * Your favorite port
   */
  port: parseInt(process.env.PORT, 10),

  /**
   * secret sauce
   */
  jwtSecret: process.env.JWT_SECRET,


  /**
   * token expire in minutes
   */
  tokenExpireMins: 60 * 60 * 1,

  /**
   * Used by winston logger
   */
  logs: {
    level: process.env.LOG_LEVEL || 'silly'
  },

  /**
   * Used by morgan logger
   */
  mogran: {
    level: process.env.MORGAN_LEVEL || 'dev'
  },

  /**
   * API configs
   */
  api: {
    prefix: '/api'
  },

  /**
   * Used by display
   */
  publicFolder: process.env.PUBLIC_FOLDER,


  /**
   * upload configs
   */
  fileUpload: {
    tempPath: process.env.FILE_UPLOAD_TEMP_PATH,
    imgItemPath: process.env.FILE_UPLOAD_IMG_ITEM_PATH,
    imgSpacePath: process.env.FILE_UPLOAD_IMG_SPACE_PATH,
    maxSize: (1024 * 1024 * parseInt(process.env.FILE_UPLOAD_MAX_SIZE, 10)),
    fileType: ['.png', '.jpg', '.jpeg', 'gif']
  }


};
