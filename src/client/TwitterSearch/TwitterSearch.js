import React, { Component } from 'react';
import styles from './TwitterSearch.css';

export default class App extends Component {
  state = { user: 'ninja', tweets: [] };

  getTweets(e) {
    e.preventDefault();
    fetch(`/api/getTweets/${e.target.q.value}`)
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
        <form onSubmit={this.getTweets.bind(this)}>
          <div>
            <label htmlFor="mySearch">Search for user</label>
            <input
              type="search"
              id="mySearch"
              name="q"
              placeholder="User IDs are 4–8 characters in length"
              required
              size="30"
              minLength="4"
              maxLength="8"
            />
            <button>Search</button>
            <span className={styles.valid} />
          </div>
        </form>
        { tweets && tweets.map(tweet => <p>{tweet}</p>) }
      </div>
    );
  }
}
