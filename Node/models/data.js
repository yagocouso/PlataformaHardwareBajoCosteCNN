'use strict'

var mongoose = require('mongoose');
var Schema = mongoose.Schema;

var DataSchema = new Schema({
    uid: String,
    ax: Number,
    ay: Number,
    az: Number,
    gx: Number,
    gy: Number,
    gz: Number,
    date: Date
})

module.exports = mongoose.model('data', DataSchema);
