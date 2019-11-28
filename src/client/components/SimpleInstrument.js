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
import NoteSelector from '../commons/noteSelector.js'
import DiscreteSlider from '../commons/volumeSelector.js'

class Instrument extends Component {

  constructor(props){
      super(props);
      this.instrument = this.props.instrument;
  }

  componentDidMount(){
    console.log('Rendering Instruments')
  }

  onChangeVolume (e) {
    // e.changeSource = e.currentTarget.name
    // e.changeType = 'Volume';
    // e.changeValue = e.target.innerText;
    this.instrument.volume = e.target.innerText;
    this.props.handleChange();
  }

  onChangeSwitch (e) {
    // e.changeSource = e.currentTarget.name
    // e.changeType = 'Switch';
    // e.changeValue = e.target.checked;
    this.instrument['Switch'] = e.target.checked;
  }

  onChangeInstrument (e) {
    //console.log(e.target.value);
    // e.changeSource = e.currentTarget.name
    // e.changeType = 'Instrument';
    // e.changeValue = e.target.value;
    this.instrument['Type'] = e.target.value;
  }

  onChangeNote (e) {
    // e.changeSource = e.currentTarget.name
    // e.changeType = 'Note';
    // e.changeValue = e.target.value;
    this.instrument['Note'] = e.target.value;
  }


  render() {
    return (
						<div id={this.instrument.name} className={"col-12"}>
                <ul className={"list-group border-0"}>
                  <li className={"list-group-item bg-secondary text-white"}>{this.instrument.name}</li>
                  <li className={"list-group-item border-0"}>
                    <div className={"row"}>
                      <div onChange={this.onChangeSwitch} name={this.name} className={"col-md-2"}>
                        <Switches/>
                      </div>
                      <div onChange={this.onChangeInstrument} name={this.name} className={"col-md-5"}>
                        <NativeSelects />
                      </div>
                      <div  onChange={this.onChangeNote} name={this.name} className={"col-md-5"}>
                        <NoteSelector />
                      </div>
                    </div>
                  </li>
                  <li className={"list-group-item border-0"}>
                    <div onMouseUp={this.onChangeVolume} name={this.name} className={"col-md-12"}>
                      <DiscreteSlider />
                    </div>
                  </li>
                </ul>
            </div>
      )
    }
}

export default Instrument;
