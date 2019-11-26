// Contain
// - Volume On/Off
// - Sound On/Off
// - Track On/Off

import React, { Component } from 'react';
import ReactDOM from 'react-dom';



class MstSoundComponent extends Component {
  constructor(props){
      super(props);
      this.instrument = this.props.instrument;
      this.state = {instrument: this.instrument};
      this.audioContext = new AudioContext();
      this.audioContext.resume();
      this.setGuitar();
      this.playGuitar()
  }

  componentDidMount(){
    this.playGuitar();
  }

  playGuitar () {
    var myinstance = createjs.Sound.play("c3");
  }

  setGuitar (){
    //this.instrument = 'guitar'
    var assetsPath = "../src/client/audio/guitar/";
    //scale: ['C','D','E','G','A'],  //majorPentatonic
    var sounds =[
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
    ];
    createjs.Sound.alternateExtensions = ["wav"];	// add other extensions to try loading if the src file extension is not supported
    createjs.Sound.addEventListener("fileload", function(event) {
      //vm.readyToPlayGuitar(event)
    }); // add an event listener for when load is completed
    createjs.Sound.registerSounds(sounds, assetsPath);
    createjs.Sound.play("c3"); // regier sound, which preloads by default
  }

  render(){
    return(
      <div>
      <span><b>Instrument:</b> {this.state.instrument['Type']}  </span>
      <span><b>with volume:</b> {this.state.instrument['Volume']}  </span>
      <span><b>and note:</b> {this.state.instrument['Note']} </span>
      <span><b>in state:</b>{this.state.instrument['Switch'].toString()} </span>
      </div>
    )
  }
}

export default MstSoundComponent;
