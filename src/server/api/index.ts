import { Router } from 'express';
import item from './routes/item';

// guaranteed to get dependencies
export default () => {
	const app = Router();
	item(app);

	return app
}