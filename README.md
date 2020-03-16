# mySpace

mySpace is a full stack web application using React, Node.js, Express and Webpack. It is also configured with webpack-dev-server, eslint, prettier and babel.

- [mySpace](#mySpace)
  - [Introduction](#introduction)
    - [Development mode](#development-mode)
    - [Production mode](#production-mode)
  - [Quick Start](#quick-start)
  - [Framework/library used](#technology-used)    

## Introduction
mySpace aims to provide a better space management approach for the user who want to well-organize their valuable items. By using mySpace, you can find your item instantly.

mySpace is a simple full stack [React](https://reactjs.org/) application with a [Node.js](https://nodejs.org/en/) and [Express](https://expressjs.com/) backend. Client side code is written in React and the backend API is written using Express. This application is configured with [Airbnb's ESLint rules](https://github.com/airbnb/javascript) and formatted through [prettier](https://prettier.io/).

### Development mode

In the development mode, we will have 2 servers running. The front end code will be served by the [webpack dev server](https://webpack.js.org/configuration/dev-server/) which helps with hot and live reloading. The server side Express code will be served by a node server using [nodemon](https://nodemon.io/) which helps in automatically restarting the server whenever server side code changes.

### Production mode

In the production mode, we will have only 1 server running. All the client side code will be bundled into static files using webpack and it will be served by the Node.js/Express application.

## Quick Start

```bash
# Install dependencies
yarn (or npm install)

# Start development server
yarn dev (or npm run dev)

# Build for production
yarn build (or npm run build)

# Start production server
yarn start (or npm start)
```

## Framework/library used

- React-Redux
- Redux-Saga
- React-Bootstrap
- React-Router-Dom
- Material-ui
- Formik
- Yup
- React-Toastify
- React-Grid-layout
- Moment
