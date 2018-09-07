import React, { Component } from 'react';
import styles from './app.css';
import ReactImage from './react.png';
import TwitterSearch from './TwitterSearch/TwitterSearch';

export default class App extends Component {
  state = { username: null };

  componentDidMount() {
    fetch('/api/getUsername')
      .then(res => res.json())
      .then(user => this.setState({ username: user.username }));
  }

  render() {
    const { username } = this.state;
    return (
      <div>
        {username ? <h1>{`Hello ${username}`}</h1> : <h1>Loading.. please wait!</h1>}
        <h2>Enter username in the search to read his tweets</h2>
        <TwitterSearch />
      </div>
    );
  }
}
