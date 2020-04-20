import React from 'react';
import {
  BrowserRouter as Router,
  Switch,
  Route,
  Link
} from "react-router-dom";

import {  Layout, Menu } from 'antd';
const { Header, Content } = Layout;

import Home from './Home.js'

const App = () => {

  return (
   
        <Layout className="layout">
           <Router>
        <Header>
     
          <Menu theme="dark" mode="horizontal" defaultSelectedKeys={['1']}>
            <Menu.Item key="1"> <Link to="/">Home</Link></Menu.Item>
          </Menu>




          
 
        </Header>
  
        <Content style={{ padding: '0 50px' }}>
 
      <div className="site-layout-content">
      
      <Switch>
          <Route path="/">
            <Home />
          </Route>
        </Switch>
      </div>
    </Content>




        </Router>
        </Layout>

   
     
   


  



  );
  
}

export default App
