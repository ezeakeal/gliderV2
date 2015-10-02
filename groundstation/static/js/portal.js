
$(document).ready(function () {
    check_alert();
    init();
    setupWings();

    if (window.WebSocket){
         console.log("WebSockets: Supported");
         setTelemSocket();
    } else {
         console.err("WebSockets: Not Supported");
         setTelemAjax();
    }
    
    animate();
    hookMapUpdateTimer();
    $('#gliderTabs').click(function(){
        setTimeout(function(){
            window.dispatchEvent(new Event('resize')); // Forces resize event for iframe resizes
        }, 500);
    })
});

TELEMETRY = {}

function setTelemAjax(){
    setInterval(function(){
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
    }, 20);
}

function setTelemSocket(){
    console.log("Creating websocket")    
    var ws = new WebSocket("ws://localhost:8888/getTelemSocket");

    ws.onmessage = function(event) {
        parseTelemetryData(event.data);
        console.log(event.data);
    }
}

function parseTelemetryData(telemData){
    telemJSON =  JSON.parse(telemData);
    TELEMETRY = telemJSON;
    window.handleTelemetry(TELEMETRY);
}

function setupWings(){
    $("#W_L").knob({
        'width': '95%',
        'readOnly': true,
    });
    $("#W_R").knob({
        'width': '95%',
        'readOnly': true,
    });
}

function renderTelemetry(telemJSON){
    function addToIDByKey(key, val){
        var sel = '#'+key;
        $(sel).html(val);
    };

    $.each(telemJSON['orientation'], addToIDByKey);
    $.each(telemJSON['wing'], addToIDByKey);
    $.each(telemJSON['gps'], addToIDByKey);

    // Update wing angles
    $('.dial').each(function(){
        var ang = $(this).text();
        $(this).val(ang).trigger('change');
    })
    
}

function handleTelemetry(telemJSON){
    renderTelemetry(telemJSON)
    updateMarker(telemJSON);
}

function check_alert(){
    var message = getParameterByName('msg');
    $.notify({
        'message': message
    });
}

function getParameterByName(name) {
    name = name.replace(/[\[]/, "\\[").replace(/[\]]/, "\\]");
    var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
        results = regex.exec(location.search);
    return results === null ? "" : decodeURIComponent(results[1].replace(/\+/g, " "));
}