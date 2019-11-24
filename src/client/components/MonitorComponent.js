// Renders the bodies

import React, { Component } from 'react';
import ReactDOM from 'react-dom';



class Monitor extends Component {

  constructor(props){
      super(props)
  }

  componentDidUpdate() {
    console.log('Welcome in Monitor Component');
    if(this.props.bodies !=undefined){
    console.log('body: ', + this.props.bodies[0].bodyIndex);
    console.log('all jpoints ', this.props.bodies[0].joints);
    var joit7 = this.props.bodies[0].joints[7];
    console.log('x coord: ', joit7.x);
    this.draw(this.props.bodies[0]);
   }
  }

  draw(body){
    var canvas = document.getElementById('bodyCanvas');
    var ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#ff0000';
    var i=0;
    for (i =0 ; i<21; ++i) {
      var j= body.joints[i];
      ctx.fillRect(j.x,j.y, 10, 10);

    }

  }

  render() {
    return <canvas className={"border"} ref="canvas" id="bodyCanvas" width="512" height="424"></canvas>
    }
}

export default Monitor;
