const express = require('express');
const proxy = require('express-http-proxy');

const app = express();

app.use(express.static('dist'));

app.use('/api/getTickers', proxy('localhost:8020', {
    proxyReqOptDecorator: function(proxyReqOpts, srcReq) {

        return new Promise(function(resolve, reject) {
            proxyReqOpts.headers['Content-Type'] = 'text/html';
            resolve(proxyReqOpts);
        })
    }
}));

app.listen(process.env.PORT || 8080, () => console.log(`Listening on port ${process.env.PORT || 8080}!`));
