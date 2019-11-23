import React, { Component } from 'react';
import './app.css';
import ReactImage from './react.png';
import InstrCtrPnl from './components/InstrumentsControllerPanel.js';
import BodiesCtrPnl from './components/BodiesControllerPanel.js';
import BodyComponent from './components/BodyComponent.js';
import InstrCmp from './components/InstrumentComponent.js';
import MstSoundComponent from './components/MasterSoundComponent.js'
import Monitor from './components/MonitorComponent.js';
import data from './lmac1.json';


//const json = require('./jse.json');

var index = 0;

function Kinect() {
  console.log('hello');
}


class App extends Component {

  constructor(props) {

    super(props);
    this.state = {bodies:[], index:1};
  }

  componentDidMount() {
        setInterval(() => {
            var newIndex = this.state.index + 1;
            var body = data[newIndex];
            //console.log(body[0].bodyIndex);
          //  console.log(body[0].joints);
            this.setState({bodies:data[newIndex], index: newIndex})
        }, 0.015);
    }

  render() {
    return (
      <div>
      <Monitor bodies={this.state.bodies} />
      </div>
    );
  }
}

export default App;
