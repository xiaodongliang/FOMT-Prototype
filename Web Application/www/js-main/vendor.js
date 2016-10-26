
var currentVendorNum= -1;

var socket = io('http://au-china-forge.herokuapp.com/');

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

var  isFromPresenter = false;
var hasBid = false;
function  refreshRFQPage(msg)
{
   var RFQInfo = eval("(" + msg + ")");

   $('#RFQ').innerHTML = '';

   var newHTML =
           '<img id="partimg" src="data:image/jpeg;base64,' + RFQInfo.image +'"/>'
           +'<br><br>'
           +'<h3 ><span class="label label-default" id="filename">零件名</span>' + RFQInfo.filename + '</h3>'
           +'<h3 ><span class="label label-default"  id="partnum">零件编号</span>' + RFQInfo.partnum + '</h3>'
           +'<h3 ><span class="label label-default"  id="material">材料</span>' + RFQInfo.material + '</h3>'
           +'<h3 ><span class="label label-default"  id="quantity">数量</span>' + RFQInfo.quantity + '</h3>'
           +'<button class="btn btn-primary" id="downloadfile" >模型下载</button>'
           + '<div>'
                 +'<h3><span class="label label-primary">描述</span></h3>'
                 +'<textarea class="form-control" rows="5" id="desc">这里做一些描述</textarea>'
           +'</div>'
           +'<br><br><br><br>'
            +'<h4 ><span class="label label-default"  id="company">公司名</span>' + RFQInfo.company + '</h4>'
           +'<h4 ><span class="label label-default"  id="contact">联系人</span>' + RFQInfo.contact + '</h4>'
           +'<h4 ><span class="label label-default"  id="email">邮件</span>' + RFQInfo.email + '</h4>'
           +'<h4 ><span class="label label-default"  id="phone">联系电话</span>' + RFQInfo.phone + '</h4>'
            + '<h4 ><span class="label label-default"  id="bidCost">报价</span>000</h4>'
           + '<button type="button" id = "bid" class="btn btn-lg btn-primary">竞价</button>'
           + '<div>'
           +    '<div id="viewerDiv"></div>'
           + '</div >' ;


    $('#RFQ').html( newHTML);

    loadView(RFQInfo.urn);


    $('#bid').click(function(evt) {
        if(isFromPresenter) {
            if(hasBid){
                alert('您已经竞价了！');
            }
            else {
                var rand = Math.random(10000);
                $('#bidCost').text(rand);
                var BidInfo = {
                    vendorNum: currentVendorNum,
                    cost: rand
                };
                //send to vendor page
                socket.emit('au_BID', JSON.stringify(BidInfo));
                hasBid =true;
            }

        }
        else {
            alert('抽奖尚未开始！');
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
      $('#username').val('提供商编号： ' + vendorNum);
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

var gcode;
var _viewer;
var modelOffset = null;

var timer = null;
var gCodePoints = null;//= JSON.parse(gcode).gcode;

var lasPT= null;
var firstPT = false;
var gCodeIndex = 0;

var material = new THREE.LineBasicMaterial({ color: 0xff0000 });


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

            _viewer = viewerApp.myCurrentViewer;
            modelOffset = _viewer.model.getData().globalOffset;
            startCNC();
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

    timer = setInterval(drawLine, 100);
}
