
$(document).ready(function () {
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
        console.log("Selector: " + sel + " Val: " + val);
        $(sel).html(val);
    };
    $.each(telemJSON, addToIDByKey);

    $('#W_L').html(telemJSON['wings'][0])
    $('#W_R').html(telemJSON['wings'][1])
    $('#O_R').html(telemJSON['orientation'][0])
    $('#O_P').html(telemJSON['orientation'][1])
    $('#O_Y').html(telemJSON['orientation'][2])
    $('#STATE').html(telemJSON['state'][0])

    $.each(telemJSON['state'], addToIDByKey);
    $.each(telemJSON['images'], addToIDByKey);

    // Update wing angles
    $('.dial').each(function(){
        var ang = $(this).text();
        $(this).val(ang).trigger('change');
    })
    
}

function handleTelemetry(telemJSON){
    console.log(telemJSON);
    renderTelemetry(telemJSON)
    updateMarker(telemJSON);
    handleImages(telemJSON);
}

function getParameterByName(name) {
    name = name.replace(/[\[]/, "\\[").replace(/[\]]/, "\\]");
    var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
        results = regex.exec(location.search);
    return results === null ? "" : decodeURIComponent(results[1].replace(/\+/g, " "));
}