$(document).ready(function () {
	bindTelemQuery();
});

function bindTelemQuery(){
    setInterval(function(){ 
        console.log("Making telemetry request");
        $.ajax({
            url: "getTelem",
            data: {
            },
            success: function(telemRes){
                telemJSON =  JSON.parse(telemRes);
                console.log(telemJSON);
                $.each(telemJSON, function(key, val) {
                    var sel = '#telemPacket dd[param="'+key+'"]'
                    console.log("Finding Sel("+sel+") for val: " + val);
                    $(sel).html(val);
                });
                
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.err(xhr.status);
                console.err(thrownError);
            },
        });
    }, 5000);
}

function updateRendering(){

}