const Twitter = require('twitter');
const {
  consumerApiKey, consumerApiSecretKey, consumerAccessToken, consumerAccessTokenSecret
} = require('./config');

const client = new Twitter({
  consumer_key: consumerApiKey,
  consumer_secret: consumerApiSecretKey,
  access_token_key: consumerAccessToken,
  access_token_secret: consumerAccessTokenSecret,
  base: 'rest',
});


const getTimeLine = (user) => {
  const params = { screen_name: user };
  client.options.base = 'stream';
  return new Promise((resolve, reject) => {
    client.get('statuses/user_timeline', params, (error, tweets, response) => {
      if (!error) {
        resolve(tweets);
      } else {
        reject(error);
      }
    });
  });
};

const getTweets = (search) => {
  const params = { q: search };
  return new Promise((resolve, reject) => {
    client.get('search/tweets', params, (error, tweets, response) => {
      if (!error) {
        resolve(tweets);
      } else {
        reject(error);
      }
    });
  });
};

module.exports = { getTweets, getTimeLine };
