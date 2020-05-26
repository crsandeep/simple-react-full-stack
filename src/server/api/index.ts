import { Router } from 'express';
import item from './routes/item';
import space from './routes/space';
import grid from './routes/grid';
import auth from './routes/auth';

// guaranteed to get dependencies
export default () => {
  const app = Router();
  space(app);
  item(app);
  grid(app);
  auth(app);
  return app;
};
