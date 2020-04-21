import React, { useState, useEffect } from "react";
import Square from "./Square";
import initialSpaceRegionState from "./initialSpaceRegionState";
import "./SpaceRegion.css";
import { droneAction } from "./drone-action";
import DroneStates from "./DroneState";
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
  const width = 5;
  const height = 5;
  const suns = [{ x: 2, y: 3 }];
  const [drones, updateDrones] = useState([
    {
      x: 1,
      y: 1,
      dir: "north",
      state: 1,
    },
    {
      x: 0,
      y: 0,
      dir: "south",
      state: 1,
    },
  ]);

  const [spaceRegionState, updateSpaceRegionState] = useState([]);
  const initialStarNumber = width * height - suns.length;
  const [currrentDroneState, setCurrentDroneState] = useState();
  // const [ remainStarNumber, updateRemainingStartNumber] = useState(10)
  // const [ remainDroneNumber, updateRemainingDroneNumber] = useState(20)

  useEffect(() => {
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

  // const droneAction = (drone, spaceRegionState, move) => {
  //   const unvisitedSquare = spaceRegionState.filter((s) => !s.explored);
  //   const path = [];
  //   const queues = [drone];
  //   path.push([drone.x, drone.y]);

  //   let curDroneState = drone.state;
  //   console.log(
  //     "curDroneState !== 0 && move < 100 && unvisitedSquare.length",
  //     curDroneState !== 0,
  //     move < 100,
  //     unvisitedSquare.length
  //   );
  //   while (curDroneState !== 0 && move < 100 && unvisitedSquare.length) {
  //     curDroneState = drone.state;
  //     console.log(
  //       "current drone",
  //       drone,
  //       "curDroneState",
  //       curDroneState,
  //       "x",
  //       drone.x,
  //       drone.y
  //     );
  //     const { x, y, dir, state } = drone;

  //     const curState = drone;
  //     let curLocation = [curState.x, curState.y];

  //     // const id = `${x}-${y}`;

  //     // const visitingSquare = document.getElementById(id);
  //     // visitingSquare.style.backgroundColor = "yellow";

  //     const nextDir = DIRS_MOVES[Math.floor(Math.random() * 8)];
  //     const dirName = Object.keys(nextDir)[0];
  //     const dirXY = nextDir[dirName];
  //     // drone.dir = dirName;

  //     const newX = Number(curLocation[0]) + Number(dirXY[0]);
  //     const newY = Number(curLocation[1]) + Number(dirXY[1]);

  //     // console.log("newX----", newX, "newY", newY);
  //     // console.log('drone.state', drone.state, 'drone', drone)
  //     if (
  //       newY >= spaceRegionState.length ||
  //       newY < 0 ||
  //       newX >= spaceRegionState[0].length ||
  //       newX < 0 ||
  //       spaceRegionState[newX][newY].explored
  //     ) {
  //       console.log("exit2");
  //       continue;
  //     }

  //     setTimeout(
  //       (function (move) {
  //         const { x, y, dir, state } = drone;

  //         const curState = drone;
  //         let curLocation = [curState.x, curState.y];

  //         const id = `${x}-${y}`;

  //         const visitingSquare = document.getElementById(id);
  //         visitingSquare.style.backgroundColor = "yellow";

  //         const nextDir = DIRS_MOVES[Math.floor(Math.random() * 8)];
  //         const dirName = Object.keys(nextDir)[0];
  //         const dirXY = nextDir[dirName];
  //         drone.dir = dirName;

  //         const newX = Number(curLocation[0]) + Number(dirXY[0]);
  //         const newY = Number(curLocation[1]) + Number(dirXY[1]);

  //         console.log("---move", move, path);
  //         path.push([newX, newY]);

  //         // const curLocation = path[move];
  //         console.log(" spaceRegionState", spaceRegionState, newX, newY);
  //         const square = spaceRegionState[newX][newY];

  //         // come to the new  square
  //         const droneId = `drone-${curLocation[0]}-${curLocation[1]}`;
  //         const leavingDrone = document.getElementById(droneId);
  //         // document.getElementById(droneId).className = 'visited'
  //         leavingDrone.style.display = "none";
  //         spaceRegionState[curLocation[0]][curLocation[1]].hasDrone = false;
  //         console.log("leavingDrone.style.display", leavingDrone.style.display);
  //         spaceRegionState[newX][newY].hasDrone = true;
  //         console.log("leavingDrone", leavingDrone);
  //         drone.x = newX;
  //         drone.y = newY;

  //         spaceRegionState[x][y].hasDrone = false;
  //         const newDroneId = `drone-${newX}-${newY}`;
  //         const newDrone = document.getElementById(newDroneId);
  //         newDrone.style.display = "block";

  //         const nextId = `${newX}-${newY}`;
  //         const nextVisitingSquare = document.getElementById(nextId);
  //         console.log("nextVisitingSquare", nextVisitingSquare);
  //         nextVisitingSquare.style.backgroundColor = "yellow";

  //         console.log("---square", square);
  //         if (square.hasSun) {
  //           const sunId = `sun-${newX}-${newY}`;
  //           const visitingSun = document.getElementById(sunId);
  //           visitingSun.style.display = "block";

  //           const explosionId = `explosion-${newX}-${newY}`;
  //           const visitingExplosion = document.getElementById(explosionId);
  //           visitingExplosion.style.display = "block";

  //           console.log("suuuuu exsit ");
  //           drone.state = 0; // crashed
  //           return;
  //         } else if (square.hasDrone) {
  //           const explosionId = `explosion-${newX}-${newY}`;
  //           const visitingExplosion = document.getElementById(explosionId);
  //           visitingExplosion.style.display = "block";

  //           drone.state = 0; // crashed
  //           return;
  //         } else if (square.hasStar) {
  //           const starId = `star-${newX}-${newY}`;
  //           const visitingStar = document.getElementById(starId);
  //           visitingStar.style.display = "block";

  //           square.hasDrone = true;
  //           square.explored = true;

  //           spaceRegionState[newX][newY].explored = true;

  //           updateSpaceRegionState(spaceRegionState);
  //           console.log("mew drone", drone);
  //         } else {
  //           console.log("nothing here continuye", drone);
  //         }
  //       })(move),
  //       move * 50
  //     );
  //     move++;
  //   }
  //   console.log("out of while loop");
  // };

  const visualizePathNodes = (pathNodes, droneStates) => {
    console.log("----------------------here");
    for (let i = 0; i < pathNodes.length; i++) {
      setTimeout(() => {
        console.log("hereiiiiiiiiiiiii", i);
        const [x, y] = pathNodes[i];
        const droneState = droneStates[i];
        console.log(
          "-----------x here",
          x,
          y,
          "---------droneState",
          droneState
        );
        const droneX = droneState.x;
        const droneY = droneState.y;
        if (i > 0) {
          const prevDroneX = droneStates[i - 1].x;
          const prevDroneY = droneStates[i - 1].y;
          const prevDroneId = `drone-${prevDroneX}-${prevDroneY}`;
          const visitingDrone = document.getElementById(prevDroneId);
          visitingDrone.style.display = "none";
        }
        const droneId = `drone-${droneX}-${droneY}`;
        const visitingDrone = document.getElementById(droneId);
        visitingDrone.style.display = "block";

        switch (droneState.status) {
          case "SUN":
            console.log("hiiiiiiiiii");
            const sunId = `sun-${droneX}-${droneY}`;
            const visitingSun = document.getElementById(sunId);
            visitingSun.style.display = "block";

          case "STAR":
            const starId = `star-${droneX}-${droneY}`;
            const visitingStar = document.getElementById(starId);
            visitingStar.style.display = "block";
          case "WALL":

          case "DRONE":

          // const explosionId = `explosion-${droneX}-${droneY}`;
          // const visitingExplosion = document.getElementById(explosionId);
          // visitingExplosion.style.display = "block";
          // const sunId = `sun-${droneX}-${droneY}`;
          // const visitingSun = document.getElementById(sunId);
          // visitingSun.style.display = "block";

          // const explosionId = `explosion-${droneX}-${droneY}`;
          // const visitingExplosion = document.getElementById(explosionId);
          // visitingExplosion.style.display = "block";

          case "PASS":
        }

        const id = `${x}-${y}`;

        const visitingSquare = document.getElementById(id);
        visitingSquare.style.backgroundColor = "yellow";
      }, i * 500);
    }
  };

  const eachRun = (spaceRegionState) => {
    drones.forEach((drone) => {
      const droneId = `drone-${drone.x}-${drone.y}`;
      const Drone = document.getElementById(droneId);
      Drone.style.display = "block";
    });

    for (let i = 0; i < drones.length; i++) {
      const { path, droneStates } = droneAction(drones[i], spaceRegionState, 0);
      console.log(
        "PathNodes",
        path,
        "-----dronestate",
        drones[i].state,
        "---------droneStates",
        droneStates
      );
      setCurrentDroneState(droneStates);
      visualizePathNodes(path, droneStates);
    }
  };

  const startSimulation = () => {
    eachRun(spaceRegionState);
  };

  return (
    <div>
      <div id="header">
        <span className="bombs-remaining digital">{initialStarNumber}</span>
        {/* <Timer isRunning={isRunning} /> */}
        {currrentDroneState && <DroneStates droneStates={currrentDroneState} />}
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
