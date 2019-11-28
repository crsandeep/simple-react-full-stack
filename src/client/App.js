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
var feet = new Channel('Feet');

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
      }, 70);
    }

    newBodyParamHandler(bodyParam){
      //console.log(bodyParam.cx);
      this.bodyParam= bodyParam;
    }

    // setGuitar (){
    //   var assetsPath = "src/client/audio/guitar/";
    //   //scale: ['C','D','E','G','A'],  //majorPentatonic
    //   var sounds =[
    //       {src:"c3_mf_rr3.wav", id:"c3"},
    //       {src:"c3_mf_rr3.wav", id:"d3"},
    //       {src:"eb3_mf_rr3.wav", id:"e3"},
    //       {src:"gb3_mf_rr3.wav", id:"g3"},
    //       {src:"a3_mf_rr3.wav", id:"a3"},
    //       {src:"c4_mf_rr3.wav", id:"c4"},
    //       {src:"c4_mf_rr3.wav", id:"d4"},
    //       {src:"eb4_mf_rr3.wav", id:"e4"},
    //       {src:"gb4_mf_rr3.wav", id:"g4"},
    //       {src:"a4_mf_rr3.wav", id:"a4"},
    //       {src:"c5_mf_rr3.wav", id:"c5"},
    //       {src:"eb5_mf_rr3.wav", id:"d5"},
    //       {src:"eb5_mf_rr3.wav", id:"e5"},
    //       {src:"gb5_mf_rr3.wav", id:"g5"},
    //       {src:"a5_mf_rr3.wav", id:"a5"},
    //   ];
    //   createjs.Sound.alternateExtensions = ["wav"];	// add other extensions to try loading if the src file extension is not supported
    //   createjs.Sound.addEventListener("fileload", function(event) {
    //     var instance = createjs.Sound.play("c3");
    //   }); // add an event listener for when load is completed
    //   createjs.Sound.registerSounds(sounds, assetsPath);  // regier sound, which preloads by default
    // }

  render() {
    return (
      <div className="container-fluid">
        <MstSoundComponent
          audioContext = {this.audioContext}
          instruments = {this.state.instruments}
          bodyParam = {this.bodyParam}
        />
      	<div className="row">
      		<div className={"col-md-12 bg-secondary"}>
            <h1 className={"text-white"}>Osmosi</h1>
          </div>
      	</div>
      	<div className={"row"}>
      		<InstrumentsPanel instruments={this.state.instruments}/>
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
