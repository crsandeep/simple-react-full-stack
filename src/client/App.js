import React, { Component } from 'react';
import './app.css';
import ReactImage from './react.png';
import InstrumentsPanel from './components/InstrumentsPanel.js';
import Monitor from './components/MonitorComponent.js';
import data from './lmac1.json';

var index = 0;
//var mss= new MstSoundComponent();

function Kinect() {
  console.log('hello');
}

// Define the name of the instruments  based on their link to the body's parts
var instrumentName =['Body', 'Hands', 'Feet', 'Spine'];

// Each instruments defines is own 'sound' channel

function channel (name) {
  var instrument = {
  'name' : name,
  'switch': true,
  'type' : 'Piano',
  'mode' : 'Single',
  'scale': 'Major',
  'note' : 'C',
  'volume' : 5,
  'sensistivy' : 10
}
  return instrument;
};

function Channel (name) {
  this.name = name;
  this.on = false;
  this.type = 'Piano';
  this.mode = 'Single';
  this.scale = 'Major';
  this.note = 'C';
  this.pitch = '3'
  this.volume = 5;
  this.sensitivity = 1;
};

var body = new Channel('Body');
var hands = new Channel('Hands');


// function bodyParam (bodyIndex) {
//   var value = {
//   'BodyIndex': bodyIndex,
//   'BodyCx': 0,
//   'BodyCy': 0,
//   'HandsCx':0,
//   'HandsCy':0,
//   'SpineCx':0,
//   'SpineCy':0,
//   'FeetCx':0,
//   'FeetCy':0
//   }
//   return value;
// };

var bodyParam = {
'BodyIndex': '',
'BodyCx': 0,
'BodyCy': 0,
'HandsCx':0,
'HandsCy':0,
'SpineCx':0,
'SpineCy':0,
'FeetCx':0,
'FeetCy':0
}


class App extends Component {
    constructor(props) {
    super(props);
    this.state = {bodies:[], index:1, instruments:[body,hands],}
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
      		<InstrumentsPanel instruments={this.state.instruments}/>
      		<div className={"col-md-6"}>
            <Monitor bodies={this.state.bodies} />
          </div>
        </div>
      </div>
    );
  }
}

export default App;
