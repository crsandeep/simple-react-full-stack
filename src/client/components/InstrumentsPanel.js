//Contains all the instrument
import React, { Component } from 'react';
import ReactDOM from 'react-dom';
import Instrument from './Instrument.js'


class InstrumentsPanel extends Component {

  constructor(props){
      super(props);
      this.state = {instruments:this.props.instruments};
  }

  // Triggered by the change of volume
  onChangeVolumeHandler (i,v) {
    var value = v/10;
    const instruments = this.state.instruments.slice();
    const instrument = instruments[i];
    if(instrument.volume != value){
      instrument.volume = value;
      instruments[i] = instrument;
      this.setState({instruments:instruments});
    }
    console.log('******Instrument Panel **********');
    console.log('Volume of:', i);
    console.log('Set With Value:', value);
  }

  // Triggered by the change of // NOTE:
  onChangeNoteHandler (i,value) {
    const instruments = this.state.instruments.slice();
    const instrument = instruments[i];
    if(instrument.note != value){
      instrument.note = value;
      instruments[i] = instrument;
      this.setState({instruments:instruments});
    }
    console.log('******Instrument Panel **********');
    console.log('Note of:', i);
    console.log('Set With Value:', value);
  }

  onChangeModeHandler (i,value) {
    const instruments = this.state.instruments.slice();
    const instrument = instruments[i];
    if(instrument.mode != value){
      instrument.mode = value;
      instruments[i] = instrument;
      this.setState({instruments:instruments});
    }
    console.log('******Instrument Panel **********');
    console.log('Mode of:', i);
    console.log('Set With Value:', value);
  }

  // Triggered by the change of instrument type
  onChangeInstrumentHandler (i,value) {
    const instruments = this.state.instruments.slice();
    const instrument = instruments[i];
    if(instrument.type != value){
      instrument.type = value;
      instruments[i] = instrument;
      this.setState({instruments:instruments});
    }
    console.log('******Instrument Panel **********');
    console.log('Instrument type of:', i);
    console.log('Set to:', value);
  }

  // Triggered by the switch on/off
  onOnOffHandler (i, value) {
    const instruments = this.state.instruments.slice();
    const instrument = instruments[i];
    if(instrument.on != value){
      instrument.on = value;
      instruments[i] = instrument;
      this.setState({instruments:instruments});
    }
    console.log('******Instrument Panel **********');
    console.log('Instrument On of:', i);
    console.log('Set to:', value);
  }

  renderInstrument(i){
    return(
      <Instrument
        onOnOff={(value)=>this.onOnOffHandler(i,value)}
        onChangeInstrument={(value) => this.onChangeInstrumentHandler(i,value)}
        onChangeNote={(value)=>this.onChangeNoteHandler(i,value)}
        onChangeMode={(value)=>this.onChangeModeHandler(i,value)}
        onChangeVolume={(value)=>this.onChangeVolumeHandler(i,value)}
        instrument={this.state.instruments[i]}
        instrumentTypeList = {this.props.instrumentTypeList}
      />
    );
  }

  render() {
    return (
        <ul className={"list-group border-0"}>
          <li className={"list-group-item border-0"}>{this.renderInstrument(0)}</li>
          <li className={"list-group-item border-0"}>{this.renderInstrument(1)}</li>
          <li className={"list-group-item border-0"}>{this.renderInstrument(2)}</li>
        </ul>
    );
  }
}



export default InstrumentsPanel;
