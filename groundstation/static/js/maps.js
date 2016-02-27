/* google maps -----------------------------------------------------*/
google.maps.event.addDomListener(window, 'load', initialize_map);

var map;
var marker;

function initialize_map() {
    var latlng = new google.maps.LatLng(52.3731, 4.8922);

    var mapOptions = {
        center: latlng,
        zoom: 13
    };

    marker = new google.maps.Marker({
        position: latlng,
        url: '/',
        animation: google.maps.Animation.DROP
    });

    map = new google.maps.Map(document.getElementById("map_plot"), mapOptions);
    marker.setMap(map);
};


function hookMapUpdateTimer(){
    setInterval(function(){
        updateMapPosition();
    }, 15000);
};

function updateMapPosition(){
    if (marker){
        console.log("Recentering Map");
        map.setCenter(marker.getPosition()); 
        google.maps.event.trigger(map, 'resize');
    }
};

function updateMarker(telemJSON){
    if (marker){
        var lat = telemJSON['lat'];
        var lon = telemJSON['lon'];
        var latlng = new google.maps.LatLng(lat, lon);
        marker.setPosition(latlng);
    }
}