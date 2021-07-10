'use strict'

var Data = require('../models/data');
var State = require('../models/state');

var controller = {
    home: function(req, res){
        console.log(new Date());
        console.log(req.body);
        return res.status(200).send({
            message: "Soy la home"
        })
    }, 

    test: function(req, res){
        return res.status(200).send({
            message: "Soy el metodo o accion del controlador de project"
        });
    },

    saveData: function(req, res){
        let params = req.body;
        params.sort((a, b) => {return a.t - b.t});
        let max = params[params.length - 1].t;
        let ahora = new Date();
        for (let fila of params){
            let diff = max - fila.t;
            let fecha_excta = ahora.getTime() - diff;
            let resp = {
                uid: req.headers.host, 
                ax: fila.x, 
                ay: fila.y, 
                az: fila.z,
                gx: fila.u, 
                gy: fila.v, 
                gz: fila.w,
                date: new Date(fecha_excta),
            };
            let dato = new Data(resp)
            dato.save((err, dataStored)=>{
                //if(err) console.log(err);
                console.log(dataStored);
            });
        }
        return res.status(200).send("OK");
        data.save((err, dataStored)=>{
            if(err) return res.status(500).send("Error al guardar");
            if (!dataStored) return res.status(404).send("No se a podido guardar el proyecto");
            return res.status(200).send("OK")
        })
    },

    getData: function(req, res){
        var dataId = req.params.id;
        if (dataId == null) res.status(404).send({message: "El proyecto no existe"});
        Data.findById(dataId, (err, data)=>{
            if (err) return res.status(500).send({message: "Error al devolver los datos"});
            if (!data) return res.status(404).send({message: "El proyecto no existe"});
            return res.status(200).send({data});
        })
    },

    getInfo: function(req, res){
        let start = req.params.start;
        let end = req.params.end;
        console.log(req.params);
        if (!start || isNaN(end)) {
            start = new Date();
            //console.log("Arrancamos", start);
            start.setDate(start.getDate() - 1);
            console.log("Arrancamos", start);
        } else {
            start = parseInt(start);
            start = new Date(start);
        }
        if (!end || isNaN(end)) {
            end = new Date();
            end.setDate(start.getDate() + 1);
        } else {
            end = parseInt(end);
            end = new Date(end);
        }
        console.log(start);
        console.log(end);
        //return res.status(200).send("Todo OK");
        Data.find({date:{"$gte": start, "$lte":end}}).exec((err, datas)=> {
            console.log(datas);
            if (err) return res.status(500).send({message: "Error al devolver los datos"});
            if (!datas) return res.status(404).send({message: "No hay proyectos para mostrar"});
            return res.status(200).send({datas});
        })
    },

    stateData: function(req, res){
        let params = req.body;
        console.log("Datos recibidos", params);
        /*let resp = {
            date: new Date(),
            host: req.headers.host,
            stop: params.stop,
            walk: params.walk,
            run: params.run
        };
        let dato = new State(resp)
        dato.save((err, dataStored)=>{
            console.log(dataStored);
        });*/
    return res.status(200).send("OK");
    }

}

module.exports = controller;