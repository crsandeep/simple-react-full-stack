import express from 'express';
import bodyParser from 'body-parser';
import cors from 'cors';
import morgan from 'morgan';
import passport from 'passport';
import routes from '../api';
import config from '../config';
import passportStrategy from './passport';

export default ({ app }: { app: express.Application }) => {
  app.get('/status', (req, res) => {
    res.status(200).end();
  });
  app.head('/status', (req, res) => {
    res.status(200).end();
  });

  app.enable('trust proxy');
  app.use(cors());

  app.use(bodyParser.json({ limit: '5mb' }));
  app.use(bodyParser.urlencoded({ limit: '5mb', extended: true }));
  app.use(passport.initialize());
  passport.use(passportStrategy);
  app.use(require('method-override')());
  app.use(morgan(config.mogran.level));


  // Load API routes
  app.use(config.api.prefix, routes());

  // set static path
  app.use(express.static(config.publicFolder));

  // / catch 404 and forward to error handler
  app.use((req, res, next) => {
    const err = new Error('Endpoint Not Found');
    // eslint-disable-next-line dot-notation
    err['status'] = 404;
    next(err);
  });

  // / error handlers
  app.use((err, req, res, next) => {
    /**
     * Handle 401 thrown by express-jwt library
     */
    if (err.name === 'Unauthorized') {
      return res
        .status(err.status)
        .send({ message: err.message })
        .end();
    }
    return next(err);
  });

  app.use((err, req, res, next) => {
    res.status(err.status || 500);
    res.json({
      isSuccess: false,
      payload: null,
      message: err.message
    });
  });
};
