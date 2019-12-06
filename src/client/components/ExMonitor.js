// Renders the bodies

import React, { Component } from 'react';
import ReactDOM from 'react-dom';
import io from 'socket.io-client';
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


//Setting Socke connetion
var socketio_url = "http://localhost:8080" ;
var socket = io.connect(socketio_url);
var kinectBodies = [];
var demoMode = true;

class ExMonitor extends Component {

  constructor(props){
      console.log("Building ExMonitor");
      super(props);
      socket.on('bodyFrame', this.settingKinectBodies.bind(this));
      this.body = null;
      this.bodyParam = new bodyParam();
      this.demoMode = true;
      this.loadDemo();
  }

  shouldComponentUpdate(){
    return false;
  }

  componentDidUpdate(){
    console.log('Did Update');
  }

  settingKinectBodies(bodyFrame){
    this.demoMode = false
    clearInterval(demo);
    for(var i=0; i<bodyFrame.bodies.length; ++i){
      if (bodyFrame.bodies.traked == true){
        this.body = bodyFrame.bodies[i];
        this.processKinectBodies();
      }
    }
  }

  loadDemo(){
    if(this.demoMode == true){
      var index = -1;
      var demo = setInterval(() => {
        ++index;
        this.body = data[index][0];
        this.processDemoBodies();
      }, 150);
    }
  }

  processKinectBodies(){
    //DRAW THE BODY
    this.bodyParam = Object.assign({},this.props.bodyParam);
    var canvas = document.getElementById('bodyCanvas');
    var cw = canvas.width;
    var ch = canvas.height;
    this.populateKinectBodyParam2(this.body.joints,this.bodyParam,cw,ch);
    this.props.newBodyParam(this.bodyParam); //Send this even before drawing the joints.
    //this.body.cx = '0';
    //this.body.cy = '0';
    //var canvas = document.getElementById('bodyCanvas');
    var ctx = canvas.getContext('2d');
    var cw = canvas.width;
    var ch = canvas.height;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    //ctx.fillStyle = '#ff0000';
    var i=0;
    //var tempx =0;
    //var tempy =0;
    //Draw each joints
    for (i =0 ; i<20; ++i) {
      var joint= this.body.joints[i];
      this.drawSimpleCircle(ctx, joint.colorX*cw, joint.colorY*ch, 5, 'red', true);
      //tempx +=joint.colorX*cw;
      //tempy +=joint.colorY*ch;
    }
    //Draw center body
    //this.bodyParam.cx =tempx/20;
    //this.bodyParam.cy =tempy/20;
    //this.drawSimpleCircle(ctx, this.bodyParam.cx, this.bodyParam.cy, 10, 'blue', true);
    //Draw Wrist circles
    if(true){
     this.drawnWistCircles(ctx, false)
    }
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
    var x2 = this.bodyParam.wrsRx;
    var y2 = this.bodyParam.wrsRy;
    var d = Math.sqrt((x2-x1)*(x2-x1)+(y2-y1)*(y2-y1));
    this.drawSimpleCircle(ctx, x1, y1, d, 'blue', toFill);

    //Left
    var x2 = this.bodyParam.wrsLx;
    var y2 = this.bodyParam.wrsLy;
    var d = Math.sqrt((x2-x1)*(x2-x1)+(y2-y1)*(y2-y1));
    this.drawSimpleCircle(ctx, x1, y1, d, 'blue', toFill);
  }

  populateKinectBodyParam2(joints,bodyParam,cw,ch){
    //Body Cnetre body, calculated. NOT a kinect param
    bodyParam.cx = joints[0].colorX*cw;
    bodyParam.cy = joints[0].colorX*cw;

    // SPINE BASE
    //bodyParam.spnbx = joints[0].colorX*cw;
    //bodyParam.spnby = joints[0].colorY*ch;

    // SPIN MID
    //bodyParam.spnmx = joints[1].colorX*cw;
    //bodyParam.spmmy = joints[1].colorY*ch;

    // NECK
    //bodyParam.nckx = joints[2].colorX*cw;
    //bodyParam.ncky = joints[2].colorY*ch;

    // HEAD
    //bodyParam.hdx = joints[3].colorX*cw;
    //bodyParam.hdy = joints[3].colorY*ch;

    // SHOULDER LEFT
    //bodyParam.shdLx = joints[4].colorX*cw;
    //bodyParam.shdLy = joints[4].colorY*ch;

    // ELBOW LEFT
    //bodyParam.elbLx = joints[5].colorX*cw;
    //bodyParam.elbLy = joints[5].colorY*ch;

    // WRIST LEFT
    bodyParam.wrsLx = joints[6].colorX*cw;
    bodyParam.wrsLy = joints[6].colorY*ch;

    // HAND LEFT
    //bodyParam.hndLx = joints[7].colorX*cw;
    //bodyParam.hndLy = joints[7].colorY*ch;

    // SHOULDER RIGHT
    //bodyParam.shdRx = joints[8].colorX*cw;
    //bodyParam.shdRy = joints[8].colorY*ch;

    // ELBOW RIGHT
    //bodyParam.elbRx = joints[9].colorX*cw;
    //bodyParam.elbRy = joints[9].colorY*ch;

    // WRIST RIGHT
    bodyParam.wrsRx = joints[10].colorX*cw;
    bodyParam.wrsRy = joints[10].colorY*ch;

    // HAND RIGHT
    //bodyParam.hndRx = joints[11].colorX*cw;
    //bodyParam.hndRy = joints[11].colorY*ch;

    // HIP LEFT
    //bodyParam.hpLx = joints[12].colorX*cw;
    //bodyParam.hpLy = joints[12].colorY*ch;

    // KNEE LEFT
    //bodyParam.knLx = joints[13].colorX*cw;
    //bodyParam.knLy = joints[13].colorY*ch;

    // ANKLE LEFT
    bodyParam.ankLx = joints[14].colorX*cw;
    bodyParam.ankLy = joints[14].colorY*ch;

    // FOOT LEFT
    //bodyParam.ftLx = joints[15].colorX*cw;
    //bodyParam.ftLy = joints[15].colorY*ch;

    // HIP RIGHT
    bodyParam.hpRx = joints[16].colorX*cw;
    bodyParam.hpRy = joints[16].colorY*ch;

    // KNEE RIGHT
    //bodyParam.knRx = joints[17].colorX*cw;
    //bodyParam.knRy = joints[17].colorY*ch;

    // ANKLE RIGHT
    bodyParam.ankRx = joints[18].colorX*cw;
    bodyParam.ankRy = joints[18].colorY*ch;

    // FOOT RIGHT
    //bodyParam.ftRx = joints[19].colorX*cw;
    //bodyParam.ftRy = joints[19].colorY*cw;

    ///******Not Available in Demo demoMode
    // spineShoulder 	: 20,
    // handTipLeft 		: 21,
    // thumbLeft 			: 22,
    // handTipRight 		: 23,
    // thumbRight 			: 24

    return bodyParam;

  }

  // populateKinectBodyParam(i,joint,bodyParam){
  //   switch(i) {
  //   // SPINE BASE
  //   case 0:
  //   bodyParam.scx = joint.colorX;
  //   bodyParam.scy = joint.colorY;
  //   break;
  //   // SPIN MID
  //   case 1:
  //   break;
  //   // NECK
  //   case 2:
  //   break;
  //   // HEAD
  //   case 3:
  //   break;
  //   // SHOULDER LEFT
  //   case 4:
  //   break;
  //   // ELBOW LEFT
  //   case 5:
  //   break;
  //   // WRIST LEFT
  //   case 6:
  //   bodyParam.wlx = joint.colorX;
  //   bodyParam.wly = joint.colorY;
  //   break;
  //   // HAND LEFT
  //   case 7:
  //   bodyParam.hlx = joint.colorX;
  //   bodyParam.hly = joint.colorY;
  //   break;
  //   // SHOULDER RIGHT
  //   case 8:
  //   break;
  //   // ELBOW RIGHT
  //   case 9:
  //   break;
  //   // WRIST RIGHT
  //   case 10:
  //   bodyParam.wrx = joint.colorX;
  //   bodyParam.wry = joint.colorY;
  //   break;
  //   // HAND RIGHT
  //   case 11:
  //   bodyParam.hrx = joint.colorX;
  //   bodyParam.hry = joint.colorY;
  //   break;
  //   // HIP LEFT
  //   case 12:
  //   break;
  //   // KNEE LEFT
  //   case 13:
  //   break;
  //   // ANKLE LEFT
  //   case 14:
  //   bodyParam.ankLx = joint.colorX;
  //   bodyParam.ankLy = joint.colorY;
  //   break;
  //   // FOOT LEFT
  //   case 15:
  //   break;
  //   // HIP RIGHT
  //   case 16:
  //   break;
  //   // KNEE RIGHT
  //   case 17:
  //   break;
  //   // ANKLE RIGHT
  //   case 18:
  //   bodyParam.ankRx = joint.colorX;
  //   bodyParam.ankRy = joint.colorY;
  //   break;
  //   // FOOT RIGHT
  //   case 19:
  //   break;
  //
  //   return;
  // }};

  populateBodyParam(i,joint,bodyParam){
    switch(i) {
    // SPINE BASE
    case 0:
    bodyParam.scx = joint.x;
    bodyParam.scy = joint.y;
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
    bodyParam.wly = joint.y;
    break;
    // HAND LEFT
    case 7:
    bodyParam.hlx = joint.x;
    bodyParam.hly = joint.y;
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
    bodyParam.wry = joint.y;
    break;
    // HAND RIGHT
    case 11:
    bodyParam.hrx = joint.x;
    bodyParam.hry = joint.y;
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
    bodyParam.ankLy = joint.y;
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
    bodyParam.ankRy = joint.y;
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
