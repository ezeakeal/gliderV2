
$(document).ready(function () {
    init();
    setupWings();
    setTelemRequest();
    animate();
    hookMapUpdateTimer();
    $('#gliderTabs').click(function(){
        setTimeout(function(){
            window.dispatchEvent(new Event('resize')); // Forces resize event for iframe resizes
        }, 500);
    })
});

TELEMETRY = {}

function setTelemRequest(){
    setInterval(function(){
        $.ajax({
            url: "getTelem",
            success: function(telemRes){
                telemJSON =  JSON.parse(telemRes);
                TELEMETRY = telemJSON;
                window.handleTelemetry(TELEMETRY);
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
            },
        });
    }, 10);
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
        $(this).val($(this).html()).trigger('change');
    })
    
}

function handleTelemetry(telemJSON){
    renderTelemetry(telemJSON)
    updateMarker(telemJSON);
}