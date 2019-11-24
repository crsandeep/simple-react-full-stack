// Contain
// - Volume On/Off
// - Sound On/Off
// - Track On/Off

import React, { Component } from 'react';
import ReactDOM from 'react-dom';



class MstSoundComponent extends Component {
  constructor(props){
      super(props)
  }

  render() {
    return (
      <div className={"row border mt-1 mr-1 mb-3"}>
        <div className={"row col-12 ml-1 mt-2"}>
          <h6>Sound Type</h6>
        </div>
        <div className={"row col-12 ml-1 mb-3"}>
          <button type="button" className={"mr-1 btn btn-small btn-outline-dark"}>Instrument 1</button>
          <button type="button" className={"btn btn-small btn-outline-dark"}>Instrument 2</button>
          <button type="button" className={"btn btn-small btn-outline-dark"}>Guitar</button>
          <button type="button" className={"btn btn-small btn-outline-dark"}>Water Bubble</button>
        </div>
      </div>
    )
  }
}

export default MstSoundComponent;
