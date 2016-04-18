/* google maps -----------------------------------------------------*/
google.maps.event.addDomListener(window, 'load', initialize_map);

var map;
var infowindow;
var marker_obj = {};

function initialize_map() {
    var pos = {lat: 53.50932, lng: -6.52371};
    var mapOptions = {
        center: pos,
        zoom: 10
    };
    map = new google.maps.Map(document.getElementById("map_plot"), mapOptions);
    infowindow = new google.maps.InfoWindow({
        content: 'Empty'
    });
};

function create_marker(telem_packet) {
    var callsign = telem_packet.callsign;
    var new_marker = new google.maps.Marker({
        position: {lat: 0, lng: 0},
        url: '/',
        animation: google.maps.Animation.DROP,
        title: callsign,
        label: callsign[0],
        map: map
    });
    marker_obj[callsign] = new_marker;
    google.maps.event.addListener(new_marker, 'click', function() {
        infowindow.setContent(new_marker.info_content);
        infowindow.open(map, new_marker);
    });
}

function updateMapMarkers(all_data){
    for (var callsign in all_data) {
        if (all_data.hasOwnProperty(callsign)) {
            console.log("Creating Marker for: " + callsign);
            if (! marker_obj.hasOwnProperty(callsign)){
                create_marker(all_data[callsign]);
            }
            var lat = all_data[callsign]['lat'];
            var lon = all_data[callsign]['lon'];
            var alt = all_data[callsign]['alt'];
            var hhmmss = all_data[callsign]['hhmmss'];
            var time_received = all_data[callsign]['time_received'];
            var date = new Date(0); // The 0 there is the key, which sets the date to the epoch
            date.setUTCSeconds(time_received);

            if (all_data[callsign]['NS'] == "S")
                lat = lat * -1;
            if (all_data[callsign]['EW'] == "W")
                lon = lon * -1;

            var latlng = new google.maps.LatLng(
                lat, lon
            );

            html_content = "<h2>" + callsign + "</h2>";
            html_content += "<p>Received: " + date.getHours() + ":" + date.getMinutes() + ":" + date.getSeconds() + "</p>";
            html_content += "<p>HHMSS: " + hhmmss + "</p>";
            html_content += "<p>LAT: " + lat + "</p>";
            html_content += "<p>LON: " + lon + "</p>";
            html_content += "<p>ALT: " + alt + "</p>";
            marker_obj[callsign].info_content = html_content;
            marker_obj[callsign].setPosition(latlng);
        }
    }
}