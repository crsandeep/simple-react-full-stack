const express = require('express');
const bodyParser = require('body-parser');
const { exec } = require('node:child_process');


const PEM_FILE_PATH = '';
const SSH_USER = '';

const pemFile = ''; // todo: obtain dynamically

const jsonParser = bodyParser.json();

const app = express();
app.use(express.static('dist'));


app.post('/api/connect', jsonParser,
  (req, res) => {
    console.log('got ip', req.body.ip);

    exec(`docker run -d --rm --name wetty3000 -p 3000:3000 wettyoss/wetty `
      + `-c “ssh -i “${pemFile}” ${SSH_USER}@${req.body.ip} ” `
      + `&& docker cp ${PEM_FILE_PATH}${pemFile} wetty3000:/usr/src/app`,
      (err, output) => {

      if (err) {
        // log and return if we encounter an error
        console.error("could not execute command: ", err);
        return;
      }

      console.log("Output: \n", output)
    })

    res.send({ port: 3000 }); // todo: calc dynamically
  });


app.listen(process.env.PORT || 8080, () =>
  console.log(`Listening on port ${process.env.PORT || 8080}!`));
