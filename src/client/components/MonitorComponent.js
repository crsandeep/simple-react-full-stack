// Renders the bodies

import React, { Component } from 'react';
import ReactDOM from 'react-dom';



class Monitor extends Component {

  constructor(props){
      super(props);
  }

  componentDidUpdate() {
    //console.log('Welcome in Monitor Component');
    if(this.props.bodies !=undefined){
    this.body = this.props.bodies[0];
    //console.log('body: ', + this.props.bodies[0].bodyIndex);
    //console.log('all jpoints ', this.props.bodies[0].joints);
    var joit7 = this.props.bodies[0].joints[7];
    //console.log('x coord: ', joit7.x);
    this.draw(this.props.bodies[0]);
   }
  }

  draw(body){
    this.body.cx = '0';
    this.body.cy = '0';
    var canvas = document.getElementById('bodyCanvas');
    var ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#ff0000';
    var i=0;
    for (i =0 ; i<21; ++i) {
      var j= body.joints[i];
      ctx.fillRect(j.x,j.y, 10, 10);
      this.body.cx +=j.x;
      this.body.cy += j.y;
    }
    this.body.handsOpenes = this.setOpeness(body,this.body.cx,this.body.cy, canvas)
  }

  setOpeness(user,userCenterX,userCenterY, canvas) {
    var leftX = user.joints[7].x*canvas.width;
    var leftY = user.joints[7].y*canvas.height;
    var rightX = user.joints[11].x*canvas.width;
    var rightY = user.joints[11].y*canvas.height;
    var leftDistance = Math.sqrt( (userCenterX-leftX)*(userCenterX-leftX) + (userCenterY-leftY)*(userCenterY-leftY));
    var rightDistance = Math.sqrt( (userCenterX-leftX)*(userCenterX-leftX) + (userCenterY-leftY)*(userCenterY-leftY));
    return (leftDistance + rightDistance)/2
  }

  render() {
    return <canvas className={"border"} ref="canvas" id="bodyCanvas" width="512" height="424"></canvas>
    }
}

export default Monitor;
