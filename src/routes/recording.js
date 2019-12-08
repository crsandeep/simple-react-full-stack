var express = require('express');
var router = express.Router();

router.post('/start', async (req, res) => {
  const recording = await req.context.models.Recording.create({
    date: req.body.date,
    frame: {},
  });

  router.post('/start', async (req, res) => {
  const recording = await req.context.models.Recording.create({
    date: req.body.date,
    frame: {},
  });
