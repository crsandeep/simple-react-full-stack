import React, { useState, useEffect } from "react";
import Drone from "./Drone";

import logo from "./download.jpeg";
import star from "./start.jpeg";
import exploded from "./exploed.jpeg";

const Square = ({ squareState, x, y }) => {
  // console.log('--squareState', squareState, x , y)
  const { explored, hasSun, hasStar, hasDrone, hasBarrier } = squareState;
  // console.log('explored, hasSun, hasStar, hasDrone, hasBarrie', explored, hasSun, hasStar, hasDrone, hasBarrier)
  const sunId = `sun-${x}-${y}`;
  const starId = `star-${x}-${y}`;
  const droneId = `drone-${x}-${y}`;
  const explosionId = `explosion-${x}-${y}`;

  const Sun = () => (
    <img
      id={sunId}
      src={exploded}
      style={{ display: "none", width: "50px", height: "50px" }}
    />
  );

  const Drone = () => (
    <img
      id={droneId}
      src={logo}
      style={{
        width: "50px",
        height: "50px",
        display: "none",
      }}
    />
  );

  const Star = () => (
    <img
      id={starId}
      src={star}
      style={{
        width: "50px",
        height: "50px",
        display: "none",
      }}
    />
  );

  const Explosion = () => (
    <img
      id={explosionId}
      src={exploded}
      style={{
        width: "50px",
        height: "50px",
        display: "none",
      }}
    />
  );

  const id = `${x}-${y}`;
  return (
    <td
      id={id}
      style={{
        width: "100px",
        height: "100px",

        border: "1px solid grey",
      }}
    >
      <div>
        {Drone()}
        {Sun()}
        {Star()}
        {Explosion()}
      </div>
    </td>
  );
};

export default Square;

// 5 - X
// 4 - Y
// 3 - drones
// 1,2,north,1 - direstion
// 0,1,northeast,1
// 3,1,west,1
// 3 - sun
// 1,1
// 1,3
// 3,0
// 3 simulation runs
