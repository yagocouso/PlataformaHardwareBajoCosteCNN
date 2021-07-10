'use strict'

var express = require('express');
var DataController = require('../controllers/data');

var router = express.Router();

router.get('/home', DataController.home);
router.get('/', DataController.home);
router.post('/', DataController.saveData);
router.post('/test', DataController.test);
router.post('/savedata', DataController.saveData);
router.post('/state', DataController.stateData);
//router.get('/data/:id?', DataController.getData);
//router.get('/data/:start?:end?', DataController.getData);
router.get('/data/:start?/:end?', DataController.getInfo);

module.exports = router;