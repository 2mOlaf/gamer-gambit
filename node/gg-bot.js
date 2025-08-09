var app = require('express')();
var http = require('http').Server(app);
var io = require('socket.io')(http);
var port = process.env.PORT || 8080;

var events = require('events');
var eventEmitter = new events.EventEmitter();

app.get('/', function(req, res){
  res.sendFile(__dirname + '/index.html');
});

eventEmitter.on('logging', function(message) {
  io.emit('log_message', message);
});

http.listen(port, function(){
  console.log('listening on *:' + port);
});

// Override console.log
var originConsoleLog = console.log;
console.log = function(data) {
  eventEmitter.emit('logging', data);
  originConsoleLog(data);
};

// code for test.
// setInterval(function() {
//   console.log('X: ' + Math.random());
// }, 2000);