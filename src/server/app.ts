import 'reflect-metadata'; 
import express from 'express';

module.exports = (async function() {
    const app = express();
    await require('./loaders').default({ expressApp: app });
    return app;
})();
    

  