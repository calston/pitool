var IOs = [];
var sparks = {};
var socket = null;
var listening = false;
var update_lock = false;
var active = [];

var baseLabels = {
  10: "10\265s",
  100: "100\265s",
  1000: "1ms",
  10000: "10ms",
  100000: "100ms",
  1000000: "1s",
  2000000: "2s",
  5000000: "5s",
  10000000: "10s"
}

function createGpioSlot(gpio) {
  IOs.push(gpio);

  var index = IOs.length - 1;
  var bcid = gpio.bcm_id;

  active.push(bcid);

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

  sparks[bcid] = $("#spark"+bcid).peity("line", { width: '100%', height: 24 })

  // Add row to dropdown
  var dropdown =  "<li><a href=\"#\" onclick=\"return toggleChan(" + bcid + ")\" id=\"chantog" + bcid + "\">Disable GPIO " + bcid + "</a></li>";
  $(dropdown).appendTo($("#chandropdown"));
};

function toggleChan(chan) {
  if (chan == 0) {
    if (active.length > 0) {
      $("#chantog0").text("Enable All");
      $.each(active, function (i, ch) {
        $("#chantog" + ch).text("Enable GPIO " + ch);
        $("#gp" + ch).hide();
      });
      active = []
    }
    else {
      $("#chantog0").text("Disable All");
      $.each(IOs, function (i, g) {
        var ch = g.bcm_id;
        $("#chantog" + ch).text("Disable GPIO " + ch);
        $("#gp" + ch).show();
        active.push(ch);
      });
    }
  }
  else {
    var index = active.indexOf(chan);

    if (index > -1) {
      // Deactivate
      active.splice(index, 1);
      $("#chantog" + chan).text("Enable GPIO " + chan);
      $("#gp" + chan).hide();
    }
    else {
      active.push(chan);
      $("#chantog" + chan).text("Disable GPIO " + chan);
      $("#gp" + chan).show();
    }
  }

  $("#chanlist").text("Enabled Channels: [" + active.join(", ") + "]");
  send_command("set_channels", {'active': active});

  return false;
}

function initialWaveforms(waves) {
  if (update_lock) {
    return false;
  }

  update_lock = true
  $.each(waves, function(i, wave) {
    if (wave.buffer) {
      sparks[wave.id].text(wave.buffer.join(",")).change();
    }
  });
  update_lock = false
  $("#gobutton").text("Go!");
};

function send_command(cmd, args) {
  socket.send(JSON.stringify({
    "type": cmd,
    "args": args
  }));
};

function setTimebase(val) {
  send_command('set_timebase', {'val': val});
  $("#timebase").html(baseLabels[val] + " <span class=\"caret\"></span>");
  return false;
}

function setWindow(val) {
  send_command('set_window', {'val': val});
  $("#window").html(baseLabels[val] + " <span class=\"caret\"></span>");
  return false;
}

function setOneshot() {
  send_command('stop_buffer_stream', {});
  $("#realtime").hide();
  $("#oneshot").show();
}

function oneShotGo() {
  send_command('one_shot', {'trigger': null});
  $("#gobutton").text("Wait...");
}

function setRealtime() {
  send_command('start_buffer_stream', {});
  $("#oneshot").hide();
  $("#realtime").show();
}

function start_analyzer() {
  var loc = new URI(document.location);
  var host = loc.hostname();

  $.getJSON( "/api/gpio", function( data ) {
    var dropdown =  "<li><a href=\"#\" onclick=\"return toggleChan(0)\" id=\"chantog0\">Disable All</a></li>";
    $(dropdown).appendTo($("#chandropdown"));

    // Add header objects to dom
    $.each( data.pins, function( i, gpio ) {
      if (gpio["mode"] == "Input") {
        createGpioSlot(gpio);
      }
    });

    $("#chanlist").text("Channels: " + active.join(", "));

    // Connect to websocket service
    socket = new WebSocket(sprintf('ws://%s:8082/', host));

    socket.onopen = function (event) {
        setRealtime();
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
};
