import React, { useState, useEffect } from "react";
import Square from "./Square";
import initialSpaceRegionState from "./initialSpaceRegionState";
import "./SpaceRegion.css";

const DIRS_MOVES = [
  { north: [0, -1] },
  { south: [0, 1] },
  { west: [-1, 0] },
  { east: [1, 0] },
  { northeast: [1, -1] },
  { northwest: [-1, -1] },
  { southeast: [1, 1] },
  { southwest: [-1, 1] },
];
const SpaceRegion = () => {
  const width = 10;
  const height = 10;
  const suns = [{ x: 7, y: 8 }];
  const [drones, updateDrones] = useState([
    {
      x: 1,
      y: 1,
      dir: "north",
      state: 1,
    },
    // {
    //   x: 0,
    //   y: 0,
    //   dir: 'south',
    //   state: 1
    // }
  ]);

  const [spaceRegionState, updateSpaceRegionState] = useState([]);
  const initialStarNumber = width * height - suns.length;
  // const [ remainStarNumber, updateRemainingStartNumber] = useState(10)
  // const [ remainDroneNumber, updateRemainingDroneNumber] = useState(20)

  useEffect(() => {
    // console.log('-rendered', suns, width)

    const defaultSpaceRegionState = initialSpaceRegionState(
      width,
      height,
      suns,
      drones
    );

    updateSpaceRegionState(defaultSpaceRegionState);
    console.log(
      "defaultSpaceRegionState",
      defaultSpaceRegionState,
      "spaceRegionState",
      spaceRegionState
    );
  }, []);

  const getRows = (spaceRegionState) => {
    return spaceRegionState.map((row, rowIndex) => {
      return (
        <tr style={{ height: "50px", background: "blue" }}>
          {getCells(row, rowIndex)}
        </tr>
      );
    });
  };

  const getCells = (row, rowIndex) => {
    return row.map((squareState, colIndex) => {
      return getSquareComponent(squareState, rowIndex, colIndex);
    });
  };

  const handleExplore = () => {};

  const getSquareComponent = (squareState, rowIndex, colIndex) => {
    const key = `${rowIndex}-${colIndex}`;
    return (
      <Square
        key={key}
        x={colIndex}
        y={rowIndex}
        squareState={squareState}
        onExpore={handleExplore}
      />
    );
  };

  // const handleUpdateDrones = (val) => {
  //   setDronesString(val)
  //   // console.log('--val', val)
  //   const drones = val.split(';').map(drone => {
  //     const [x, y, dir] = drone.split(',')
  //     // console.log('---spaceRegionState', spaceRegionState)

  //     return {
  //       x,
  //       y,
  //       dir,
  //       state: 1
  //     }
  //   })

  //   console.log('--drones', drones)
  //   updateDrones(drones)
  //   drones.forEach(({x, y}) => {
  //     spaceRegionState[x][y].hasDrone = true
  //   })
  //   // console.log('-------spaceRegionState', spaceRegionState)
  //   updateSpaceRegionState(spaceRegionState)
  // }

  // const handleUpdateSuns = (val) => {

  //   updateSunString(val)
  //   // console.log('--valsss', val)
  //   const suns = val.split(';').map(sun => {
  //     const [x, y] = sun.split(',')
  //     spaceRegionState[x][y].hasSun = true
  //     return {
  //       x,
  //       y
  //     }

  //   })
  //   updateSuns(suns)
  //   suns.forEach(({x, y}) => {
  //     spaceRegionState[x][y].hasSun = true
  //   })
  //   updateSpaceRegionState(spaceRegionState)

  // }

  // const animatePath = (path) => {
  //   for (let i = 0; i < path.length; i++) {
  //     setTimeout(() => {
  //       const node = path[i];
  //       document.getElementById(`${node[0]}-${node[1]}`).className =
  //         'visited';
  //     }, 50 * i);
  //   }
  // }

  // const animateExplorationPath = (visitedSquares, nodesInShortestPathOrder) => {
  //   for (let i = 0; i <= visitedSquares.length; i++) {
  //     if (i === visitedSquares.length) {
  //       setTimeout(() => {
  //         animatePath(visitedSquares);
  //       }, 10 * i);
  //       return;
  //     }
  //     setTimeout(() => {
  //       const node = visitedSquares[i];
  //       document.getElementById(`${node.row}-${node.col}`).className =
  //         'visited';
  //     }, 10 * i);
  //   }
  // }
  const allExplored = (spaceRegionState) => {
    return spaceRegionState.every((square) => square.explored);
  };

  const getDronePath = (drone, spaceRegionState) => {
    const exploreNext = (spaceRegionState, newX, newY, move, queues, path) => {
      // get a new dir
      const newDir = DIRS_MOVES[Math.floor(Math.random() * 8)];
      const dirName = Object.keys(newDir)[0];
      drone.dir = dirName;
      // push to path
      queues.push([newX, newY]);

      path.push([newX, newY]);
      drone.x = newX;
      drone.y = newY;
      const square = spaceRegionState[newX][newY];
      console.log("---square", square);
      spaceRegionState[newX][newY].explored = true;
      move++;

      if (square.hasSun) {
        console.log("suuuuu");
        // updateSpaceRegionState(spaceRegionState)
        drone.state = 0; // crashed
        return;
      } else if (square.hasDrone) {
        drone.state = 0; // crashed
        // updateSpaceRegionState(spaceRegionState)
        return;
      } else if (square.hasStar) {
        console.log("sttar");
        // updateSpaceRegionState(spaceRegionState)
        // square.hasDrone= true
        // square.explored = trues
      }
    };

    const { x, y, dir, state } = drone;
    const path = [[x, y]];
    console.log("drone", drone);
    let queues = [[x, y]];
    let move = 0;

    const dirXY = DIRS_MOVES.find((move) => Object.keys(move)[0] === dir)[dir];
    console.log("---dirXy", dir, DIRS_MOVES, dirXY);

    while (drone.state === 1 && move < 500 && !allExplored(spaceRegionState)) {
      const cur = [drone.x, drone.y];
      const newX = Number(cur[0]) + Number(dirXY[0]);
      const newY = Number(cur[1]) + Number(dirXY[1]);

      if (
        newY >= spaceRegionState.length ||
        newY < 0 ||
        newX >= spaceRegionState[0].length ||
        newX < 0 ||
        spaceRegionState[newX][newY].explored
      ) {
        // barrier
        continue;
      }
      exploreNext(spaceRegionState, newX, newY, move, queues, path);
      // spaceRegionState[x][y].hasDrone = false
    }

    return path;
  };

  const droneAction = (drone, spaceRegionState, i) => {
    const { x, y, dir, state } = drone;
    // console.log('action', spaceRegionState)
    const startNode = [x, y];
    const queues = [startNode];
    let move = 0;
    const id = `${x}-${y}`;
    const visitingSquare = document.getElementById(id);
    // console.log('visitingSquare', visitingSquare, 'id', id)
    visitingSquare.style.backgroundColor = "yellow";
    const dronePaths = getDronePath(drone, spaceRegionState);
    console.log("dronepaths", dronePaths);

    // while(drone.state === 1 && move < 500) {
    //   const dir = DIRS_MOVES[Math.floor(Math.random() * 8)]
    //   const dirName = Object.keys(dir)[0]
    //   const dirXY = dir[dirName]
    //   const cur = queues.shift()

    //   const newX = Number(cur[0]) + Number(dirXY[0])
    //   const newY = Number(cur[1]) + Number(dirXY[1])

    //   queues.push([newX, newY])
    //   // update drone dir
    //   drone.dir = dirName
    //   // console.log('drone.state', drone.state, 'drone', drone)
    //   move ++

    //     if (newY >= spaceRegionState.length || newY < 0 || newX >= spaceRegionState[0].length || newX < 0) {
    //       // barrier
    //       continue
    //     }

    //     // leaving the current square

    //     setTimeout(() => {
    //       const square = spaceRegionState[newX][newY]
    //               // come to the new  square
    //               const droneId = `drone-${drone.x}-${drone.y}`
    //               const leavingDrone = document.getElementById(droneId)
    //               // document.getElementById(droneId).className = 'visited'

    //               leavingDrone.style.display = 'none'
    //               console.log('leavingDrone.style.display', leavingDrone.style.display)
    //               // spaceRegionState[newX][newY].hasDrone = true
    //               console.log('leavingDrone', leavingDrone)

    //       if (square.explored) {
    //         // next step
    //         square.hasDrone = false
    //         return
    //       } else {

    //         drone.x = newX
    //         drone.y = newY

    //                   // come to the new  square
    //         // const droneId = `drone-${cur[0]}-${cur[1]}`
    //         // const leavingDrone = document.getElementById(droneId)
    //         // // document.getElementById(droneId).className = 'visited'

    //         // leavingDrone.style.display = 'none'
    //         // console.log('leavingDrone.style.display', leavingDrone.style.display)
    //         // // spaceRegionState[newX][newY].hasDrone = true
    //         // console.log('leavingDrone', leavingDrone)

    //         spaceRegionState[x][y].hasDrone = false

    //         const newDroneId = `drone-${newX}-${newY}`
    //         const newDrone = document.getElementById(newDroneId)

    //         newDrone.style.display = 'block'
    //         const id = `${newX}-${newY}`
    //         const visitingSquare = document.getElementById(id)
    //         console.log('visitingSquare', visitingSquare)
    //         visitingSquare.style.backgroundColor = 'yellow'

    //         console.log('---square', square)
    //         if (square.hasSun) {
    //           const sunId = `sun-${newX}-${newY}`
    //           const visitingSun = document.getElementById(sunId)
    //           visitingSun.style.display = 'block'

    //           const explosionId = `explosion-${newX}-${newY}`
    //           const visitingExplosion = document.getElementById(explosionId)
    //           visitingExplosion.style.display = 'block'

    //           console.log('suuuuu')
    //           drone.state = 0 // crashed
    //           return
    //         } else if (square.hasDrone) {
    //           const explosionId = `explosion-${newX}-${newY}`
    //           const visitingExplosion = document.getElementById(explosionId)
    //           visitingExplosion.style.display = 'block'

    //           drone.state = 0 // crashed
    //           return
    //         } else if (square.hasStar){
    //           const starId = `star-${newX}-${newY}`
    //           const visitingStar = document.getElementById(starId)
    //           visitingStar.style.display = 'block'

    //           square.hasDrone= true
    //           square.explored = true

    //         }
    //       }

    //       spaceRegionState[newX][newY].explored = true

    //       updateSpaceRegionState(spaceRegionState)

    //     }, move * 50)

    // }
  };

  const eachRun = (spaceRegionState) => {
    console.log("---drones", drones);
    drones.forEach((drone) => {
      const droneId = `drone-${drone.x}-${drone.y}`;
      const Drone = document.getElementById(droneId);
      Drone.style.display = "block";
    });

    for (let i = 0; i < drones.length; i++) {
      droneAction(drones[i], spaceRegionState, i);
    }
  };

  const startSimulation = () => {
    console.log("here", spaceRegionState);
    eachRun(spaceRegionState);
  };

  return (
    <div>
      <div id="header">
        <span className="bombs-remaining digital">{initialStarNumber}</span>
        {/* <Timer isRunning={isRunning} /> */}
      </div>
      <table>
        <tbody>{spaceRegionState && getRows(spaceRegionState)}</tbody>
      </table>
      <button onClick={startSimulation}>Run Simulation </button>
    </div>
  );
};

export default SpaceRegion;

// const getSquareState = (x, y) => {
//   if (x < 0 || x >= width || y < 0 || y >= height) {
//       return SquareState.barrier;
//   }
//   return spaceRegionState[x][y];
// }

// const getAllSquareState = () => {
//   return spaceRegionState;
// }

// const setSquareStateEmpty = (x, y) => {
//   if (x < 0 || x >= width || y < 0 || y >= height) {
//       return; // throw error;
//   }
//    if (spaceRegionState[x][y] == SquareState.drone) {
//       remainDroneNumber--;
//   }
//   spaceRegionState[x][y] = SquareState.empty;
// }

// const setSquareStateDrone = (x, y) => {
//   if (x < 0 || x >= width || y < 0 || y >= height) {
//       return; // throw error;
//   }
//   if (spaceRegionState[x][y] == SquareState.star) {
//       remainStarNumber--;
//   }
//   remainDroneNumber++;
//   spaceRegionState[x][y] = SquareState.drone;
// }

// const initSpaceState = (drones, suns) => {
//   for (drone of drones) {
//       spaceRegionState[drone.getDroneX()][drone.getDroneY()] = SquareState.drone;
//       droneNumber++;
//       initialStarNumber--;
//   }
//   remainDroneNumber = droneNumber;
//   for (sun of suns) {
//       spaceRegionState[sun.getSunX()][sun.getSunY()] = SquareState.sun;
//       sunString++;
//       initialStarNumber--;
//   }
// }
