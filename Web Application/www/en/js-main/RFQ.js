
var socket = io('http://au-china-forge.herokuapp.com');
$(document).ready (function () {

    //loadView('urn:dXJuOmFkc2sub2JqZWN0czpvcy5vYmplY3Q6YWRudGVzdGJ1Y2tldC9lZjIzNGRmOC05YWIwLTExZTYtYWYyMy00MGYwMmY3YWM1MTQuZjNk');

   // return;
    var customerNum = Autodesk.Viewing.Private.getParameterByName('customerNum');
    var customerNum = (customerNum !== '' ? customerNum : 0 );

    var filenamewithoutext = Autodesk.Viewing.Private.getParameterByName('filenamewithoutext');
    var RFQBasic =  JSON.parse(localStorage["RFQBasicInfo" + filenamewithoutext]);



    if(RFQBasic!=null) {

        $("#partimg").attr('src','data:image/jpeg;base64,' + RFQBasic.image);

        $('#filename').text(RFQBasic.filename);
        $('#partnum').text(RFQBasic.partnum);

        $('#downloadfile').text(RFQBasic.filename);

        $('#material').text(RFQBasic.material);
        $('#quantity').text(RFQBasic.quantity)

        loadView(RFQBasic.urn);

        $('#placerfq').click(function(evt){

             var RFGInfo = {
                sendAll:(customerNum == 0 ? true : false),
                vendorNum: parseInt(customerNum) + 1,
                image:RFQBasic.image,
                filename:RFQBasic.filename,
                partnum:RFQBasic.partnum,
                quantity:$('#quantity').text() ,
                material:$('#material').text(),
                urn:RFQBasic.urn,
                desc:$('#desc').val(),
                company:$('#company').val(),
                contact:$('#contact').val(),
                email:$('#email').val(),
                phone:$('#phone').val()
            };

            //send to vendor
             socket.emit('au_RFQ',JSON.stringify(RFGInfo));

        });
        $('#pushcnc').click(function(evt) {
            var filenamewithoutext = RFQBasic.filename.substr(0,RFQBasic.filename.lastIndexOf('.'));
            socket.emit('au_CNC',JSON.stringify({filename:filenamewithoutext+'.json'}));
        });

        if(customerNum ==0 ) {

            $("#bidtable tbody").remove();
            $("#bidtable").append('<tbody></tbody>');

            //watch the bid from vendors
            socket.on('au_BID', function (msg) {

                var bidJson = eval("(" + msg + ")");

                $("#bidtable tbody").append('<tr id="'+ bidJson.vendorNum +'">' +
                                               '<td>Vendor ' + bidJson.vendorNum  + '</td><td>' + bidJson.cost + '</td></tr>');
             });
        }
    }

    //dropdown for material and quantity
    $(".dropdown-menu a").on("click", function(e){
        if(this.parentNode.parentNode.id=='materialDropdown')
        {
            $('#material').text(this.innerText);
        }
        if(this.parentNode.parentNode.id=='quantityDropdown')
        {
            $('#quantity').text(this.innerText);

        }
    });

}) ;

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

$('#downloadfile').click (function (evt) {

    var hf = document.createElement('a');
    hf.id = 'tempwiresult';

    hf.href = 'https://' + window.location.host + '/downloadfusionfile/' + filename;
    hf.download = new Date().toISOString() + msg;
    hf.innerHTML = hf.download;
    document.body.appendChild(hf);
    document.getElementById('tempwiresult').click();
    document.body.removeChild(document.getElementById('tempwiresult'));
}) ;
