import fs from 'fs';
import path from 'path';
import { Container } from 'typedi';
import winston from 'winston';


export function clearUploadFile(path: string): boolean {
    const logger:winston.Logger = Container.get('logger');  
    try {
        if (path != null) {
            fs.unlinkSync(path)
            logger.debug('Item image removed, path: %o ' + path);
        }
        return true;
    } catch (err) {
        logger.error('Fail to delete item image file, path: %o, reason: %o ', path, err.message);
        return false;
    }
}

export function moveFileToPath(tempFilePath: string, targetPath: string): string {
    const logger:winston.Logger = Container.get('logger');  
    try {
        const newFilePath = targetPath + "/" + path.basename(tempFilePath);
        fs.rename(tempFilePath, newFilePath, function (err) {
            if (err) throw err
        });

        logger.debug('Item image moved from %o to %o ', tempFilePath, newFilePath);
        return newFilePath;
    } catch (err) {
        logger.error('Fail to move image file, path: %o, reason: %o ', tempFilePath);
        throw err
    }
}