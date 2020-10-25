const express = require('express');
const os = require('os');

const app = express();

const initialTickers = {
    aapl: 115.60,
    sbux: 88.40,
    tsla: 453.81,
    pypl: 203.59,
    ba: 167.42
}


function recalculateUnitPrice(oldPrice) {
    const direction = Math.round(Math.random()) === 1 ? 1 : -1;
    const magnitude = Math.random() / 20;
    const coefficient = 1 + (direction * magnitude);
    const newPriceInCents = oldPrice * coefficient * 100;
    const newPrice = Math.round(newPriceInCents) / 100;
    return newPrice;
}

app.use(express.static('dist'));
app.get('/', (req, res) => {
    let newTickers = {};
    for (var company in initialTickers) {
        newTickers[company] = recalculateUnitPrice(initialTickers[company]);
    }

    res.send({ tickers: newTickers });
});



app.listen(process.env.PORT || 8020, () => console.log(`Listening on port ${process.env.PORT || 8020}!`));
