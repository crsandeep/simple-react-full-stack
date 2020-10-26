const express = require('express');

const app = express();

const oldTickers = {
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

function calculatePercentChange(oldPrice, newPrice) {
    return Math.round((newPrice - oldPrice) * 10000 / oldPrice) /  100;
}

app.use(express.static('dist'));
app.get('/', (req, res) => {
    let newTickers = [];
    for (let company in oldTickers) {
        let obj = {}
        obj['name'] = company;
        const newPrice = recalculateUnitPrice(oldTickers[company]);
        obj['price'] = newPrice;
        obj['percentChange'] = calculatePercentChange(oldTickers[company], newPrice);
        obj['timestamp'] = new Date();
        newTickers.push(obj);
        oldTickers[company] = newPrice;
    }

    res.send({ tickers: newTickers });
});



app.listen(process.env.PORT || 8020, () => console.log(`Listening on port ${process.env.PORT || 8020}!`));
