const Twitter = require('twitter');
const {
  consumerApiKey, consumerApiSecretKey, consumerAccessToken, consumerAccessTokenSecret
} = require('./config');

const client = new Twitter({
  consumer_key: consumerApiKey,
  consumer_secret: consumerApiSecretKey,
  access_token_key: consumerAccessToken,
  access_token_secret: consumerAccessTokenSecret
});

const getTweets = (user) => {
  const params = { screen_name: user };
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

module.exports = getTweets;
