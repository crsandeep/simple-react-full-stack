import React, { Component } from 'react';
import './app.css';
import io from 'socket.io-client';
import InstrumentsPanel from './components/InstrumentsPanel.js';
import InstrumentsSettingPanel from './components/InstrumentsSettingPanel.js';
import MstSoundComponent from './components/MasterSoundComponent.js';
import ExMonitor from './components/ExMonitor.js';
import data from './lmac1.json';

var index = 0;


var water_drop = {
  name:'Water Drop',
  instance: null,
  source: [
      {src:"01-C0.wav", id:"c0"},
      {src:"02-Db0.wav", id:"db0"},
      {src:"03-D0.wav", id:"d0"},
      {src:"04-Eb0.wav", id:"eb0"},
      {src:"05-E0.wav", id:"e0"},
      {src:"06-F0.wav", id:"f0"},
      {src:"07-Gb0.wav", id:"gb0"},
      {src:"08-G0.wav", id:"g0"},
      {src:"09-Ab0.wav", id:"ab0"},
      {src:"10-A0.wav", id:"a0"},
      {src:"11-Bb0.wav", id:"bb0"},
      {src:"12-B0.wav", id:"b0"},
      {src:"13-C1.wav", id:"c1"},
      {src:"14-Cb1.wav", id:"cb1"},
      {src:"15-D1.wav", id:"d1"},
      {src:"16-Eb1.wav", id:"eb1"},
      {src:"17-E1.wav", id:"e1"},
      {src:"18-F1.wav", id:"f1"},
      {src:"19-Gb1.wav", id:"gb1"},
      {src:"20-G1.wav", id:"g1"},
      {src:"21-Ab1.wav", id:"ab1"},
      {src:"22-A1.wav", id:"a1"},
    ],
  notes: ["c0","db0","d0","eb0","e0","f0","gb0","g0","ab0","a0","bb0","b0","c1","cb1","d1","eb1","e1","f1","gb1","g1","ab1","a1"],
  assetsPath: "src/client/audio/water_drop/"
}

var classic_guitar = {
  name:'Classic Guitar',
  instance: null,
  source: [
      {src:"c3_mf_rr3.wav", id:"c3"},
      {src:"c3_mf_rr3.wav", id:"d3"},
      {src:"eb3_mf_rr3.wav", id:"e3"},
      {src:"gb3_mf_rr3.wav", id:"g3"},
      {src:"a3_mf_rr3.wav", id:"a3"},
      {src:"c4_mf_rr3.wav", id:"c4"},
      {src:"c4_mf_rr3.wav", id:"d4"},
      {src:"eb4_mf_rr3.wav", id:"e4"},
      {src:"gb4_mf_rr3.wav", id:"g4"},
      {src:"a4_mf_rr3.wav", id:"a4"},
      {src:"c5_mf_rr3.wav", id:"c5"},
      {src:"eb5_mf_rr3.wav", id:"d5"},
      {src:"eb5_mf_rr3.wav", id:"e5"},
      {src:"gb5_mf_rr3.wav", id:"g5"},
      {src:"a5_mf_rr3.wav", id:"a5"},
    ],
  notes: ["c3","d3","e3","g3","a3","c4","d4","e4","g4","a4","c5","d5","e5","g5","a5"],
  assetsPath: "src/client/audio/guitar/"
};

var setting1 = [
  {"name":"Body","on":true,"type":"Classic Guitar","lastPlayedNote":["a5"],"volume":0.2,"mode":"Scale"},
  {"name":"Hands","on":true,"type":"Water Drop","lastPlayedNote":["db0","db0"],"volume":0.2,"mode":"Scale"},
  {"name":"Feet","on":true,"type":"Classic Guitar","lastPlayedNote":["g3"],"volume":0.2,"mode":"Scale"}
];

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

    //this.demoMode = true;

    this.audioContext = new AudioContext();
    this.bodyParam = null;
    this.state = {instruments:[body,hands,feet],};
  }

  //Create a JSON file to capture the instrument settings and store somewhere
  // onSaveSettingsHandler(){
  //   console.log('Should save this settings: ', JSON.stringify(this.state.instruments))
  // }

  // onLoadSettingsHandler(){
  //   this.setState({instruments:setting1});
  // }

  newBodyParameterHandle(bodyParameter){
    //this.setState({bodyParam: bodyParameter});
    this.bodyParam= bodyParameter;
    this.loadInstruments(this.state.instruments)
  }

  renderMonitor(){
    console.log("Rendering");
    return(
      <ExMonitor
        newBodyParam={(value)=>this.newBodyParameterHandle(value)}
      />
    )
  }

  loadInstruments (instruments){
      var i = 0;
      for (i=0; i<instruments.length; ++i) {
        this.prepInstrument(instruments[i]);
      }
    }

  // If Body Instrument is Off or with no volume don't play
  // Else set the channel and then use it
  prepInstrument (instrument){
    if (!instrument.on) return;
    if (instrument.volume == 0) return;
    var sounds = this.getSounds(instrument.type);
    var note = this.getNote(sounds, instrument, this.bodyParam);
    this.playInstrument(instrument, note);
  }

  //Provide the sounds sample based on the type defined by the Body Instrument
  // the sample are variable defined above. Should be a better way.....
  //MUST DO: Select the type automatically by its defintion
  getSounds (type){
    switch (type) {
      case instrumentTypeList.classic_guitar:
      return classic_guitar;
      break;
      case instrumentTypeList.water_drop:
      return water_drop;
      break;
    }
  }

  //Generates random notes or redirect to the right instrument sounds generator
  getNote (sounds, instrument, bodyParam){
    var note = [];
    if (instrument.mode == instrumentModeList.random ){
      note.push(sounds.notes[Math.floor(Math.random()*sounds.notes.length)]);
      return note;
    } else {
      switch (instrument.name){
        case instrumentChannelName.body:
        note = this.generateCenterBodyNote(sounds, instrument, bodyParam);
        return note;
        break;
        case instrumentChannelName.hands:
        //As soon as you have the array of notes generate also the one for the hands
        note = this.generateWristeNote(sounds, instrument, bodyParam);
        return note;
        break;
        case instrumentChannelName.feet:
        note = this.generateFeetNote(sounds, instrument, bodyParam);
        return note;
        break;
      }
    }
  }

  generateFeetNote (sounds, instrument, bp) {
    var note = [];
    var arx = bp.ankRx;
    var ary = bp.ankRy;
    var alx = bp.ankLx;
    var aly = bp.ankLy;
    var d = Math.sqrt((arx-alx)*(arx-alx)+(ary-aly)*(ary-aly));
    var norm_d = Math.round(d/sounds.notes.length);
    //console.log('Distance from Center of Right Hands:' , d);
    //console.log('Distance from Center of Right Hands:' , Math.round(d/10));
    if(norm_d<sounds.notes.length){
      note.push(sounds.notes[norm_d]);
      } else {
        note.push((sounds.notes[(sounds.notes.length)-1]));
    }
    return note;
  }

  generateWristeNote(sounds, instrument, bp){
    //Right Wrist
    var note = [];
    var norm_d = Math.round(this.bodyParam.RWrist_Center_D/sounds.notes.length);
    //console.log('Distance from Center of Right Hands:' , d);
    //console.log('Distance from Center of Right Hands:' , Math.round(d/10));
    if(norm_d<sounds.notes.length){
      note.push(sounds.notes[norm_d]);
    } else {
      note.push((sounds.notes[(sounds.notes.length)-1]));
    }

    //Left Wrist
    // var x1 = bp.cx;
    // var x2 = bp.wlx;
    // var y1 = bp.cy;
    // var y2 = bp.wly;
    // var d = Math.sqrt((x2-x1)*(x2-x1)+(y2-y1)*(y2-y1))
    var norm_d = Math.round(this.bodyParam.LWrist_Center_D/sounds.notes.length);
    //console.log('Distance from Center of Right Hands:' , d);
    //console.log('Distance from Center of Right Hands:' , Math.round(d/10));
    if(norm_d<sounds.notes.length){
      note.push(sounds.notes[norm_d]);
    } else {
      note.push((sounds.notes.length)-1);
    }
    //console.log('Playing Note:' , note);
    return note;
  }

  generateCenterBodyNote (sounds, instrument, bodyParam){
    var bp = bodyParam;
    var note = [];
    var cx = bp.cx;
    var norm_cx = Math.round(cx/sounds.notes.length);
    //console.log('Distance from Center of Right Hands:' , d);
    //console.log('Distance from Center of Right Hands:' , Math.round(d/10));
    if(norm_cx<sounds.notes.length){
      note.push(sounds.notes[norm_cx]);
      } else {
        note.push((sounds.notes[(sounds.notes.length)-1]));
    }
    return note;
  }

  //All instruemts at the end plays here!!
  playInstrument (instrument, note){
    //console.log('Playing: ' + note.length + ' notes');
    if (JSON.stringify(note) !=JSON.stringify(instrument.lastPlayedNote)) {
      note.forEach( function (n,index){
        //console.log('Playing Note:' , n);
        var myinstance = createjs.Sound.play(n);
        myinstance.volume = instrument.volume;
      })
      instrument.lastPlayedNote = note;
    } else {
      return;
    }
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
          <div className={"col-md-6 mt-2"}>
      		<InstrumentsPanel instruments={this.state.instruments} instrumentTypeList={instrumentTypeList}/>
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
