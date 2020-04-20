import React, { useState, useEffect, useRef } from 'react';
import droneImg from './drone.svg'
import logo from './download.jpeg';
// public enum Direction {
//     north(0, 1, '\u2191'), northeast(1, 1, '\u2197'),
//             east(1, 0, '\u2192'), southeast(1, -1, '\u2198'),
//             south(0, -1, '\u2193'), southwest(-1, -1, '\u2199'),
//             west(-1, 0, '\u2190'), northwest(-1, 1, '\u2196');

//     private int x;
//     private int y;
//     private char arrow;
//     Direction(int x, int y, char arrow) {
//         this.x = x;
//         this.y = y;
//         this.arrow = arrow;
//     }
//     public int moveX() {
//         return x;
//     }

//     public int moveY() {
//         return y;
//     }

//     public char getArrow() {
//         return arrow;
//     }

//    Map<String, Direction> map = new HashMap<>();





//    public Direction findDirection(String dir) {}



// }


const Drone  = () => {
    const [droneX, updateDroneX] = useState()
    const [droneY, uodateDroneY] = useState()
    const [direction, updateDirection] = useState()
    const [strategy, setStrategy] = useState()
    const status = 1;
    // const SquasurroundingStates = new SquareState[3][3]; // start from north, clockwise
    const collectedStar = 0;
//     const id = 1
//    const nextAction;
//    const actionSave;

    // const reward = new int[3][3];

    //    public enum Action {steer, thrust, scan, pass}
    // constructor
    // public Drone(Integer droneX, Integer droneY, Direction direction, int strategy, int id) {
    //     this.droneX = droneX;
    //     this.droneY = droneY;
    //     this.direction = direction;
    //     this.strategy = strategy;
    //     this.id = id;
    //     this.nextAction = null;
    //     this.actionSave = new ArrayList<>();
    // }

    // public void setStatus(DroneCondition status) {
    //     this.status = status;
    // }

    // public int getDroneX() {
    //     return droneX;
    // }

    // public int getDroneY() {
    //     return droneY;
    // }

    // public int getId() {
    //     return id;
    // }


    // public DroneCondition getStatus() {
    //     return status;
    // }

    // public Direction getDirection() {
    //     return direction;
    // }

    // public Action getNextAction() {
    //     return this.nextAction;
    // }

    // public void setNextAction(Action nextAction) {
    //     this.nextAction = nextAction;
    //     actionSave.add(nextAction);
    // }

    // public int getStrategy() {
    //     return strategy;
    // }

    // public SquareState getSurroundingStateXY(int x, int y) {
    //     return surroundingStates[x][y];
    // }

    // public int getCollectedStar() {
    //     return collectedStar;
    // }

    // public void collectedStar() {
    //     collectedStar++;
    // }

   const executeNextAction = (space) => {
        switch (nextAction) {
            case steer:
                this.direction = nextAction.getDirection();
            case thrust:
                this.thrust(space);
            case scan:
                this.scan(space);
            case pass:
                this.pass();
        }
    }

    const updateSurronding = (space) => {
        scan(space);
    }


    const thrust = (space) => {
        const steps = nextAction.getSteps();
        for (let i = 1; i <= steps; i++) {
            let oldDroneX = droneX;
            let oldDroneY = droneY;
            droneX += direction.moveX();
            droneY += direction.moveY();
            if (droneY >= 0 && droneX >= 0 && droneX < space.getWidth() && droneY < space.getHeight()) {
                switch (space.getSquareState(droneX, droneY)) {
                    case star:
                        collectedStar();
                        space.setSquareStateEmpty(oldDroneX, oldDroneY);
                        space.setSquareStateDrone(droneX, droneY);
                        break;
                    case barrier:
                        return;
                    case empty:
                        space.setSquareStateEmpty(oldDroneX, oldDroneY);
                        space.setSquareStateDrone(droneX, droneY);
                        break;
                    case drone:
                        status = DroneCondition.crashed;
                        // find another drone;
                        // how to find another drone
                        space.setSquareStateEmpty(oldDroneX, oldDroneY);
                        space.setSquareStateEmpty(droneX, droneY);
                        // add drone that if this is the space is empty.
                        return;
                    case sun:
                        status = DroneCondition.crashed;
                        space.setSquareStateEmpty(oldDroneX, oldDroneY);
                        return;
                    default:
                        break;
                }
            } else {
                droneX = oldDroneX;
                droneY = oldDroneY;
            }


        }
    }

    const scan = (space) => {
        for (let i = -1; i <= 1; i++) {
            for (let j = -1; j <= 1; j++) {
                surroundingStates[i + 1][j + 1] = space.getSquareState(droneX + i, droneY + j);
            }
        }
    }

    // public void pass() {
    // }


   const getStarDirection = () => {
        let current = null;
        for (let i = -1; i <= 1; i++) {
            for (let j = -1; j <= 1; j++) {
                let hasStar = surroundingStates[i + 1][j + 1] == SquareState.star;
                if (hasStar) {
                    if (i == 0 && j == 1) {
                        current = Direction.north;
                    } else if (i == 1 && j == 1) {
                        current = Direction.northeast;
                    } else if (i == 1 && j == 0) {
                        current = Direction.east;
                    } else if (i == 1 && j == -1) {
                        current = Direction.southeast;
                    } else if (i == 0 && j == -1) {
                        current = Direction.south;
                    } else if (i == -1 && j == -1) {
                        current = Direction.southwest;
                    } else if (i == -1 && j == 0) {
                        current = Direction.west;
                    } else if (i == -1 && j == 1) {
                        current = Direction.northwest;
                    }

                }
            }
        }

        return current;
    }


    const getEmptySafeDirection = () => {
        let current = null;
        let i = 0;
        while (current == null || !directionSafe(current) || i < 1000) {
            current = Direction.values()[new Random().nextInt(Direction.values().length)];
            i++;
        }
        return current;
    }


    const directionSafe = (direction) => {
        if (surroundingStates[direction.moveX() + 1][direction.moveY() + 1] == SquareState.empty) {
            return true;
        } else {
            return false;
        }
    }

    const hasStarSurrounding = () => {
        for (let i = -1; i <= 1; i++) {
            for (let j = -1; j <= 1; j++) {
                const hasStar = surroundingStates[i + 1][j + 1] == SquareState.star;
                if (hasStar) {
                    return true;
                }
            }
        }
        return false;
    }

    const canvasRef = useRef(null);

    const [drone, updateDrone] = useState({
        x: 0,
        y: 0,
        radius: 20
      })

    //   const draw = () => {
    //     const ctx = canvasRef.current.getContext("2d");
    //     console.log('---ctx', ctx)
    //     ctx.fillStyle = "green";
    //     ctx.beginPath();
    //     ctx.arc(drone.x, drone.y,                        
    //             drone.radius, 0, 2 * Math.PI);
    //     ctx.fill();
    //     ctx.stroke();
    // }
    
    useEffect(
        () => {
        // fetchData()
        // draw()
      }, [])

      
    //   <canvas ref={canvasRef} width={450} height={650} style={{position: 'absolute'}}/>

    return (
  
        <img src={logo} style={{ width: '50px', height: '50px'}} />
    )

}


export default Drone