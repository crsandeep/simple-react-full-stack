const express = require('express');
const cors = require('cors');
const os = require('os');

// const app = express();
// app.use(cors());

//
// var server = require('http').Server(app);
//
//
// var io = require('socket.io')(server);
// server.listen(8080);


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


// WARNING: app.listen(80) will NOT work here!

// app.get('/', function (req, res) {
//   res.sendFile(__dirname + '/index.html');
// });

// io.on('connection', function (socket) {
//     console.log(data);
// });


//
// var server = require('http').createServer(app);



    //Kinect2 = require('kinect2');
    //kinect = new Kinect2();

// io.origins((origin, callback) => {
//   if (origin !== 'localhost:3000') {
//       return callback('origin not allowed', false);
//   }
//   callback(null, true);
// });

// var server = require('http').createServer(app);
//     io = require('socket.io')(server, {
//     handlePreflightRequest: (req, res) => {
//             const headers = {
//                 "Access-Control-Allow-Headers": "Content-Type, Authorization",
//                 "Access-Control-Allow-Origin": req.headers.origin, //or the specific origin you want to give access to,
//                 "Access-Control-Allow-Credentials": true
//             };
//             res.writeHead(200, headers);
//             res.end();
//         }
//     });

//io.set('origins', '*:*');
//io.set('origins', 'localhost:3000');

//Allow Cross Domain Requests
//io.set('transports', ['websocket']);



// if(kinect.open()){
//   kinect.on('bodyFrame', sendFrame);
//
//   function sendFrame(bodyFrame){
//       console.log('Kinect is Lve!!')
//       io.emit('bodyFrame', bodyFrame);
//   }
//
//   kinect.openBodyReader();
// }




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
