const express = require('express');
const cors = require('cors');
const os = require('os');
const Kinect2 = require('kinect2');

var app = require('express')();
var http = require('http').createServer(app);

var io = require('socket.io')(http);

app.get('/', function(req, res){
  res.sendFile(__dirname + '/index.html');
});

io.on('connection', function(socket){
  console.log('a user connected');
});

http.listen(8080, function(){
  console.log('listening on *:8080');
});

//Setting Kinect
kinect = new Kinect2();

if(kinect.open()){
  kinect.on('bodyFrame', sendFrame);

  function sendFrame(bodyFrame){
      console.log('Kinect is Lve!!')
      io.emit('bodyFrame', bodyFrame);
  }

  kinect.openBodyReader();
}




app.use(express.static('dist'));

app.use( (req, res, next) => {
   res.header("Access-Control-Allow-Origin", "http://localhost:3000"); //The ionic server
   res.header("Access-Control-Allow-Credentials", "true");
   res.header("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept");
   next();
});

//app.listen(process.env.PORT || 8080, () => console.log(`Lstening ons port ${process.env.PORT || 8080}!`));

// io.on('connection', function (socket){
//   console.log('socket.io connection estlabished');
//   socket.broadcast.emit('message', {topic: 'new_connection', message: 'user'});
// })
