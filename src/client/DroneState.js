import React from "react";

const DroneStates = ({ droneStates }) => {
  return (
    <div>
      {droneStates.map((drone) => {
        return <div>drone event: {drone.status}</div>;
      })}
    </div>
  );
};

export default DroneStates;
