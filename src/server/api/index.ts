import { Router } from 'express';
import item from './routes/item';
import space from './routes/space';

// guaranteed to get dependencies
export default () => {
	const app = Router();
	space(app);
	item(app);
	return app
}