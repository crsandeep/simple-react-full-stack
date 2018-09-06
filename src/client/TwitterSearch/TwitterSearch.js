import React, { Component } from 'react';

export default class App extends Component {
  state = { user: 'ninja', tweets: [] };

  componentDidMount() {
    fetch('/api/getTweets/ninja')
      .then(res => res.json())
      .then(tweets => this.setState({
        tweets
      }));
  }

  render() {
    const { user, tweets } = this.state;
    return (
      <div>
        <h1>{user}</h1>
        { tweets && tweets.map(tweet => <p>{tweet}</p>) }
      </div>
    );
  }
}
