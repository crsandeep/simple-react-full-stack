import React, { Component } from 'react';
import './app.css';
import io from 'socket.io-client';
import InstrumentsPanel from './components/InstrumentsPanel.js';
import InstrumentsSettingPanel from './components/InstrumentsSettingPanel.js';
import MstSoundComponent from './components/MasterSoundComponent.js';
import Monitor from './components/MonitorComponent.js';
import data from './lmac1.json';

var index = 0;

//Setting Socke connetion
var socketio_url = "http://localhost:8080" ;
var socket = io.connect(socketio_url);
var kinectBodies = [];
var demoMode = true;



//TO DO: Add message handler for when Kinect stops working or socket.io disconnects


var setting1 = [
  {"name":"Body","on":true,"type":"Classic Guitar","lastPlayedNote":["a5"],"volume":0.2,"mode":"Scale"},
  {"name":"Hands","on":true,"type":"Water Drop","lastPlayedNote":["db0","db0"],"volume":0.2,"mode":"Scale"},
  {"name":"Feet","on":true,"type":"Classic Guitar","lastPlayedNote":["g3"],"volume":0.2,"mode":"Scale"}
]

const instrumentName =['Body', 'Hands', 'Feet', 'Spine']; // Define the name of the instruments  based on their link to the body's parts
const instrumentTypeList = {classic_guitar:'Classic Guitar', water_drop:'Water Drop'};
const instrumentModeList = {random:'Random', scale:'Scale'};
const instrumentChannelName ={body:'Body', hands:'Hands', feet: 'Feet'};

function bodyParam () {
this.BodyIndex= '';
this.cx= 0;
this.cy= 0;
this.wrx=0;   //Wrist right
this.wry=0;   //Wrist left
this.wlx=0;   //Wrist right
this.wlx=0;   //Wrist right
this.wl=0;
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
this.ankLx=0; //left ankle x
this.ankLy=0; //left ankle y
this.ankRx=0; //right ankle x
this.ankRy=0; //right ankle y
}

function Channel (name) {
  this.name = name;
  this.on = true;
  this.type = instrumentTypeList.classic_guitar;
  this.lastPlayedNote= [];
  this.volume = 0.2;
  this.mode = instrumentModeList.scale;
};

var body = new Channel(instrumentChannelName.body);
var hands = new Channel(instrumentChannelName.hands);
var feet = new Channel(instrumentChannelName.feet);

class App extends Component {
    constructor(props) {
    super(props);

    this.demoMode = true;

    socket.on('connect', this.manageSocketConnection);
    socket.on('bodyFrame', this.settingKinectBodies.bind(this));

    this.audioContext = new AudioContext();
    //this.setGuitar();
    this.bodyParam = new bodyParam();
    this.state = {bodies:[],kinectBodies:[],index:1, instruments:[body,hands,feet], bodyParam:this.bodyParam};
  }

  manageSocketConnection(){
    console.log('Socket.io Client connected');
  }

  settingKinectBodies(bodyFrame){
    var bodies = bodyFrame.bodies;
    this.setState({kinectBodies:bodies});
    this.demoMode = false;
    this.state.index =0;
  }

  componentDidMount() {
    if(this.demoMode == true){
      setInterval(() => {
        var newIndex = this.state.index + 1;
        var body = data[newIndex];
        this.setState({bodies:data[newIndex], index: newIndex})
      }, 150);
    } else {
    }
  }

  //Create a JSON file to capture the instrument settings and store somewhere
  onSaveSettingsHandler(){
    console.log('Should save this settings: ', JSON.stringify(this.state.instruments))
  }

  onLoadSettingsHandler(){
    this.setState({instruments:setting1});
  }

  newBodyParamHandler(bodyParam){
    this.bodyParam= bodyParam;
  }

  renderMonitor(){
    var bds = [];
    if(this.demoMode){
      bds= this.state.bodies;
    } else{
      bds = this.state.kinectBodies;
    }
    return(
      <Monitor
        newBodyParameter={(value)=>newBodyParameterHandle(value)}
        demoMode = {this.demoMode}
        bodies={bds}
        instruments ={this.state.instruments}
        newBodyParam = {(value)=> this.newBodyParamHandler(value)}
      />
    )
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
          <div className={"col-md-4 mt-2"}>
      		<InstrumentsPanel instruments={this.state.instruments} instrumentTypeList={instrumentTypeList}/>
          </div>
          <div className={"col-md-2 mt-2"}>
            <InstrumentsSettingPanel
              onSaveSettings={()=>this.onSaveSettingsHandler()}
              onLoadSettings={()=>this.onLoadSettingsHandler()}/>
          </div>
      		<div className={"col-md-6 mt-5"}>
            {this.renderMonitor()}
          </div>
        </div>
      </div>
    );
  }
}

export default App;
