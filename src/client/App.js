import React from 'react';
import { Route, BrowserRouter as Router } from 'react-router-dom';
import { Provider } from 'react-redux';
import { createStore, applyMiddleware } from 'redux';
import createSagaMiddleware from 'redux-saga';
import SideNav, {
  NavItem, NavIcon, NavText
} from '@trendmicro/react-sidenav';
import styled from 'styled-components';
import allReducers from './reducers';
import rootSaga from './sagas';
import { Item, Space, Grid } from './views';

const sagaMiddleware = createSagaMiddleware();
const store = createStore(allReducers, applyMiddleware(sagaMiddleware));
sagaMiddleware.run(rootSaga);

const navWidthCollapsed = 64;
const navWidthExpanded = 300;

const Main = styled.main`
  position: relative;
  overflow: hidden;
  transition: all .15s;
  padding: 0 5px;
  margin-left: ${props => (props.expanded ? navWidthExpanded : navWidthCollapsed)}px;
`;

const NavHeader = styled.div`
    display: ${props => (props.expanded ? 'block' : 'none')};
    white-space: nowrap;
    // background-color: #007bff;
    color: #fff;
    > * {
        color: inherit;
        background-color: inherit;
    }
`;
const NavTitle = styled.div`
    font-size: 2em;
    line-height: 20px;
    padding: 10px 0;
`;
const NavSubTitle = styled.div`
    font-size: 1em;
    line-height: 20px;
    padding-bottom: 4px;
`;

const Separator = styled.div`
    clear: both;
    position: relative;
    margin: .8rem 0;
    background-color: #ddd;
    height: 1px;
`;

export class App extends React.Component {
  state = {
    selected: 'home',
    expanded: false
  };

  onToggle = (expanded) => {
    this.setState({ expanded });
  };

  render() {
    const { expanded, selected } = this.state;

    return (
      <Provider store={store}>
        <Router>
          <Route render={({ location, history }) => (
            <React.Fragment>
              <SideNav
                style={{ minWidth: expanded ? navWidthExpanded : navWidthCollapsed }}
                onSelect={(isSelect) => {
                  const to = `/${isSelect}`;
                  if (location.pathname !== to) {
                    history.push(to);
                  }
                  this.setState({ selected: isSelect });
                }}
                onToggle={this.onToggle}
              >
                <SideNav.Toggle />
                <NavHeader expanded={expanded}>
                  <NavTitle>Space Master</NavTitle>
                  <NavSubTitle>Welcome Back Peter!</NavSubTitle>
                </NavHeader>
                <SideNav.Nav selected={selected}>
                  <NavItem eventKey="space">
                    <NavIcon>
                      <i className="fa fa-fw fa-home" style={{ fontSize: '1.75em', verticalAlign: 'middle' }} />
                    </NavIcon>
                    <NavText style={{ paddingRight: 32 }} title="Space">
                      Space
                    </NavText>
                  </NavItem>
                  <NavItem eventKey="grid">
                    <NavIcon>
                      <i className="fa fa-fw fa-table" style={{ fontSize: '1.75em', verticalAlign: 'middle' }} />
                    </NavIcon>
                    <NavText style={{ paddingRight: 32 }} title="Grid">
                      Grid
                    </NavText>
                  </NavItem>
                  <NavItem eventKey="item">
                    <NavIcon>
                      <i className="fa fa-fw fa-th-list" style={{ fontSize: '1.75em', verticalAlign: 'middle' }} />
                    </NavIcon>
                    <NavText style={{ paddingRight: 32 }} title="Items">
                      Items
                    </NavText>
                  </NavItem>
                  <Separator />
                  <NavItem eventKey="logout">
                    <NavIcon>
                      <i className="fa fa-fw fa-power-off" style={{ fontSize: '1.75em', verticalAlign: 'middle' }} />
                    </NavIcon>
                    <NavText style={{ paddingRight: 32 }} title="Logout">
                      Logout
                    </NavText>
                  </NavItem>
                </SideNav.Nav>
              </SideNav>
              <Main expanded={expanded}>
                <Route path="/" exact component={props => <Space />} />
                <Route path="/space" exact component={props => <Space />} />
                <Route path="/grid" component={props => <Grid />} />
                <Route path="/item" component={props => <Item />} />
                <Route path="/logout" component={props => <Item />} />
              </Main>
            </React.Fragment>
          )}
          />
        </Router>
      </Provider>
    );
  }
}
export default App;
