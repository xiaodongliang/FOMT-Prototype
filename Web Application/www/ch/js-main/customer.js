
var socket = io('http://au-china-forge.herokuapp.com');

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

$(document).ready (function () {

    //check which attendees call this page
    var customerNum = getParameterByNameFromPath('customerNum',window.location.href);
    var customerNum = (customerNum !== '' ? customerNum : 0 );

    if(customerNum > 0){
        //attendees
        $("#useremailimg").attr('src','images/customer.png');
         $('#username').val('需求方编号： ' + customerNum);
    }

    socket.on('au_one_more_model', function(msg){

        var testJson = eval("(" + msg + ")");
        var filename = testJson.filename;
        var filenamewithoutext = filename.substr(0,filename.lastIndexOf('.'));
        var thumbnailBlob = testJson.snapshot;

        var html = '<div class="col-xs-12 col-sm-6 col-lg-8">'
            + '<img src="data:image/jpeg;base64,' + thumbnailBlob +'" width="300" height="300"/>'
            + '<button id="' + filename + '" type="text" class="form-control">' + filename + '</button>'
            + '<br><h3><span class="label label-default">零件编号： ' + testJson.part_number + '</span></h3>   '
            + '<h3><span class="label label-default">数量： ' + testJson.part_count + '</span></h3>   '
            + '<h3><span class="label label-default">材料： ' + testJson.material_type + '</span></h3>   '
             +'<button class="btn btn-large btn-primary" id="btnRFQ-' +filenamewithoutext + '" >检查报价</button>'
            + '</div>';

        var localStgJson = {image:thumbnailBlob,
                             filename:filename,
                             partnum:testJson.part_number,
                             quantity:testJson.part_count ,
                             material:testJson.material_type,
                             urn:''  };

        localStorage["RFQBasicInfo" + filenamewithoutext] = JSON.stringify(localStgJson);

        $('#FusionFileList').append (
            html
        ) ;

        $('#btnRFQ-' + filenamewithoutext).click (function (evt) {

            $.ajax ({
                url: '/ForgeRoute/checkTransStatus/' + filename,
                type: 'get',
                data: null,
                contentType: 'application/json',
                complete: null
            }).done (function (response) {
                if(response.err){
                    $('#msg').text ('[Progress request failed]' + filename + ' ' + response.err) ;
                }
                else {
                    var responsObj = eval('('+response+')');

                    if (responsObj.translatingprogress) {
                        if (responsObj.translatingprogress == 'complete' && responsObj.urn != '') {
                           var stgJson =  JSON.parse(localStorage["RFQBasicInfo" + filenamewithoutext]);
                            stgJson.urn = 'urn:' + responsObj.urn;
                            localStorage["RFQBasicInfo" + filenamewithoutext] = JSON.stringify(stgJson);
                            window.location.href = 'RFQ.html?customerNum=' + customerNum +'&filenamewithoutext=' + filenamewithoutext;
                         }
                        else {
                            alert('正在转化模型！稍后尝试！');
                        }
                    }
                }
            }).fail (function (xhr, ajaxOptions, thrownError) {
                $('#msg').text ('[Progress request failed]' + filename) ;
            }) ;

        }) ;
    });
}) ;

function createBucketAndUpload (data) {

}
