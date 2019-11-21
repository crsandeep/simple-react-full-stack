import React, { Component } from 'react';
import './app.css';
import ReactImage from './react.png';
import InstrCtrPnl from './components/InstrumentsControllerPanel.js';
import BodiesCtrPnl from './components/BodiesControllerPanel.js';
import BodyComponent from './components/BodyComponent.js';
import InstrCmp from './components/InstrumentComponent.js';
import MstSoundComponent from './components/MasterSoundComponent.js'
import Monitor from './components/MonitorComponent.js'


class App extends Component {

  render() {
    return (
      <div>
      <MstSoundComponent />
      <InstrCtrPnl />
      <InstrCmp />
      <BodiesCtrPnl />
      <div>
      <Monitor />
      <BodyComponent />
      </div>
      </div>
    );
  }
}

export default App;
