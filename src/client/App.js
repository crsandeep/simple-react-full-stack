import React, { useState } from 'react';
import './app.css';
import ReactImage from './react.png';

const App = () => {
  const [ip, setIp] = useState('');

  const onIpChange = (event) =>
    setIp(event.target.value);

  const connect = () =>
    fetch('/api/connect', {
      method: 'post',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ ip })
    })
      .then(res => res.json())
      .then(data => window.location.href = `http://localhost:${data.port}/wetty`);


  return (
    <div>
      <h1>Easy SSH: Open a web-based terminal in just one click!</h1>


      <div>
        <input
          type='text'
          placeholder='Enter server IP address'
          onChange={onIpChange}
          autoFocus
          value={ip}
        />
        &nbsp;&nbsp;&nbsp;&nbsp;
        <button
          onClick={connect}
        >
          Connect
        </button>
      </div>

      <p/>

      <img src={ReactImage} alt="react" />
    </div>
  );
}

export default App;