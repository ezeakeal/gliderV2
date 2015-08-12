var container, stats;
var camera, cameraTarget, scene, renderer;
var mouseX = 0, mouseY = 0;

var gliderObj;
var windowHalfX = window.innerWidth / 2;
var windowHalfY = window.innerHeight / 2;

de2ra = function(degree){ 
    return degree*(Math.PI/180); 
}

$(document).ready(function () {
    init();
    animate();
    hookMapUpdateTimer();
});

function init() {
    // Getting the container for later..
    container = document.getElementById( 'glider_div' );

    // Camera setup
    camera = new THREE.PerspectiveCamera( 45, container.clientWidth / container.clientHeight, 1, 2000 );
    camera.position.z = 15;
    camera.position.y = 7;
    camera.position.x = 10;
    cameraTarget = new THREE.Vector3( 0, 0, 0 );

    // scene
    scene = new THREE.Scene();

    // Add lighting
    var ambient = new THREE.AmbientLight( 0xAAAAAA );
    scene.add( ambient );
    var directionalLight = new THREE.DirectionalLight( 0xffeedd );
    directionalLight.position.set( 2, 5, 7 ).normalize();
    scene.add( directionalLight );

    // Setup loading manager
    var manager = new THREE.LoadingManager();
    manager.onProgress = function ( item, loaded, total ) {
        console.log( item, loaded, total );
    };

    // model
    var loader = new THREE.OBJMTLLoader( manager );
    loader.load( '/static/glider/glider.obj', '/static/glider/glider.mtl', function ( object ) {
        scene.add( object );
        gliderObj = object;
    }, function ( xhr ) {
        if ( xhr.lengthComputable ) {
            var percentComplete = xhr.loaded / xhr.total * 100;
            console.log( Math.round(percentComplete, 2) + '% downloaded' );
        }
    }, function ( xhr ) {
    } );
        
    

    // YAW
    var plane = new THREE.Mesh(
        new THREE.PlaneBufferGeometry( 6, 6 ),
        new THREE.MeshPhongMaterial( { color: 0xFF0000, opacity: 0.2, transparent: true } )
    );
    plane.rotation.x = -Math.PI/2;
    scene.add( plane );
    // ROLL
    var plane = new THREE.Mesh(
        new THREE.PlaneBufferGeometry( 6, 10 ),
        new THREE.MeshPhongMaterial( { color: 0x00FF00, opacity: 0.2, transparent: true } )
    );
    plane.rotation.z = -Math.PI/2;
    plane.position.x = -5;
    scene.add( plane );
    // PITCH
    var plane = new THREE.Mesh(
        new THREE.PlaneBufferGeometry( 3, 6 ),
        new THREE.MeshPhongMaterial( { color: 0x0000FF, opacity: 0.2, transparent: true } )
    );
    plane.rotation.y = Math.PI/2;
    plane.position.z = 1.5;
    scene.add( plane );

    // Setup the Renderer
    renderer = new THREE.WebGLRenderer();
    renderer.setSize( container.clientWidth, container.clientHeight );

    renderer.shadowCameraNear = 3;
    renderer.shadowCameraFar = 40;
    renderer.shadowCameraFov = 45;
    container.appendChild( renderer.domElement );
    // Setup the stats item
    stats = new Stats();
    stats.domElement.style.position = 'absolute';
    stats.domElement.style.top = '0px';
    container.appendChild( stats.domElement );
    
    document.addEventListener( 'mousemove', onDocumentMouseMove, false );
    window.addEventListener( 'resize', onWindowResize, false );
}


function onWindowResize() {
    container = document.getElementById( 'glider_div' );

    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize( container.clientWidth, container.clientHeight );
}

function animate() {
    requestAnimationFrame( animate );
    $.ajax({
        url: "getTelem",
        data: {
        },
        success: function(telemRes){
            telemJSON =  JSON.parse(telemRes);
            $.each(telemJSON, function(key, val) {
                var sel = '#telemPacket dd[param="'+key+'"]'
                $(sel).html(val);
            });
            updateMarker(telemJSON);
            render(telemJSON);
        },
        error: function (xhr, ajaxOptions, thrownError) {
            console.log(xhr.status);
            console.log(thrownError);
        },
    });
    stats.update();
}

function render(telemJSON) {
    if (gliderObj) {
        gliderObj.rotation.x = de2ra(parseFloat(telemJSON['O_P']));
        gliderObj.rotation.y = de2ra(parseFloat(telemJSON['O_R']));
        gliderObj.rotation.z = de2ra(parseFloat(telemJSON['O_Y']));
    }
    camera.lookAt( cameraTarget );
    renderer.render( scene, camera );
}

function onDocumentMouseMove( event ) {
}
