// One for
// - Only Hands
// - Spine
// - Full Body
// - Only Feet
//
// Each one controlls
// - Type of instrument
// - Volume
// - On and Off
// - Sensitivity
// - Effetc


import React, { Component } from 'react';
import ReactDOM from 'react-dom';

import Switches from '../commons/switch.js'
import NativeSelects from '../commons/selector.js'
import DiscreteSlider from '../commons/volumeSelector.js'



class InstrCmp extends Component {

  constructor(props){
      super(props);
      this.name = this.props.name;
  }

  render() {
    return (
						<div className={"col-12"}>
                <ul className={"list-group border-0"}>
                  <li className={"list-group-item bg-secondary text-white"}>{this.name}</li>
                  <li className={"list-group-item border-0"}>
                    <div className={"row"}>
                      <div className={"col-md-2"}>
                        <Switches/>
                      </div>
                      <div className={"col-md-5"}>
                        <NativeSelects />
                      </div>
                      <div className={"col-md-5"}>
                        <NativeSelects />
                      </div>
                    </div>
                  </li>
                  <li className={"list-group-item border-0"}><DiscreteSlider/></li>
                </ul>
            </div>
      )
    }
}

export default InstrCmp;
