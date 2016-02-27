function handleImages(telemJson) {
    image_panel = $('#images');
    var image_list = telemJson['images'];
    $.each(image_list, function( index, value ) {
        console.log("Parsing: " + value);
        image_panel.append('<div class="col-lg-3 col-md-4 col-xs-6"><img class="img-responsive" src="'+value+'" alt=""></div>')
    });
}