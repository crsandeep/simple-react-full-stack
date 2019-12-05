// Renders the bodies

import React, { Component } from 'react';
import ReactDOM from 'react-dom';
import data from '../lmac1.json';

//https://github.com/js6450/kinect-data
// SPINE BASE
// SPIN MID
// NECK
// HEAD
// SHOULDER LEFT
// ELBOW LEFT
// WRIST LEFT
// HAND LEFT
// SHOULDER RIGHT
// ELBOW RIGHT
// WRIST RIGHT
// HAND RIGHT
// HIP LEFT
// KNEE LEFT
// ANKLE LEFT
// FOOT LEFT
// HIP RIGHT
// KNEE RIGHT
// ANKLE RIGHT
// FOOT RIGHT#

///******Not Available in Demo demoMode
// spineShoulder 	: 20,
// handTipLeft 		: 21,
// thumbLeft 			: 22,
// handTipRight 		: 23,
// thumbRight 			: 24


//MUST DO:
// I have two of this. One in app. Remove this
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
//Other to implement not available in Demo mode
}

class ExMonitor extends Component {

  constructor(props){
      console.log("Building ExMonitor");
      super(props);
      this.body = null;
      this.bodyParam = null;
      this.KIsTraking = false;
      this.demoMode = true;
      this.loadDemo();
  }

  loadDemo(){
    if(this.demoMode == true){
      var index = -1;
      setInterval(() => {
        ++index;
        this.body = data[index][0];
        this.processDemoBodies();
      }, 150);
    }
  }

  processKinectBodies(body){
    //DRAW THE BODY
    this.bodyParam = Object.assign({},this.props.bodyParam);
    this.body.cx = '0';
    this.body.cy = '0';
    var canvas = document.getElementById('bodyCanvas');
    var ctx = canvas.getContext('2d');
    var cw = canvas.width;
    var ch = canvas.height;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    //ctx.fillStyle = '#ff0000';
    var i=0;
    var tempx =0;
    var tempy =0;
    //Draw each joints
    for (i =0 ; i<20; ++i) {
      var joint= body.joints[i];
      this.drawSimpleCircle(ctx, joint.colorX*cw, joint.colorY*ch, 5, 'red', true);
      tempx +=joint.colorX*cw;
      tempy +=joint.colorY*ch;
      this.populateBodyParam(i,joint, this.bodyParam);
    }
    //Draw center body
    this.bodyParam.cx =tempx/20;
    this.bodyParam.cy =tempy/20;
    this.drawSimpleCircle(ctx, this.bodyParam.cx, this.bodyParam.cy, 10, 'blue', true);
    //Draw Wrist circles
    if(true){
     this.drawnWistCircles(ctx, false)
    }

    this.props.newBodyParam(this.bodyParam);
  }

  processDemoBodies(){
    //DRAW THE BODY
    this.bodyParam = Object.assign({},this.props.bodyParam);
    this.body.cx = '0';
    this.body.cy = '0';
    var canvas = document.getElementById('bodyCanvas');
    var ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    //ctx.fillStyle = '#ff0000';
    var i=0;
    var tempx =0;
    var tempy =0;
    //Draw each joints
    for (i =0 ; i<20; ++i) {
      var joint= this.body.joints[i];
      this.drawSimpleCircle(ctx, joint.x, joint.y, 5, 'red', true);
      tempx +=joint.x;
      tempy +=joint.y;
      this.populateBodyParam(i,joint, this.bodyParam);
    }
    //Draw center body
    this.bodyParam.cx =tempx/20;
    this.bodyParam.cy =tempy/20;
    this.drawSimpleCircle(ctx, this.bodyParam.cx, this.bodyParam.cy, 10, 'blue', true);
    //Draw Wrist circles
    if(true){
     this.drawnWistCircles(ctx, false)
    }

    this.props.newBodyParam(this.bodyParam);
  }

  drawSimpleCircle(ctx, cx, cy, d, color, toFill){
    ctx.fillStyle = color;
    ctx.strokeStyle = color;
    ctx.beginPath();
    ctx.arc(cx, cy, d, 0, 2 * Math.PI);
    ctx.stroke();
    if (toFill) {
      ctx.fill();
    }
  }

  drawnWistCircles(ctx, toFill){
    var x1 = this.bodyParam.cx;
    var y1 = this.bodyParam.cy;
    //Right
    var x2 = this.bodyParam.wrx;
    var y2 = this.bodyParam.wry;
    var d = Math.sqrt((x2-x1)*(x2-x1)+(y2-y1)*(y2-y1));
    this.drawSimpleCircle(ctx, x1, y1, d, 'blue', toFill);

    //Left
    var x2 = this.bodyParam.wlx;
    var y2 = this.bodyParam.wly;
    var d = Math.sqrt((x2-x1)*(x2-x1)+(y2-y1)*(y2-y1));
    this.drawSimpleCircle(ctx, x1, y1, d, 'blue', toFill);
  }

  populateKinectBodyParam(i,joint,bodyParam){
    switch(i) {
    // SPINE BASE
    case 0:
    bodyParam.scx = joint.colorX;
    bodyParam.scy = joint.colorY;
    break;
    // SPIN MID
    case 1:
    break;
    // NECK
    case 2:
    break;
    // HEAD
    case 3:
    break;
    // SHOULDER LEFT
    case 4:
    break;
    // ELBOW LEFT
    case 5:
    break;
    // WRIST LEFT
    case 6:
    bodyParam.wlx = joint.colorX;
    bodyParam.wly = joint.colorY;
    break;
    // HAND LEFT
    case 7:
    bodyParam.hlx = joint.colorX;
    bodyParam.hly = joint.colorY;
    break;
    // SHOULDER RIGHT
    case 8:
    break;
    // ELBOW RIGHT
    case 9:
    break;
    // WRIST RIGHT
    case 10:
    bodyParam.wrx = joint.colorX;
    bodyParam.wry = joint.colorY;
    break;
    // HAND RIGHT
    case 11:
    bodyParam.hrx = joint.colorX;
    bodyParam.hry = joint.colorY;
    break;
    // HIP LEFT
    case 12:
    break;
    // KNEE LEFT
    case 13:
    break;
    // ANKLE LEFT
    case 14:
    bodyParam.ankLx = joint.colorX;
    bodyParam.ankLy = joint.colorY;
    break;
    // FOOT LEFT
    case 15:
    break;
    // HIP RIGHT
    case 16:
    break;
    // KNEE RIGHT
    case 17:
    break;
    // ANKLE RIGHT
    case 18:
    bodyParam.ankRx = joint.colorX;
    bodyParam.ankRy = joint.colorY;
    break;
    // FOOT RIGHT
    case 19:
    break;

    return;
  }}

  populateBodyParam(i,joint,bodyParam){
    switch(i) {
    // SPINE BASE
    case 0:
    bodyParam.scx = joint.x;
    bodyParam.scy = joint.y
    break;
    // SPIN MID
    case 1:
    break;
    // NECK
    case 2:
    break;
    // HEAD
    case 3:
    break;
    // SHOULDER LEFT
    case 4:
    break;
    // ELBOW LEFT
    case 5:
    break;
    // WRIST LEFT
    case 6:
    bodyParam.wlx = joint.x;
    bodyParam.wly = joint.y
    break;
    // HAND LEFT
    case 7:
    bodyParam.hlx = joint.x;
    bodyParam.hly = joint.y
    break;
    // SHOULDER RIGHT
    case 8:
    break;
    // ELBOW RIGHT
    case 9:
    break;
    // WRIST RIGHT
    case 10:
    bodyParam.wrx = joint.x;
    bodyParam.wry = joint.y
    break;
    // HAND RIGHT
    case 11:
    bodyParam.hrx = joint.x;
    bodyParam.hry = joint.y
    break;
    // HIP LEFT
    case 12:
    break;
    // KNEE LEFT
    case 13:
    break;
    // ANKLE LEFT
    case 14:
    bodyParam.ankLx = joint.x;
    bodyParam.ankLy = joint.y
    break;
    // FOOT LEFT
    case 15:
    break;
    // HIP RIGHT
    case 16:
    break;
    // KNEE RIGHT
    case 17:
    break;
    // ANKLE RIGHT
    case 18:
    bodyParam.ankRx = joint.x;
    bodyParam.ankRy = joint.y
    break;
    // FOOT RIGHT
    case 19:
    break;

    return;
  }}

  render() {
    return (
      <div>
        <canvas className={"border"} ref="canvas" id="bodyCanvas" width="512" height="424"></canvas>
      </div>
    );
  }
}

export default ExMonitor;
