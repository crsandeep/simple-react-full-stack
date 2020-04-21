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

export const droneAction = (drone, spaceRegionState, move) => {
  let path = [[drone.x, drone.y]];
  const droneStates = [
    {
      ...drone,
      status: "INIT",
    },
  ];
  helper(spaceRegionState, path, move, droneStates);
  return { path, droneStates };
};
const findUnExplored = (spaceRegionState) => {
  let unExplored = [];
  spaceRegionState.forEach((row) => {
    row.forEach((node) => {
      if (!node.explored) {
        unExplored.push(node);
      }
    });
  });
  return unExplored;
};

const helper = (spaceRegionState, path, move, droneStates) => {
  while (
    drone.state === 1 &&
    move < 500 &&
    findUnExplored(spaceRegionState).length
  ) {
    const nextDir = DIRS_MOVES[Math.floor(Math.random() * 8)];
    const dirName = Object.keys(nextDir)[0];
    drone.dir = dirName;
    const dirXY = nextDir[dirName];
    const newX = Number(drone.x) + Number(dirXY[0]);
    const newY = Number(drone.y) + Number(dirXY[1]);

    if (drone.state === 0) {
      console.log("yyyyyyyyy------------------drone head");
      return { path, droneStates };
    }
    if (
      newY < 0 ||
      newX < 0 ||
      newY >= spaceRegionState.length ||
      newX >= spaceRegionState[0].length
    ) {
      droneStates.push({
        ...drone,
        status: "WALL",
      });

      move++;
      continue;
    }

    if (spaceRegionState[newY][newX].explored) {
      droneStates.push({
        ...drone,
        status: "PASS",
      });
    }

    path.push([newX, newY]);

    const square = spaceRegionState[newX][newY];
    spaceRegionState[newX][newY].explored = true;
    console.log("sssssssss", spaceRegionState[newX][newY]);
    drone.x = newX;
    drone.y = newY;

    if (square.hasSun) {
      console.log("------------------drone sun");
      droneStates.push({
        ...drone,
        state: 0,
        status: "SUN",
      });

      return { path, droneStates };
    } else if (square.hasDrone) {
      console.log("------------------drone drone");
      droneStates.push({
        ...drone,
        state: 0,
        status: "DRONE",
      });

      return { path, droneStates };
    } else if (square.hasStar) {
      droneStates.push({
        ...drone,
        status: "STAR",
      });
      //   console.log("---------------------------------------star");
    }
  }
};

const space = [
  [
    {
      explored: false,
      hasSun: false,
      hasStar: false,
      hasDrone: false,
      hasBarrier: false,
    },
    {
      explored: false,
      hasSun: false,
      hasStar: false,
      hasDrone: false,
      hasBarrier: false,
    },
    {
      explored: false,
      hasSun: false,
      hasStar: false,
      hasDrone: false,
      hasBarrier: false,
    },
    {
      explored: false,
      hasSun: false,
      hasStar: true,
      hasDrone: false,
      hasBarrier: false,
    },
    {
      explored: false,
      hasSun: false,
      hasStar: false,
      hasDrone: false,
      hasBarrier: false,
    },
  ],
  [
    {
      explored: false,
      hasSun: false,
      hasStar: true,
      hasDrone: false,
      hasBarrier: false,
    },
    {
      explored: true,
      hasSun: false,
      hasStar: true,
      hasDrone: true,
      hasBarrier: false,
    },
    {
      explored: false,
      hasSun: false,
      hasStar: false,
      hasDrone: false,
      hasBarrier: false,
    },
    {
      explored: false,
      hasSun: false,
      hasStar: true,
      hasDrone: false,
      hasBarrier: false,
    },
    {
      explored: false,
      hasSun: false,
      hasStar: true,
      hasDrone: false,
      hasBarrier: false,
    },
  ],
  [
    {
      explored: false,
      hasSun: false,
      hasStar: true,
      hasDrone: false,
      hasBarrier: false,
    },
    {
      explored: false,
      hasSun: false,
      hasStar: true,
      hasDrone: false,
      hasBarrier: false,
    },
    {
      explored: false,
      hasSun: false,
      hasStar: false,
      hasDrone: false,
      hasBarrier: false,
    },
    {
      explored: false,
      hasSun: false,
      hasStar: true,
      hasDrone: false,
      hasBarrier: false,
    },
    {
      explored: false,
      hasSun: false,
      hasStar: false,
      hasDrone: false,
      hasBarrier: false,
    },
  ],
  [
    {
      explored: false,
      hasSun: false,
      hasStar: true,
      hasDrone: false,
      hasBarrier: false,
    },
    {
      explored: false,
      hasSun: false,
      hasStar: false,
      hasDrone: false,
      hasBarrier: false,
    },
    {
      explored: false,
      hasSun: false,
      hasStar: true,
      hasDrone: false,
      hasBarrier: false,
    },
    {
      explored: false,
      hasSun: false,
      hasStar: true,
      hasDrone: false,
      hasBarrier: false,
    },
    {
      explored: false,
      hasSun: false,
      hasStar: true,
      hasDrone: false,
      hasBarrier: false,
    },
  ],
  [
    {
      explored: false,
      hasSun: false,
      hasStar: true,
      hasDrone: false,
      hasBarrier: false,
    },
    {
      explored: false,
      hasSun: false,
      hasStar: true,
      hasDrone: false,
      hasBarrier: false,
    },
    {
      explored: false,
      hasSun: false,
      hasStar: false,
      hasDrone: false,
      hasBarrier: false,
    },
    {
      explored: false,
      hasSun: false,
      hasStar: true,
      hasDrone: false,
      hasBarrier: false,
    },
    {
      explored: false,
      hasSun: false,
      hasStar: true,
      hasDrone: false,
      hasBarrier: false,
    },
  ],
];

const drone = {
  x: 1,
  y: 1,
  state: 1,
};

console.log(droneAction(drone, space, 0));
