# Space Master

SpaceMaster is a full stack web application using React, Node.js, Express and Webpack. It is also configured with webpack-dev-server, eslint, prettier and babel.

- [spaceMaster](#spaceMaster)
  - [Introduction](#introduction)
    - [Development mode](#development-mode)
  - [Quick Start](#quick-start)
  - [Framework/library used](#technology-used)

## Introduction
SpaceMaster aims to provide a better space management approach for the user who want to well-organize their valuable items. By using SpaceMaster, you can find your item instantly.

SpaceMaster is a simple full stack [React](https://reactjs.org/) application with a [Node.js](https://nodejs.org/en/) and [Express](https://expressjs.com/) backend. Client side code is written in React and the backend API is written using Express. 

### Development mode

In the development mode, we will have 2 servers running. The front end code will be served by the [webpack dev server](https://webpack.js.org/configuration/dev-server/) which helps with hot and live reloading. The server side Express code will be served by a node server using [nodemon](https://nodemon.io/) which helps in automatically restarting the server whenever server side code changes.


## Quick Start

```bash
# Install dependencies
npm install

# Start development server and client
npm run dev

```

## Framework/library used
### **Backend/Server**
- Node.js
- Express
- Typescript
- Sequelize
- Celebrate
- Multer
- Typedi

### **Frontend/Client**
- React
- React-Redux
- Redux-Saga
- React-Bootstrap
- React-Router-Dom
- Formik
- Yup
- React-Toastify
- React-Grid-layout

### **Database**
- PostgreSQL

### **Automated Testing**
- Jest
- Supertest
- Enzyme

