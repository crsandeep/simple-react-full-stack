
 mySpace-react-full-stack 

**Sometime you just can't find the item you are looking for? We have the same problem.** 
SpaceMaster enable user to locate their items at a glance, it shows the location (bedroom/living room/kitchen...etc) or container (wardobe/cabinet/box/...etc) in an intuitive approach. You can keep all details of your items, including photo, location and remarks, by using SpaceMaster. Reminder is a great way to remind you to take care of your items, like milk and bread which have a very short shelf life.


### How it works:
 - Customize your container(wardobe/cabinet/box/...etc) with an intutive approach (2D-view)
 - Save your items with details (photo, category, remark and reminder)
 - That's it! 

### Looking for your item? 
 - Search your item in various way (keyword/location/container/category...etc)
 - All related items' location will be located with a very clear path (e.g. Kitchen -> Top left cabinet ->  space #3)
 - Photo and remarks are shown to assist you to confirm it is a correct item you are looking for
 - Magic!

### Reminder
 - Save your items with specific date and time
 - SpaceMaster will notify you when due time has come
 - It's time to handle your item!

 

### How to run SpaceMaster?

```bash
{
    npm install # install all dependency
    npm run dev # Start development server and client
}
```


### Technology Used:

**Frontend**
- React
- React-Redux

**Backend**
- Node.js
- Express
- Typescript

**Database**
- PostgreSQL

**Automated Testing**
- Jest
- Supertest
- Enzyme



### Folder Structure
``` bash
├─__tests__ 	#test files
├─public 		#final hosting folder
├─jest			#jest setup
└─src
	├─client
	│  ├─actions
	│  ├─actionTypes
	│  ├─components
	│  ├─config
	│  ├─constants
	│  ├─css
	│  ├─reducers
	│  ├─sagas
	│  ├─services
	│  ├─utils
	│  └─views
	└─server
		├─api
		│  └─routes
		├─config
		├─constants
		├─interfaces
		├─loaders
		├─models
		├─services
		└─util
```


### Todos
 - Integrate JWT to improve security
 - Add reminder job
 - Add image template for space grid
 - Improve UI to provide more mobile friendly experience

License
----

MIT
