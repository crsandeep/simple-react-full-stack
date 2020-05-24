import { Router } from 'express';
import item from './routes/item';
import space from './routes/space';
import grid from './routes/grid';

// guaranteed to get dependencies
export default () => {
  const app = Router();
  space(app);
  item(app);
  grid(app);
  return app;
};
