import React from 'react';
import {
  BrowserRouter as Router,
  Switch,
  Route,
  Link
} from "react-router-dom";

import { DatePicker, Layout, Menu, Breadcrumb } from 'antd';
const { Header, Content, Footer } = Layout;

import Home from './pages/Home.js'
import About from './pages/About.js'
import Essays from './pages/Essays.js'
import Projects from './pages/Projects.js';

const App = () => {

const nav = {
  padding: 0,
  margin: 0,
  position: "absolute",
  top: 0,
  height: "40px",
  width: "100%",
  display: "flex"
};

  return (
   
        <Layout className="layout">
           <Router>
        <Header>
     
          <Menu theme="dark" mode="horizontal" defaultSelectedKeys={['1']}>
            <Menu.Item key="1"> <Link to="/">Home</Link></Menu.Item>
            <Menu.Item key="2"> <Link to="/about">About Me</Link></Menu.Item>
            <Menu.Item key="3"> <Link to="/essays">Essays</Link></Menu.Item>
            <Menu.Item key="4"> <Link to="/projects">Projects</Link></Menu.Item>
          </Menu>




          
 
        </Header>
  
        <Content style={{ padding: '0 50px' }}>
         <Breadcrumb style={{ margin: '16px 0' }}>
         <Breadcrumb.Item>Home</Breadcrumb.Item>
        <Breadcrumb.Item>List</Breadcrumb.Item>
        <Breadcrumb.Item>App</Breadcrumb.Item>
      </Breadcrumb>
      <div className="site-layout-content">
      
      <Switch>
          <Route path="/projects">
            <Projects />
          </Route>
          <Route path="/about">
            <About />
          </Route>
          <Route path="/essays">
            <Essays />
          </Route>
          <Route path="/">
            <Home />
          </Route>
        </Switch>
      </div>
    </Content>




        <Footer style={{ textAlign: 'center' }}>        <DatePicker /> Social Media</Footer>
        </Router>
        </Layout>

   
     
   


  



  );
  
}

export default App
