
import multer from 'multer';
import config from '.';
import path from 'path';
import {v4 as uuid} from 'uuid';

export const storageOptions:multer.DiskStorageOptions = {
    destination: function (req, file, cb) {
        //upload to temp path
        cb(null, config.fileUpload.tempPath);
    },
    filename: function (req, file, cb) {
        //rename as uuid
        cb(null, uuid() + path.extname(file.originalname))
    }
}

export function fileTypeFilter(req, file, callback) {
    var ext = path.extname(file.originalname);
    let isValid = false;
    for(let supportType of config.fileUpload.fileType){
        if(ext.toLowerCase() == supportType.toLowerCase()){
            isValid = true;
            break;
        }
    }

    if(!isValid){
        return callback(new Error('Only images are allowed'))
    }else{
        callback(null, true)
    }
}
  
export const fileSizeFilter = { fileSize: config.fileUpload.maxSize }