
$(document).ready(function () {
    setupTelemAjax();
});

function setupTelemAjax(){
    setInterval(function(){
        console.log("Requesting Telemetry");
        $.ajax({
            url: "getTelem",
            success: function(telemData){
                parseTelemetryData(telemData);
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
            },
        });
    }, 3000);
}

function parseTelemetryData(telemData){
    telemJSON =  JSON.parse(telemData);
    handleTelemetry(telemJSON);
}


function handleTelemetry(telemJSON){
    console.log(telemJSON);
    window.updateMapMarkers(telemJSON);
    window.createTelemWindows(telemJSON);
}


function createTelemWindows(all_data){
    for (var callsign in all_data) {
        if (all_data.hasOwnProperty(callsign)) {
            callsign_window = $('#window_' + callsign);
            if (callsign_window.length == 0){
                console.log("Creating Window for: " + callsign);
                var window_html = [
                    "<div style='border-style: solid;border-radius: 5px;border-width: 1px;' id='" + "window_" + callsign + "'>",
                    "</div>"
                ]
                $('#telemPacket').append(window_html.join(""));
            };
            console.log("Updating window for: " + callsign);
            var lat = all_data[callsign]['lat'];
            var NS = all_data[callsign]['NS'];
            var lon = all_data[callsign]['lon'];
            var EW = all_data[callsign]['EW'];
            var alt = all_data[callsign]['alt'];
            var hhmmss = all_data[callsign]['hhmmss'];
            var time_received = all_data[callsign]['time_received'];
            var window_content_html = [
                "<h4>" + callsign + "</h4>",
                "<dl class='dl-horizontal'>",
                "  <dt>LAT</dt><dd>"+lat+" "+NS+"</dd>",
                "  <dt>LON</dt><dd>"+lon+" "+EW+"</dd>",
                "  <dt>ALT</dt><dd>"+alt+"</dd>",
                "  <dt>HHMMSSS</dt><dd>"+hhmmss+"</dd>",
                "</dl>",
                "<div class='btn-group btn-group-justified' role='group'>",
                "<a name='predict' class='btn btn-sm btn-info'",
                "data-lat='"+lat+"'",
                "data-lon='-"+lon+"'",
                "data-alt='"+alt+"'",
                ">Flight</a>",
                "<a name='predict_landing' class='btn btn-sm btn-warning'",
                "data-lat='"+lat+"'",
                "data-lon='-"+lon+"'",
                "data-alt='"+alt+"'",
                ">Landing</a>",
                "</div>"
            ]
            callsign_window.html(window_content_html.join(""));
            bind_buttons();
        }
    }
}

function bind_buttons(){
    $('a[name="predict"]').off("click");
    $('a[name="predict"]').on("click", function(){
        console.log(this);
        call_predict(this);
    });
    $('a[name="predict_landing"]').on("click", function(){
        console.log(this);
        call_predict_landing(this);
    });
}

function call_predict(button){
    $.ajax({
        url: "getPredict",
        method: "POST",
        data: {
            lat: $(button).data("lat"),
            lon: $(button).data("lon"),
            alt: $(button).data("alt")
        },
        success: function(url){
            var win = window.open(url, '_blank');
            win.focus();
        },
        error: function (xhr, ajaxOptions, thrownError) {
            console.log(xhr.status);
            console.log(thrownError);
        },
    });
}

function call_predict_landing(button){
    $.ajax({
        url: "getPredictLand",
        method: "POST",
        data: {
            lat: $(button).data("lat"),
            lon: $(button).data("lon"),
            alt: $(button).data("alt")
        },
        success: function(url){
            var win = window.open(url, '_blank');
            win.focus();
        },
        error: function (xhr, ajaxOptions, thrownError) {
            console.log(xhr.status);
            console.log(thrownError);
        },
    });
}