
var favicon = require('serve-favicon');
var ForgeRoute = require('./routes/ForgeRoute');
var express = require('express');
var app = express();
var server = require('http').Server(app);

var io = require('socket.io')(server);
io.on('connection', function(socket){
    console.log('connected');
    socket.on('au_RFQ', function(msg){

        var jsonObj = JSON.parse(msg);
        console.log('sending RFQ to vendor: ' + jsonObj.vendorNum );
        console.log(msg);

        if(jsonObj.sendAll)
            //emit the msg to all vendor
            io.emit('au_RFQ' , msg);
        else
            //emit the msg to specific vendor
        {
            console.log('au_RFQ_' + jsonObj.vendorNum);
            io.emit('au_RFQ_' + jsonObj.vendorNum, msg);
        }
    });

    socket.on('au_BID', function(msg){
        console.log('sending BID to : ' + msg.customerNum );
        //emit the msg to target vendor
        //send to customer 0 only for demo
        io.emit('au_BID' , msg);
    });

    socket.on('au_CNC', function(msg){
        console.log('sending CNC to : ' + msg.filename );
        //emit the msg to target vendor
        //send to customer 0 only for demo

        io.emit('au_CNC' , msg);
    });
});
app.io = io;

app.use('/', express.static(__dirname+ '/www') );
app.use(favicon(__dirname + '/www/images/favicon.ico'));
app.use('/ForgeRoute', ForgeRoute);

app.set('port', process.env.PORT || 3001);

server.listen(app.get('port'), function() {
    console.log('Server listening on port ' + server.address().port);
});



