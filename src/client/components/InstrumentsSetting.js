import React, { Component } from 'react';
import ReactDOM from 'react-dom';



class InstrumentsSetting extends Component {
  constructor(props){
      super(props);
    }

    render() {
      return (
        <div>
        <ul className={"list-group border-0"}>
          <li className={"list-group-item border-0 text-left p-0"}>
                <b>Body</b>
          </li>
          <li className={"list-group-item border-0 text-left p-0"}>
              Volume: 0.5
          </li>
          <li className={"list-group-item border-0 text-left p-0"}>
              Classic Guitar
          </li>
          <li className={"list-group-item border-0 text-left p-0"}>
              Scale
          </li>
          <li className={"list-group-item border-0 text-left p-0"}>
                <b>Hands</b>
          </li>
          <li className={"list-group-item border-0 text-left p-0"}>
              Volume: 0.5
          </li>
          <li className={"list-group-item border-0 text-left p-0"}>
              Water Drop
          </li>
          <li className={"list-group-item border-0 text-left p-0"}>
              Scale
          </li>
          <li className={"list-group-item border-0 text-left p-0"}>
                <b>Feet</b>
          </li>
          <li className={"list-group-item border-0 text-left p-0"}>
              Volume: 0.5
          </li>
          <li className={"list-group-item border-0 text-left p-0"}>
              Classic Guitar
          </li>
          <li className={"list-group-item border-0 text-left p-0"}>
              Scale
          </li>
        </ul>
        </div>
      );
    }
  }



  export default InstrumentsSetting;
