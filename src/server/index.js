const express = require('express');
const os = require('os');
// const http = require('http');
const proxy = require('express-http-proxy');

const app = express();

const tickers = {
    aapl: 115.60,
    sbux: 88.40,
    tsla: 453.81,
    pypl: 203.59,
    ba: 167.42
}

app.use(express.static('dist'));

app.use('/api/getTickers', proxy('localhost:8020', {
    proxyReqOptDecorator: function(proxyReqOpts, srcReq) {

    return new Promise(function(resolve, reject) {
        proxyReqOpts.headers['Content-Type'] = 'text/html';
            resolve(proxyReqOpts);
        })
    }
}))

app.listen(process.env.PORT || 8080, () => console.log(`Listening on port ${process.env.PORT || 8080}!`));
