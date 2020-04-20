import React, {useState, useEffect} from 'react'

const SimulationPanel = () => {
    const [width, updateWidth] = useState(10)
    const [height, updateHeight] = useState(10)
    const [ sunString, updateSunString] = useState('1,2;3,4')
    const [ dronesString, setDronesString] = useState('1,2,west;3,4,east')
    const [drones, updateDrones] = useState([
        {
          x: 1,
          y: 1,
          dir: 'north',
          state: 1
        },
        {
          x: 3,
          y: 6,
          dir: 'north',
          state: 1
        }
      ])

      const [suns, updateSuns] = useState([
        {x: 1, y: 2}
      ])

   


    return <div id='footer' style={{margin: '50px'}}>
          
    <form>
        <div> Set width: </div>
        <input
            type='number'
            style={{ height: "20px", width: "300px" }}
            value={width}
            onChange={(event) => handleUpdateWidth(event.target.value)}
        />
      <div> Set height: </div>
        <input
            type='number'
            style={{ height: "20px", width: "300px" }}
            value={height}
            onChange={(event) => handleUpdateHeight(event.target.value)}
        />
        <div> Drones e.g: 1,2,west;3,4,east </div>
        <input
     
            style={{ height: "20px", width: "300px" }}
            value={dronesString}
            onChange={(event) => handleUpdateDrones(event.target.value)}
        
        />
            {drones && drones.map((drone, index) => {
            return <div key={index}>
                <strong>Drone{index + 1}</strong>: x: {drone.x} y: {drone.y} dir: {drone.dir}
            </div>
        })}
        <div> Suns e.g. 1,2;3,4</div>
        <input

            style={{ height: "20px", width: "300px" }}
            value={sunString}
            onChange={(event) => handleUpdateSuns(event.target.value)}
        
          />
      {suns && suns.map((sun, index) => {
            return <div key={index}>
                <strong>Sun {index + 1}</strong>: x: {sun.x} y: {sun.y}
            </div>
        })}
        <br />
       
        <br />
       
       <br />
       
       <br />

        </form>
    </div>
}
      
export default SimulationPanel