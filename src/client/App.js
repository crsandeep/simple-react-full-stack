import React, { Component, useEffect } from 'react';
import './app.css';
import ReactImage from './react.png';

export default class App extends Component {
  state = { tickers: [] };

    componentDidMount() {
        fetch('/api/getTickers')
            .then(res => res.json())
            .then(data => {
                const tickerData = [];
                for (let company in data.tickers) {
                    let obj = {};
                    obj['name'] = company;
                    obj['value'] = data.tickers[company];
                    tickerData.push(obj);
                }

                this.setState({ tickers: tickerData });
            });
    }

    componentDidUpdate() {
        setTimeout(() => {
            fetch('/api/getTickers')
                .then(res => res.json())
                .then(data => {
                    const tickerData = [];
                    for (let company in data.tickers) {
                        let obj = {};
                        obj['name'] = company;
                        obj['value'] = data.tickers[company];
                        tickerData.push(obj);
                    }

                    this.setState({ tickers: tickerData });
                });
        }, 1000);
    }

    render() {
        const { tickers } = this.state;
        return (
            <div>
                { tickers ? <h1>Today's stocks!</h1> : <h1>oops! something isn't working</h1> }
                { tickers.map(ticker => <h2>{ticker.name.toUpperCase()}: ${ticker.value}</h2>) }
            </div>
        );
    }
}

// <img src={ReactImage} alt="react" />
