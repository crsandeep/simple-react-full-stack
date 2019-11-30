// Contain
// - Volume On/Off
// - Sound On/Off
// - Track On/Off

import React, { Component } from 'react';
import ReactDOM from 'react-dom';

var water_drop = {
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

createjs.Sound.alternateExtensions = ["wav"];	// add other extensions to try loading if the src file extension is not supported
createjs.Sound.addEventListener("fileload", function(event) {

}); // add an event listener for when load is completed

water_drop.sounds = createjs.Sound.registerSounds(water_drop.source, water_drop.assetsPath);
classic_guitar.sounds = createjs.Sound.registerSounds(classic_guitar.source, classic_guitar.assetsPath);


class MstSoundComponent extends Component {
  constructor(props){
      super(props);
      //this.classic_Guitar = new Classic_Guitar();
      //this.water_Drop = new Water_Drop();
      this.state = {instruments:this.props.instruments,};
  }

  //Try to play each Body instrument
  // TO DO: Make an abstract foreach() instead
  componentDidUpdate (){
      this.playCenterBody(this.props.instruments[0]);
      this.playHands(this.props.instruments[1]);
      this.playFeet(this.props.instruments[2]);
    }

  // If Body Instrument is Off or with no volume don't play
  // Else set the channel and then use it
  playCenterBody (instrument){
    if (!instrument.on) return;
    if (instrument.volume == 0) return;
    var channel = this.getInstrument(instrument.type);
    var note = this.generateNote(channel, instrument, this.props.bodyParam);
    this.generateSound(instrument, note);
  }

  playHands (instrument){
    if (!instrument.on) return;
    if (instrument.volume == 0 ) return;
    var channel = this.getInstrument(instrument.type);
    var note = this.generateNote(channel, instrument, this.props.bodyParam);
    this.generateSound(instrument, note);
  }

  playFeet (instrument){
    if (!instrument.on) return;
    if (instrument.volume == 0 ) return;
    var channel = this.getInstrument(instrument.type);
    var note = this.generateNote(channel, instrument, this.props.bodyParam);
    this.generateSound(instrument, note);
  }

  //Provide the instrument type to the Body Instrument
  //MUST DO: Select the type automatically by its defintion
  getInstrument (type){
    switch (type) {
      case this.props.instrumentTypeList.classic_guitar:
        return classic_guitar;
        break;
      case this.props.instrumentTypeList.water_drop:
        return water_drop;
        break;
    }
  }

  generateNote (chn, instrument, bodyParam){
    var note = null;
    if (instrument.mode == this.props.instrumentModeList.random ){
      note = chn.notes[Math.floor(Math.random()*chn.notes.length)];
      return note;
    } else {
      switch (instrument.name){
        case this.props.instrumentChannelName.body:
          note = this.generateBodyNote(chn, instrument, bodyParam);
          return note;
          break;
        case this.props.instrumentChannelName.hands:
          note = this.generateHandsNote(chn, instrument, bodyParam);
          return note;
          break;
        case this.props.instrumentChannelName.feet:
          note = this.generateFeetNote(chn, instrument, bodyParam);
          return note;
          break;
      }
    }
  }

  generateBodyNote (channel, instrument, bodyParam){
      var note = null;
      note = channel.notes[0];
      return note;
  }

  generateHandsNote (channel, instrument, bodyParam){
      var note = null;
      note = channel.notes[0];
      return note;
  }

  generateFeetNote (channel, instrument, bodyParaml){
      var note = null;
      note = channel.notes[0];
      return note;
  }

  generateSound (instrument, note){
    var myinstance = createjs.Sound.play(note);
    myinstance.volume = instrument.volume;
  }

  render() {
    return(
      <div>
      </div>
    )
  }
}

export default MstSoundComponent;
