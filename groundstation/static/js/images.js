function handleImages(telemJson) {
    image_panel = $('#image_display');
    var image_list = telemJson['images'];
    image_panel.html('');
    $.each(image_list, function( index, value ) {
        console.log("Parsing: " + value);
        var timestamp = value.split("_")[1].split(".")[0]
        var imagetime = timestamp.substring(0, 2) + ":" + timestamp.substring(2, 4) + ":" + timestamp.substring(4, 6)
        image_panel.append('<div class="col-xs-12"><div class = "panel panel-default"><div class = "panel-heading">'+imagetime+'</div><div class = "panel-body"><img class="img-responsive" src="'+value+'" alt=""></div></div></div>')
    });
}

