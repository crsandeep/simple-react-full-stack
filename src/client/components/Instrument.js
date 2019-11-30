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

import OnOff from '../commons/switch.js';
import InstrumentSelector from '../commons/instrumentSelector.js';
import NoteSelector from '../commons/noteSelector.js';
import ModeSelector from '../commons/modeSelector.js';
import DiscreteSlider from '../commons/volumeSelector.js';

class Instrument extends Component {
  constructor(props){
      super(props);
      this.onChangeVolumeHandler = this.onChangeVolumeHandler.bind(this);
      this.onChangeNoteHandler = this.onChangeNoteHandler.bind(this);
      this.onChangeModeHandler = this.onChangeModeHandler.bind(this);
      this.onChangeInstrumentHandler = this.onChangeInstrumentHandler.bind(this);
      this.onOnOffHandler = this.onOnOffHandler.bind(this);
    }

  // Triggered by the volume selector
  onChangeVolumeHandler(e,value){
    this.props.onChangeVolume(value);
  }

  // Triggered by the note selector
  onChangeNoteHandler(e){
    this.props.onChangeNote(e.target.value);
  }

  onChangeModeHandler(e){
    this.props.onChangeMode(e.target.value);
  }

  // Triggered by the instrument selector
  onChangeInstrumentHandler(e){
    this.props.onChangeInstrument(e.target.value);
  }

  // Triggered by the Switch on/of selector
  onOnOffHandler(e){
    this.props.onOnOff(e.target.checked);
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
                    value={this.props.instrument.on}
                  />
                </div>
                <div className={"col-md-4"}>
                  <InstrumentSelector
                    onChange={()=> this.onChangeInstrumentHandler}
                    value={this.props.instrument.type}
                  />
                </div>
                <div className={"col-md-5"}>
                  <ModeSelector
                    onChange={()=>this.onChangeModeHandler}
                    value={this.props.instrument.mode}
                  />
                </div>
              </div>
            </li>
            <li className={"list-group-item border-0"}>
              <div className={"col-md-12"}>
                <DiscreteSlider
                  onChangeCommitted={()=>this.onChangeVolumeHandler}
                  value={this.props.instrument.volume*10}
                />
              </div>
            </li>
          </ul>
      </div>
      )
    }
}

export default Instrument;
