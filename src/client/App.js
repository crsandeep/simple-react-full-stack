import React, { useState, useEffect } from 'react';
import { DatePicker, Layout, Menu, Breadcrumb } from 'antd';
const { Header, Content, Footer } = Layout;


const App = () => {
  // state = { username: null };
  const [username, setUsername] = useState()
  // todo write fetcer
  const fetchData = async () => {
    const resp = await fetch('/api/getUsername')
    const res = await resp.json()
    console.log('--res', res)
    setUsername(res.username)
    return res
  }

  useEffect(
    () => {
    fetchData()
  }, [])

  return (
    <div>
      <Layout className="layout">
        <Header>
          <div className="logo" />
          <Menu theme="dark" mode="horizontal" defaultSelectedKeys={['1']}>
            <Menu.Item key="1">nav 1</Menu.Item>
            <Menu.Item key="2">nav 2</Menu.Item>
            <Menu.Item key="3">nav 3</Menu.Item>
          </Menu>
        </Header>
        <Content style={{ padding: '0 50px' }}>
          <Breadcrumb style={{ margin: '16px 0' }}>
            <Breadcrumb.Item>Home</Breadcrumb.Item>
            <Breadcrumb.Item>List</Breadcrumb.Item>
            <Breadcrumb.Item>App</Breadcrumb.Item>
          </Breadcrumb>
          <div className="site-layout-content">Content</div>
          {username ? <h1>{`Hello ${username}`}</h1> : <h1>Loading.. please wait!</h1>}
          <DatePicker />
        </Content>
        <Footer style={{ textAlign: 'center' }}>Social Media</Footer>
        </Layout>
    </div>
  );
  
}

export default App
