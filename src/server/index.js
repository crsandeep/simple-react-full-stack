const express = require('express');
const os = require('os');
const { getTweets, getTimeLine } = require('./twitter');

const app = express();

app.use(express.static('dist'));

app.get('/api/getUsername', (req, res) => res.send({ username: os.userInfo().username }));

app.get('/api/getTweets/:search', (req, res) => {
  if (req.params && req.params.search) {
    getTweets(req.params.search).then(data => res.send(data.statuses.map(status => status.text)));
  }
});

app.get('/api/getTimeLine/:user', (req, res) => {
  if (req.params && req.params.user) {
    getTimeLine(req.params.user).then(data => res.send(data.map(status => status.text)));
  }
});

app.listen(8080, () => console.log('Listening on port 8080!'));
