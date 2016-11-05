
var currentVendorNum= -1;
//if from presenter, the [bid] button is displayed.
var  isFromPresenter = false;
//one attendee can only bid once
var hasBid = false;

var socket = io('http://au-china-forge.herokuapp.com/');

//for CNC
var _viewer;
var gcode;
var modelOffset = null;
var timer = null;
var gCodePoints = null;
var lasPT= null;
var gCodeIndex = 0;
var material = new THREE.LineBasicMaterial({ color: 0xff0000 });

function getParameterByNameFromPath (name, url) {
   name = name.replace(/[\[]/, "\\\[").replace(/[\]]/, "\\\]");
   var regexS = "[\\?&]" + name + "=([^&#]*)";
   var regex = new RegExp(regexS);
   var results = regex.exec(url);
   if (results == null)
      return "";
   else
      return decodeURIComponent(results[1].replace(/\+/g, " "));
}

function  refreshRFQPage(msg)
{


    var RFQInfo = eval("(" + msg + ")");


   var newHTML =
           '<img id="partimg" src="data:image/jpeg;base64,' + RFQInfo.image +'"/>'
           +'<br><br>'
           +'<h3 ><span class="label label-default" id="filename">Part Name</span>' + RFQInfo.filename + '</h3>'
           +'<h3 ><span class="label label-default"  id="partnum">Part Number</span>' + RFQInfo.partnum + '</h3>'
           +'<h3 ><span class="label label-default"  id="material">Material </span>' + RFQInfo.material + '</h3>'
           +'<h3 ><span class="label label-default"  id="quantity">Quanity</span>' + RFQInfo.quantity + '</h3>'
           +'<button class="btn btn-primary" id="downloadfile" >Download Model</button>'
           + '<div>'
                 +'<h3><span class="label label-default">Description</span></h3>'
                 +'<textarea class="form-control" rows="5" id="desc">More Detailed Description</textarea>'
           +'</div>'
            +'<h3 ><span class="label label-default"  id="company">Company</span>' + RFQInfo.company + '</h3>'
           +'<h3 ><span class="label label-default"  id="contact">Contact</span>' + RFQInfo.contact + '</h3>'
           +'<h3 ><span class="label label-default"  id="email">Email</span>' + RFQInfo.email + '</h3>'
           +'<h3 ><span class="label label-default"  id="phone">Phone</span>' + RFQInfo.phone + '</h3>'
            + '<h3 ><span class="label label-default"  id="bidCost">Quote</span></h3>'
           + '<button type="button" id = "bid" class="btn btn-lg btn-primary">Bid</button>'
           + '<div>'
           +    '<div id="viewerDiv"></div>'
           + '</div >' ;


    $('#RFQ').innerHTML = '';
    $('#RFQ').html( newHTML);

    if(_viewer != null)
    {
        _viewer.uninitialize();
        _viewer = null;
    }

    loadView(RFQInfo.urn);

    $('#bid').click(function(evt) {
        if(isFromPresenter) {
            if(hasBid){
                alert('Your have bid！');
            }
            else {
                var rand = Math.random();
                $('#bidCost').text(rand * 100);
                var BidInfo = {
                    vendorNum: currentVendorNum,
                    cost: rand * 100
                };
                //send to vendor page
                socket.emit('au_BID', JSON.stringify(BidInfo));
                hasBid =true;
            }

        }
        else {
            alert('Lottery Draw not started！');
        }
   });
}

$(document).ready (function () {

   var vendorNum = getParameterByNameFromPath('vendorNum',window.location.href);
   var vendorNum = (vendorNum !== '' ? vendorNum : 0 );
    currentVendorNum = vendorNum;

   if(vendorNum > 0){
      //attendees
      $("#useremailimg").attr('src','images/vendor.png');
      $('#username').val('Vendor No： ' + vendorNum);
   }

    socket.on('au_RFQ', function(msg) {

      console.log('One RFQ from Presenter');
        isFromPresenter = true;
        hasBid = false;
      refreshRFQPage(msg);
   });

   socket.on('au_RFQ_' + vendorNum, function(msg) {
      console.log('One RFQ from One Customer: ' + vendorNum -1);
      refreshRFQPage(msg);
   });

    socket.on('au_CNC', function(msg) {
        console.log('CNC Started1 ');
        DoCNC(msg);

     });

}) ;//docuemnt teady

function loadView(urn)
{
    var xhr = new XMLHttpRequest();
    xhr.open("GET", 'http://' + window.location.host + '/ForgeRoute/gettoken', false);
    xhr.send(null);
    var json = eval('(' + xhr.responseText + ')');
    var token =  json.access_token;

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




function  drawLine()
{
    if(gCodeIndex >=gCodePoints.length)
    {
        clearInterval(timer);
        gCodeIndex = 0;;
        return;
    }
    if(gCodePoints[gCodeIndex].type=='m5')
    {
        //stop animation
        clearInterval(timer);
        gCodeIndex = 0;;
    }
    else if(gCodePoints[gCodeIndex].type=='g0')
    {
        gCodeIndex+=2;
        //g1 - z
        var z = parseFloat(gCodePoints[gCodeIndex].value.z - modelOffset.z+5);
        gCodeIndex++;
        //g1
        var x = parseFloat(gCodePoints[gCodeIndex].value.x- modelOffset.x);
        var y = parseFloat(gCodePoints[gCodeIndex].value.y- modelOffset.y);

        //build the first pt of next curve
        lasPT = new THREE.Vector3( x, y, z );
    }
    else
    {
        //next point of current curve

        var x = parseFloat(gCodePoints[gCodeIndex].value.x- modelOffset.x);
        var y = parseFloat(gCodePoints[gCodeIndex].value.y- modelOffset.y);
        var z = lasPT.z;
        currentPT = new THREE.Vector3( x, y, z );

        var geometry = new THREE.Geometry();
        geometry.vertices.push( lasPT );
        geometry.vertices.push(currentPT);

        var newLine = new THREE.Line( geometry, material );

        _viewer.impl.scene.add(newLine);
        _viewer.impl.invalidate(true);

        lasPT = currentPT;
    }

    gCodeIndex++;
}



function DoCNC(msg){

    var filename = JSON.parse(msg).filename;

    $.ajax ({
        url: 'http://' + window.location.host + '/ForgeRoute/cncdata/'+filename,
        type: 'get',
        data: null,
        contentType: 'application/json',
        complete: null
    }).done (function (response) {
        if(response.err){
            console.log('get token error:' + response.err);
        }
        else {
            gcode = response;
            gCodePoints = JSON.parse(gcode).gcode;

            if(gCodePoints.length > 0) {
                _viewer = viewerApp.myCurrentViewer;
                modelOffset = _viewer.model.getData().globalOffset;
                gCodeIndex = 0;
                startCNC();
            }
            else {
                alert('no CNC data with this model!');
            }
        }
    }).fail (function (xhr, ajaxOptions, thrownError) {
        console.log('get token error:' + response.err);
    }) ;
}

function startCNC() {


    var geometry = new THREE.Geometry();
    gCodeIndex = 0;

    while (gCodePoints[gCodeIndex].type != 'g4') {
        gCodeIndex++;
    }

    gCodeIndex += 2;  //skipp g4 and g0

//g1 - z
    var z = parseFloat(gCodePoints[gCodeIndex].value.z - modelOffset.z+5);
    gCodeIndex++;
    var x = parseFloat(gCodePoints[gCodeIndex].value.x -  modelOffset.x);
    var y = parseFloat(gCodePoints[gCodeIndex].value.y-  modelOffset.y);

//build the first pt of first curve
    lasPT = new THREE.Vector3(x, y, z);

    gCodeIndex++;


    var geometry_cylinder = new THREE.CylinderGeometry( 1, 1, 10, 32 );
    var material_cylinder= new THREE.MeshBasicMaterial( {color: 0xffff00} );
    var cylinder = new THREE.Mesh( geometry_cylinder, material_cylinder );
    _viewer.impl.scene.add(cylinder);
    _viewer.impl.invalidate(true);

    cylinder.translateX( 10 );
    cylinder.translateY( 10 );
    cylinder.translateZ( 10 );


    timer = setInterval(drawLine, 100);
}
