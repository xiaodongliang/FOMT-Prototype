var socket = io('http://au-china-forge.herokuapp.com');


var defaultUrn = 'urn:dXJuOmFkc2sub2JqZWN0czpvcy5vYmplY3Q6eGlhb2Rvbmd0ZXN0YnVja2V0L3JhY19hZHZhbmNlZC5ydnQ=';

var viewerApp;
var _viewer;
var _overrideFragIds = {};
var _overlayRed = 'red';


var material = new THREE.LineBasicMaterial({ color: 0xff0000 });

var isIoT = false;

function loadView(urn)
{
    $.ajax ({
        url: 'http://' + window.location.host + '/ForgeRoute/gettoken',
        type: 'get',
        data: null,
        contentType: 'application/json',
        complete: null
    }).done (function (response) {
        if(response.err){
            console.log('get token error:' + response.err);
        }
        else {

            var token =  response.access_token;
            var options = {
                env: 'AutodeskProduction',
                accessToken: token
            };
            Autodesk.Viewing.Initializer(options, function onInitialized(){

                var config3d = {
                    // extensions: ['Autodesk.Viewing.Extensions.Collaboration']
                };
                viewerApp = new Autodesk.A360ViewingApplication('viewerDiv');
                viewerApp.registerViewer(viewerApp.k3D, Autodesk.Viewing.Private.GuiViewer3D,config3d);
                viewerApp.loadDocumentWithItemAndObject(urn);
            });
        }
    }).fail (function (xhr, ajaxOptions, thrownError) {
        console.log('get token error:' + response.err);
    }) ;
}

function overrideColorOnFragments(fragIds, overlayName) {
    for (j=0; j<fragIds.length; j++) {
        var mesh = _viewer.impl.getRenderProxy(_viewer.impl.model, fragIds[j]);

        var myProxy = new THREE.Mesh(mesh.geometry, mesh.material);
        myProxy.matrix.copy(mesh.matrixWorld);
        myProxy.matrixAutoUpdate = false;
        myProxy.matrixWorldNeedsUpdate = true;
        myProxy.frustumCulled = false;
        _viewer.impl.addOverlay(overlayName, myProxy);
        _overrideFragIds[fragIds[j]] = myProxy;  // keep track of the frags so that we can remove later
    }
}

function restoreOverrideColor()
{
    for (var p in _overrideFragIds) {
        var mesh = _overrideFragIds[p];
        if (mesh) {
            _viewer.impl.removeOverlay(_overlayRed, mesh);
            //_viewer.impl.removeOverlay(_overlayBlue, mesh);
        }
    }
    _overrideFragIds = {};      // reset the fragIds array
    _viewer.showAll();

}

$(document).ready(function () {

    var paramUrn = Autodesk.Viewing.Private.getParameterByName('urn');
    var urn = (paramUrn !== '' ? paramUrn : defaultUrn);

    loadView(urn);

    $('#btndraw').click(function(evt){

    });

    $("#isiot").on("click", function(e){

        _viewer = viewerApp.myCurrentViewer;
        if(isIoT)
        {
            restoreOverrideColor();
            socket.removeAllListeners("au_IoT");
        }
        else {
             socket.on('au_IoT', function (msg) {

                 var IoTJson = eval("(" + msg + ")");
                 //var IoTJson = {windowNum:'183911',IoTData:{alpha:255,beta:0,gamma:0}};
                 var windowNum = IoTJson.windowNum;
                 var IoTData = IoTJson.IoTData;

                 var colorRed = new THREE.Color(IoTData.alpha, IoTData.beta, IoTData.gamma);

                 var matRed = new THREE.MeshBasicMaterial({color: colorRed});

                 _viewer.impl.removeOverlayScene(_overlayRed);
                 _viewer.impl.createOverlayScene(_overlayRed, matRed);

                 _viewer.search(windowNum, function (idArray) {
                     if (idArray.length > 0) {
                         var objTree = _viewer.model.visibilityManager.getInstanceTree();
                         var frags = [];
                         objTree.enumNodeFragments(idArray[0], function (fragId) {
                             frags.push(fragId);
                         });
                         overrideColorOnFragments(frags,_overlayRed);
                     }
                 });
             });
       }
        isIoT = !isIoT;
    });

});

function onError(error) {
    console.log('Error: ' + error);
};
