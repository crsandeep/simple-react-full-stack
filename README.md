# simple-react-full-stack

[![Build Status](https://travis-ci.org/crsandeep/simple-react-full-stack.svg?branch=master)](https://travis-ci.org/crsandeep/simple-react-full-stack)

This is a boilerplate to build a full stack web application using React, Node.js, Express and Webpack. It is also configured with webpack-dev-server, eslint, prettier and babel.

---

## ✅ Deliverables & Tasks

### 1. Application Selection & Fork

* Chosen App: [simple-react-full-stack](https://github.com/crsandeep/simple-react-full-stack)
* Forked from GitHub to customize and extend.

### 2. Multi-Stage CI/CD Pipeline (GitHub Actions)

* **Stage 1:** Lint + Unit Tests
* **Stage 2:** Docker Build & Push
* **Stage 3:** Deploy to Staging (e.g., Render/Fly.io)
* **Stage 4:** Manual Approval → Deploy to Production
* Docker images pushed to Docker Hub / GitHub Container Registry.

### 3. Infrastructure as Code

* Used **Terraform** (free) to set up:

  * Containerized hosting setup
  * Networking rules (optional)
* `.tf` files support both **staging** and **production**.

### 4. Reverse Proxy Setup with NGINX

* NGINX configured as a reverse proxy in front of apps
* Routing:

  * `yourapp.com/staging` → staging
  * `yourapp.com/` → production
* Used Freenom (free domain) + Cloudflare DNS + Render/Railway

### 5. Monitoring & Logging

* Stack: **Prometheus + Grafana + Alertmanager**
* Via `docker-compose` setup
* Tracks:

  * Container uptime, CPU, memory
  * Alerts simulated via Alertmanager

### 6. Health Check & Failover Simulation

* Script (bash/python) to:

  * Run health checks on production URL
  * If down → switch NGINX route to staging
* NGINX config reload used for failover simulation

---

## 🧠 Original Project Documentation

[Create React App](https://github.com/facebook/create-react-app) is a quick way to get started with React development and it requires no build configuration. But it completely hides the build config which makes it difficult to extend. It also requires some additional work to integrate it with an existing Node.js/Express backend application.

This is a simple full stack [React](https://reactjs.org/) application with a [Node.js](https://nodejs.org/en/) and [Express](https://expressjs.com/) backend. Client side code is written in React and the backend API is written using Express. This application is configured with [Airbnb's ESLint rules](https://github.com/airbnb/javascript) and formatted through [prettier](https://prettier.io/).

---

## Development mode

In the development mode, we will have 2 servers running. The front end code will be served by the [webpack dev server](https://webpack.js.org/configuration/dev-server/) which helps with hot and live reloading. The server side Express code will be served by a node server using [nodemon](https://nodemon.io/) which helps in automatically restarting the server whenever server side code changes.

## Production mode

In the production mode, we will have only 1 server running. All the client side code will be bundled into static files using webpack and it will be served by the Node.js/Express application.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/crsandeep/simple-react-full-stack

# Go inside the directory
cd simple-react-full-stack

# Install dependencies
yarn (or npm install)

# Start development server
yarn dev (or npm run dev)

# Build for production
yarn build (or npm run build)

# Start production server
yarn start (or npm start)
```

---

## Documentation

### Folder Structure

All the source code will be inside **src** directory. Inside src, there is client and server directory. All the frontend code (react, css, js and any other assets) will be in client directory. Backend Node.js/Express code will be in the server directory.

### Babel

[Babel](https://babeljs.io/) helps us to write code in the latest version of JavaScript. If an environment does not support certain features natively, Babel will help us to compile those features down to a supported version. It also helps us to convert JSX to Javascript.

.babelrc

```json
{
  "presets": ["env", "react"]
}
```

### ESLint

[ESLint](https://eslint.org/) is a pluggable and configurable linter tool for identifying and reporting on patterns in JavaScript.

.eslintrc.json

```json
{
  "extends": ["airbnb"],
  "env": {
    "browser": true,
    "node": true
  },
  "rules": {
    "no-console": "off",
    "comma-dangle": "off",
    "react/jsx-filename-extension": "off"
  }
}
```

### Webpack

webpack.config.js

```js
const path = require("path");
const HtmlWebpackPlugin = require("html-webpack-plugin");
const { CleanWebpackPlugin } = require("clean-webpack-plugin");

const outputDirectory = "dist";

module.exports = {
  entry: ["babel-polyfill", "./src/client/index.js"],
  output: {
    path: path.join(__dirname, outputDirectory),
    filename: "bundle.js"
  },
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: {
          loader: "babel-loader"
        }
      },
      {
        test: /\.css$/,
        use: ["style-loader", "css-loader"]
      },
      {
        test: /\.(png|woff|woff2|eot|ttf|svg)$/,
        loader: "url-loader?limit=100000"
      }
    ]
  },
  devServer: {
    port: 3000,
    open: true,
    proxy: {
      "/api": "http://localhost:8080"
    }
  },
  plugins: [
    new CleanWebpackPlugin(),
    new HtmlWebpackPlugin({
      template: "./public/index.html",
      favicon: "./public/favicon.ico"
    })
  ]
};
```

### Webpack Dev Server

webpack.config.js devServer section:

```js
  devServer: {
    port: 3000,
    open: true,
    proxy: {
      "/api": "http://localhost:8080"
    }
  }
```

### Nodemon

nodemon.json

```json
{
  "watch": ["src/server/"]
}
```

### Express

src/server/index.js

```js
const express = require("express");
const os = require("os");

const app = express();

app.use(express.static("dist"));
app.get("/api/getUsername", (req, res) =>
  res.send({ username: os.userInfo().username })
);
app.listen(8080, () => console.log("Listening on port 8080!"));
```

### Concurrently

package.json scripts:

```json
"client": "webpack-dev-server --mode development --devtool inline-source-map --hot",
"server": "nodemon src/server/index.js",
"dev": "concurrently \"npm run server\" \"npm run client\""
```

### VSCode + ESLint + Prettier

VSCode settings:

```json
"eslint.alwaysShowStatus": true,
"eslint.autoFixOnSave": true,
"editor.formatOnSave": true,
"prettier.eslintIntegration": true
```

---

## Credits

Based on [@crsandeep](https://github.com/crsandeep/simple-react-full-stack).

Updated by [Bharadwaj Shivanya](https://github.com/BharadwajShivanya) with Docker, GitHub Actions, Prometheus stack, and NGINX failover.
