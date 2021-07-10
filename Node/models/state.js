'use strict'

var mongoose = require('mongoose');
var Schema = mongoose.Schema;

var DataSchema = new Schema({
    date: Date,
    host: String,
    stop: Number,
    walk: Number,
    run: Number,
})

module.exports = mongoose.model('state', DataSchema);
