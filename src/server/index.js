const express = require('express');
const cors = require('cors');
const os = require('os');

const app = express();
app.use(cors());

var server = require('http').createServer(app);
    io = require('socket.io').listen(server);
    Kinect2 = require('kinect2');
    kinect = new Kinect2();

io.origins((origin, callback) => {
  if (origin !== 'localhost:3000') {
      return callback('origin not allowed', false);
  }
  callback(null, true);
});

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

io.on('connection', function (socket){
  console.log('socket.io connection estlabished');
  socket.broadcast.emit('message', {topic: 'new_connection', message: 'user'});
})

if(kinect.open()){
  kinect.on('bodyFrame', sendFrame);

  function sendFrame(bodyFrame){
      console.log('Kinect is Lve!!')
      io.emit('bodyFrame', bodyFrame);
  }

  kinect.openBodyReader();
}




app.use(express.static('dist'));
app.get('/api/getUsername', (req, res) => res.send({ username: os.userInfo().username }));

app.listen(process.env.PORT || 8080, () => console.log(`Lstening ons port ${process.env.PORT || 8080}!`));
