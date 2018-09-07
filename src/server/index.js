const express = require('express');
const os = require('os');
const { getTweets } = require('./twitter');

const app = express();

app.use(express.static('dist'));
app.get('/api/getUsername', (req, res) => res.send({ username: os.userInfo().username }));
app.get('/api/getTweets/:search', (req, res) => {
  if (req.params && req.params.search) {
    getTweets(req.params.search).then(data => res.send(data.statuses.map(status => status.text)));
  }
});

app.listen(8080, () => console.log('Listening on port 8080!'));
