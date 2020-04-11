import React from 'react';
import { Route, BrowserRouter as Router, Switch } from "react-router-dom";
import { Provider } from 'react-redux'
import { createStore,applyMiddleware} from 'redux'
import allReducers from './reducers'
import createSagaMiddleware from 'redux-saga'
import rootSaga from './sagas'

import {Item, Space} from './views/';
import {HeaderComp} from "./components/";
// import FooterComp from "./components/common/FooterComp";

//saga
const sagaMiddleware = createSagaMiddleware()
const store = createStore(allReducers, applyMiddleware(sagaMiddleware))
sagaMiddleware.run(rootSaga)

function App() {
  let linkMap = new Map([
    ['Home', '/home'],
    ['Space', '/space'],
    ['Item', '/item'],
  ]);
  return (
    <Provider store={store}>
      <Router>
        <div>
          <HeaderComp linkMap={linkMap}/>
          <Switch>
            <Route path="/" component={Space} />
          </Switch>
         </div>
      </Router>
    </Provider>
  );
}

export default App;
