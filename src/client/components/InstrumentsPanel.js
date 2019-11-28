//Contains all the instrument
import React, { Component } from 'react';
import ReactDOM from 'react-dom';
import Instrument from './Instrument.js'


class InstrumentsPanel extends Component {

  constructor(props){
      super(props);
      this.instruments = this.props.instruments;
  }

  renderInstrument(i){
    return(
      <Instrument instrument={this.instruments[i]}/>
    );
  }

  handleChange(i){
    console.log('with:', i);
  }

  render() {
    return (
      <div className="col-md-6">
        <ul className={"list-group border-0"}>
          <li className={"list-group-item border-0"}>{this.renderInstrument(0)}</li>
          <li className={"list-group-item border-0"}>{this.renderInstrument(1)}</li>
        </ul>
      </div>
    );
  }
}



export default InstrumentsPanel;
