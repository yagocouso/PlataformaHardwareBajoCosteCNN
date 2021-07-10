'use strict'
var mongoose = require("mongoose");
var app = require('./app');
var port = 8592;

mongoose.Promise =  global.Promise;
mongoose.connect('mongodb://localhost:27017/Arduino')
        .then(()=>{
            // Creacion del servidor
            app.listen(port, ()=>{
                console.log("Starting server in port", port);
            });
        })
        .catch(err => console.log(err));