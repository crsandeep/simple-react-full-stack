const express = require('express');
const path = require('path');

const app = express();

// Serve static React build
app.use(express.static(path.join(__dirname, 'public')));

app.get('/health', (req, res) => {
  res.send('OK');
});

app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
