import React, { Component } from 'react';
import './app.css';
import ReactImage from './react.png';

export default class AppTest extends Component {
  state = { 
    username: null,
    input: ''
  };

  constructor(props) {
    super(props);
    this.updateUser = this.updateUser.bind(this);
    this.handleChange = this.handleChange.bind(this);
  }

  componentDidMount() {
    // fetch('/api/getUsername')
    //   .then(res => res.json())
    //   .then(user => this.setState({ username: user.username }));
  }

  updateUser(){
    this.setState({ username: 'abc' })
  }

  handleChange(e) {
    this.setState({ input: e.target.value })
  }

  render() {
    const { username } = this.state;
    return (
      <div>
        <p>testing</p>
        {username ? <h1>{`Hello ${username}`}</h1> : <h1>Loading.. please wait!</h1>}
        {username ? <input id='txtField' name='txtField' type='text' value={this.state.input} onChange={this.handleChange}/> : null}
        <img src={ReactImage} alt="react" />
        <button onClick={this.updateUser}>Test</button>
        {this.props.showMsg ? <span>message 123</span> : null}
      </div>
    );
  }
}
