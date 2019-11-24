import React, { Component } from 'react';
import './app.css';
import Switches from './commons/switch.js'
import ReactImage from './react.png';
import Menu from './components/MenuHeaderComponent.js';
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
        }, 70);
    }

  render() {
    return (
      <div className="container-fluid">
      	<div className="row">
      		<div className={"col-md-12 bg-secondary"}>
            <h1 className={"text-white"}>Osmosi</h1>
          </div>
      	</div>
      	<div className={"row"}>
      		<div className="col-md-6">
            <ul className={"list-group border-0"}>
              <li className={"list-group-item border-0"}><InstrCmp name='All Body' /></li>
              <li className={"list-group-item border-0"}><InstrCmp name="Hands" /></li>
              <li className={"list-group-item border-0"}><InstrCmp name="Spine" /></li>
              <li className={"list-group-item border-0"}><InstrCmp name="Feet" /></li>
            </ul>
          </div>
      		<div className={"col-md-6"}>
            <Monitor bodies={this.state.bodies} />
          </div>
        </div>
      </div>
    );
  }
}

export default App;
