import React, { Component } from 'react';
import './app.css';
import ReactImage from './react.png';
import InstrumentsPanel from './components/InstrumentsPanel.js';
import MstSoundComponent from './components/MasterSoundComponent.js';
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

// function channel (name) {
//   var instrument = {
//   'name' : name,
//   'switch': true,
//   'type' : 'Piano',
//   'mode' : 'Single',
//   'scale': 'Major',
//   'note' : 'C',
//   'volume' : 0.5,
//   'sensistivy' : 10
// }
//   return instrument;
// };

const instrumentTypeList = {classic_guitar:'Classic Guitar', water_drop:'Water Drop'};
const instrumentModeList = {random:'Random', scale:'Scale'};
const instrumentChannelName ={body:'Body', hands:'Hands', feet: 'Feet'};

function Channel (name) {
  this.name = name;
  this.on = false;
  this.type = instrumentTypeList.classic_guitar;
  this.mode = 'Single';
  this.scale = 'Major';
  this.note = 'C';
  this.pitch = '3'
  this.volume = 0.5;
  this.mode = instrumentModeList.random;
  this.sensitivity = 1;
};

var body = new Channel(instrumentChannelName.body);
var hands = new Channel(instrumentChannelName.hands);
var feet = new Channel(instrumentChannelName.feet);

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

function bodyParam () {
this.BodyIndex= '';
this.cx= 0;
this.cy= 0;
this.hlx=0;   //left hand x
this.hly=0    //right habd y
this.hrx=0;   //left hand x
this.hry=0    //right habd y
this.hocx=0;  //hand openess x
this.hocy=0;  //hand openess y
this.Scx=0;
this.Scy=0;
this.Fcx=0;
this.Fcy=0
}


class App extends Component {
    constructor(props) {
    super(props);
    this.audioContext = new AudioContext();
    //this.setGuitar();
    this.bodyParam = new bodyParam();
    this.state = {bodies:[], index:1, instruments:[body,hands,feet], bodyParam:this.bodyParam}
  }

  componentDidMount() {
      setInterval(() => {
          var newIndex = this.state.index + 1;
          var body = data[newIndex];
          //console.log(body[0].bodyIndex);
        //  console.log(body[0].joints);
          this.setState({bodies:data[newIndex], index: newIndex})
      }, 300);
    }

    newBodyParamHandler(bodyParam){
      //console.log(bodyParam.cx);
      this.bodyParam= bodyParam;
    }

  render() {
    return (
      <div className="container-fluid">
        <MstSoundComponent
          audioContext = {this.audioContext}
          instruments = {this.state.instruments}
          bodyParam = {this.bodyParam}
          instrumentTypeList={instrumentTypeList}
          instrumentModeList={instrumentModeList}
          instrumentChannelName={instrumentChannelName}
        />
      	<div className="row">
      		<div className={"col-md-12 bg-secondary"}>
            <h1 className={"text-white"}>Osmosi</h1>
          </div>
      	</div>
      	<div className={"row"}>
      		<InstrumentsPanel instruments={this.state.instruments} instrumentTypeList={instrumentTypeList}/>
      		<div className={"col-md-6"}>
            <Monitor
              newBodyParameter={(value)=>newBodyParameterHandle(value)}
              bodies={this.state.bodies}
              bodyParam = {this.state.bodyParam}
              newBodyParam = {(value)=> this.newBodyParamHandler(value)}
            />
          </div>
        </div>
      </div>
    );
  }
}

export default App;



// -----------

class SoundBox extends Component {
    constructor(props) {
    super(props);
  }

  render() {
    return(
      <div>
        SoundBox
      </div>
    )
  }
}
