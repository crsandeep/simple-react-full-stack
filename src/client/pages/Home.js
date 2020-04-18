import React, { useState, useEffect } from 'react';
import { Row, Col } from 'antd';

const Home = () => {
    const [username, setUsername] = useState()
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

  

        <div className="">
        
              Content
              <Row gutter={[16, 16]}>
                <Col span={12} >
                  hahah
                </Col>
                <Col span={12} >
                  hahah
                </Col>
              </Row>

              <Row gutter={[16, 16]}>
                <Col span={12} >
                  hahah
                </Col>
                <Col span={12} >
                  hahah
                </Col>
              </Row>

              <Row gutter={[16, 16]}>
                <Col span={12} >
                  hahah
                </Col>
                <Col span={12} >
                  hahah
                </Col>
              </Row>

                
   
        
        
        </div>

        
      
   

  )
}

  export default Home