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

import OnOff from '../commons/switch.js'
import InstrumentSelector from '../commons/instrumentSelector.js'
import NoteSelector from '../commons/noteSelector.js'
import DiscreteSlider from '../commons/volumeSelector.js'

class Instrument extends Component {
  constructor(props){
      super(props);
      this.onChangeVolumeHandler = this.onChangeVolumeHandler.bind(this);
      this.onChangeNoteHandler = this.onChangeNoteHandler.bind(this);
      this.onChangeInstrumentHandler = this.onChangeInstrumentHandler.bind(this);
      this.onOnOffHandler = this.onOnOffHandler.bind(this);
    }

  // Triggered by the volume selector
  onChangeVolumeHandler(e,value){
    this.props.onChangeVolumeHandler(value);
  }

  // Triggered by the note selector
  onChangeNoteHandler(e){
    this.props.onChangeNoteHandler(e.target.value);
  }

  // Triggered by the instrument selector
  onChangeInstrumentHandler(e){
    this.props.onChangeInstrumentHandler(e.target.value);
  }

  // Triggered by the Switch on/of selector
  onOnOffHandler(e){
    this.props.onOnOffHandler(e.target.checked);
  }


  render() {
    return (
      <div className={"col-12"}>
          <ul className={"list-group border-0"}>
            <li className={"list-group-item bg-secondary text-white"}>{this.props.instrument.name}</li>
            <li className={"list-group-item border-0"}>
              <div className={"row"}>
                <div className={"col-md-2"}>
                  <OnOff
                    onChange={()=> this.onOnOffHandler}
                    value={this.props.instrument.switch}
                  />
                </div>
                <div className={"col-md-5"}>
                  <InstrumentSelector
                    onChange={()=> this.onChangeInstrumentHandler}
                    value={this.props.instrument.type}
                  />
                </div>
                <div className={"col-md-5"}>
                  <NoteSelector
                    onChange={()=>this.onChangeNoteHandler}
                    value={this.props.instrument.note}
                  />
                </div>
              </div>
            </li>
            <li className={"list-group-item border-0"}>
              <div className={"col-md-12"}>
                <DiscreteSlider
                  onChangeCommitted={()=>this.onChangeVolumeHandler}
                  value={this.props.instrument.volume}
                />
              </div>
            </li>
          </ul>
      </div>
      )
    }
}

export default Instrument;
