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


import MstSoundComponent from './MasterSoundComponent.js';



class InstrCmp extends Component {

  constructor(props){
      super(props);
      this.instrument = this.props.instrument;
      this.state = {instrument: this.instrument};
      this.name = this.props.name;
      this.onChangeVolume = this.onChangeVolume.bind(this);
      this.onChangeSwitch = this.onChangeSwitch.bind(this);
      this.onChangeInstrument = this.onChangeInstrument.bind(this);
      this.onChangeNote = this.onChangeNote.bind(this);
  }

  componentDidMount(){
    console.log('Rendering Instruments')
  }

  onChangeVolume (e) {
    // e.changeSource = e.currentTarget.name
    // e.changeType = 'Volume';
    // e.changeValue = e.target.innerText;
    this.instrument['Volume'] = e.target.innerText;
    this.setState({instrument:this.instrument});
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
						<div id={this.name} className={"col-12"}>
                <ul className={"list-group border-0"}>
                  <li className={"list-group-item bg-secondary text-white"}>{this.name}</li>
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
                  <li className={"list-group-item border-0"}>
                    <div onMouseUp={this.onChangeVolume} name={this.name} className={"col-md-12"}>
                      <MstSoundComponent instrument = {this.instrument} />
                    </div>
                  </li>
                </ul>
            </div>
      )
    }
}

export default InstrCmp;
