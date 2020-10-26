import React, { Component, useEffect } from 'react';
import './app.css';
import ReactImage from './react.png';
import PriceTable from './components/PriceTable';
import PriceGraph from './components/PriceGraph';

function padPriceString(price) {
    let priceString = price.toString();
    if (!priceString.split('.')[1]) {
        priceString += '00';
    } else if (priceString.split('.')[1].length === 1) {
        priceString += '0';
    }

    return priceString;
}

function processForTable(json) {
    const tickerData = [];
    for (let company in json.tickers) {
        let obj = {};
        obj['name'] = json.tickers[company].name;
        obj['price'] = padPriceString(json.tickers[company].price);
        obj['direction'] = json.tickers[company].percentChange > 0;
        tickerData.push(obj);
    }

    return tickerData;
}

export default class App extends Component {
    constructor(props) {
      super();
      this.state = {
          tickers: []
      };
    }

    componentDidMount() {
        fetch('/api/getTickers')
            .then(res => res.json())
            .then(data => {
                this.setState({ tickers: processForTable(data) });
            });
    }

    componentDidUpdate() {
        setTimeout(() => {
            fetch('/api/getTickers')
                .then(res => res.json())
                .then(data => {
                    this.setState({ tickers: processForTable(data) });
                });

        }, 1000);
    }

    render() {
        const { tickers } = this.state;
        return (
            <div>
                { tickers ? <h1>Simple Robinhood!</h1> : <h1>oops! something isn't working</h1> }
                <PriceTable tickers={tickers} />
            </div>
        );
    }
}
