const express = require('express');
const bodyParser = require('body-parser');
const os = require('os');
const { exec } = require('node:child_process');

const jsonParser = bodyParser.json();

const app = express();
app.use(express.static('dist'));


app.get('/api/getUsername',
  (req, res) =>
    res.send({ username: os.userInfo().username }));

app.post('/api/connect', jsonParser,
  (req, res) => {
    console.log('got ip', req.body);

    exec('ls ./', (err, output) => {
      // once the command has completed, the callback function is called
      if (err) {
        // log and return if we encounter an error
        console.error("could not execute command: ", err);
        return;
      }
      // log the output received from the command
      console.log("Output: \n", output)
    })

    res.send({ port: 3000 });
  });


app.listen(process.env.PORT || 8080, () =>
  console.log(`Listening on port ${process.env.PORT || 8080}!`));
