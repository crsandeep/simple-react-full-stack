import React, { useState, useEffect, useRef } from 'react';
import SpaceRegion from './SpaceRegion2'
import SimulationPanel from './SimulationPanel'

const Home = () => {

    const fetchData = async () => {
      const resp = await fetch('/api/getUsername')
      const res = await resp.json()
      console.log('--res', res)
      // setUsername(res.username)
      return res
    }

  
    useEffect(
      () => {
    }, [])
    return (
        <div className="">
          <SpaceRegion />
            
          <SimulationPanel />
        </div>

        
      
   

  )
}

  export default Home