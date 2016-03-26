var IOs = [];
var sparks = {};

var listening = false;

function createGpioSlot(gpio) {
  IOs.push(gpio);
  var bcid = gpio.bcm_id;
  var doc="<div class=\"analyzer row\" id=\"gp"+bcid+"\">";

  doc += "<div class=\"col-lg-1 col-md-1 col-sm-1 col-xs-1 gpio-cell\">";
  doc += "<strong>GPIO"+bcid+"</strong>";
  doc += "</div>";

  doc += "<div class=\"col-lg-11 col-md-11 col-sm-11 col-xs-11 gpio-cell\">";
  doc += '<span class="gpio-chart" id="spark'+bcid+'"></span>';
  doc += "</div>";

  doc += "</div>";

  // Add row to doc
  $(doc).appendTo($("#gpiolist"));

  sparks[bcid] = $("#spark"+bcid).peity("line", { width: '100%' })
}

function initialWaveforms(waves) {
   $.each(waves, function(i, wave) {
      if (wave.buffer) {
        sparks[wave.id].text(wave.buffer.join(",")).change();
      }
   });
};

function start_analyzer() {
  var loc = new URI(document.location);
  var host = loc.hostname();

  $.getJSON( "/api/gpio", function( data ) {
    // Add header objects to dom
    $.each( data.pins, function( i, gpio ) {
      if (gpio["mode"] == "Input") {
        createGpioSlot(gpio);
      }
    });

    // Connect to websocket service
    var socket = new WebSocket(sprintf('ws://%s:8082/', host));

    socket.onopen = function (event) {
        socket.send("start_buffer_stream");
    };

    socket.onmessage = function (event) {
      // Parse JSON message and dispatch to processor functions
      var msg = JSON.parse(event.data);
      switch (msg.type) {
        case "waveform_update":
          waveformUpdate(msg.payload)
          break;

        case "waveform_start":
          initialWaveforms(msg.payload);
          break;
      }
    };
  });
}
