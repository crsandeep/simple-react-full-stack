import React, { useEffect, useState } from 'react';
import './app.css';
import ReactImage from './react.png';

const App = () => {
  const [userName, setUserName] = useState('');
  const [ip, setIp] = useState('');

  useEffect(() => {
    fetch('/api/getUsername')
      .then(res => res.json())
      .then(user => setUserName(user.username));
  }, [])

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
      .then(data => window.location.href = 'https://__________________:' + data.port);


  return (
    <div>
      {userName
        ? <h1>{`Hello ${userName}`}</h1>
        : <h1>Loading.. please wait!</h1>}

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