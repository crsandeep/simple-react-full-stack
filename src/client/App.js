import React from 'react';
import { Route, BrowserRouter as Router, Switch } from 'react-router-dom';
import { Provider } from 'react-redux';
import { createStore, applyMiddleware } from 'redux';
import createSagaMiddleware from 'redux-saga';
import allReducers from './reducers';
import rootSaga from './sagas';
import { Item, Space, Grid } from './views';
import { HeaderComp } from './components';

// import FooterComp from "./components/common/FooterComp";
// saga

const sagaMiddleware = createSagaMiddleware();
const store = createStore(allReducers, applyMiddleware(sagaMiddleware));
sagaMiddleware.run(rootSaga);

function App() {
  const linkMap = new Map([
    ['Home', '/home'],
    ['Space', '/space'],
    ['Grid', '/grid'],
    ['Item', '/item']
  ]);

  return (
    <Provider store={store}>
      <Router>
        <div>
          <HeaderComp linkMap={linkMap} />

          <Switch>
            {/* <Route path="/" component={Space} /> */}
            <Route path="/space" component={Space} />
            <Route path="/grid" component={Grid} />
            <Route path="/item" component={Item} />
          </Switch>
        </div>
      </Router>
    </Provider>
  );
}

export default App;
