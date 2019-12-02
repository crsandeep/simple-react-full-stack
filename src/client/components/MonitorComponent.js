// Renders the bodies

import React, { Component } from 'react';
import ReactDOM from 'react-dom';


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
// FOOT RIGHT


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
}

class Monitor extends Component {

  constructor(props){
      super(props);
      this.body = null;
  }

  componentDidUpdate() {
    //console.log('Welcome in Monitor Component');
    if(this.props.demoMode && this.props.bodies !=undefined){
        this.body = this.props.bodies[0];
        this.processDemoBodies(this.props.bodies[0]);
        return;
      }
    if(!this.props.demoMode && this.props.bodies !=undefined){
        this.props.bodies.forEach(function(body,index){
          if(body.tracked){
            this.body=body;
            this.processKinectBodies(this.body);
        }}
      )}
    }

  processKinectBodies(body){
    consle.log('Lets write some cool code');
    //Take most of code from below function agnostic and move outside to serve both knect and demoMode
  }

  processDemoBodies(body){

    //DRAW THE BODY
    var bodyParam = Object.assign({},this.props.bodyParam);
    this.body.cx = '0';
    this.body.cy = '0';
    var canvas = document.getElementById('bodyCanvas');
    var ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#ff0000';
    var i=0;
    var tempx =0;
    var tempy =0;
    for (i =0 ; i<20; ++i) {
      var joint= body.joints[i];
      ctx.beginPath();
      ctx.arc(joint.x,joint.y, 5, 0, 2 * Math.PI);
      ctx.stroke();
      ctx.fillStyle = 'red';
      ctx.fill();
      // ctx.fillRect(joint.x,joint.y, 10, 10);
      tempx +=joint.x;
      tempy +=joint.y;
      this.populateBodyParam(i,joint, bodyParam);
    }
    //bodyParam.handsOpenes = this.setOpeness(body,bodyParam.cx,this.body.cy, canvas)
    //FILL CENTER BODY

    bodyParam.cx =tempx/20;
    bodyParam.cy =tempy/20;
    ctx.fillStyle = '#5CACEE';
    ctx.beginPath();
    ctx.arc(bodyParam.cx, bodyParam.cy, 10, 0, 2 * Math.PI);
    ctx.stroke();
    ctx.fillStyle = 'blue';
    ctx.fill();
    //ctx.fillRect(bodyParam.cx/20,bodyParam.cy/20, 20, 20);

    // To be turn on and off with future swithces
    if(true){
      var x1 = bodyParam.cx;
      var x2 = bodyParam.wrx;
      var y1 = bodyParam.cy;
      var y2 = bodyParam.wry;
      var d = Math.sqrt((x2-x1)*(x2-x1)+(y2-y1)*(y2-y1))
      ctx.beginPath();
      ctx.arc(bodyParam.cx,bodyParam.cy, d, 0, 2 * Math.PI);
      ctx.stroke();

      var x1 = bodyParam.cx;
      var x2 = bodyParam.wlx;
      var y1 = bodyParam.cy;
      var y2 = bodyParam.wly;
      var d = Math.sqrt((x2-x1)*(x2-x1)+(y2-y1)*(y2-y1))
      ctx.beginPath();
      ctx.arc(bodyParam.cx,bodyParam.cy, d, 0, 2 * Math.PI);
      ctx.stroke();
    }

    this.props.newBodyParam(bodyParam);
  }

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
