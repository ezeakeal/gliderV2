
$(document).ready(function () {
    init();
    animate();
    hookMapUpdateTimer();
    $('#gliderTabs').click(function(){
        setTimeout(function(){
            window.dispatchEvent(new Event('resize')); // Forces resize event for iframe resizes
        }, 500);
    })
});


function renderTelemetry(telemJSON){
    function addToIDByKey(key, val){
        var sel = '#'+key;
        $(sel).html(val);
    };

    $.each(telemJSON['orientation'], addToIDByKey);
    $.each(telemJSON['wing'], addToIDByKey)
    $.each(telemJSON['gps'], addToIDByKey);
}

function handleTelemetry(telemJSON){
    renderTelemetry(telemJSON)
    updateMarker(telemJSON);
    render(telemJSON);
}