var express =require ('express') ;
var bodyParser =require ('body-parser') ;
var fs =require ('fs') ;
var path =require ('path') ;
var multer = require('multer');


var router =express.Router () ;
router.use (bodyParser.json ()) ;



var config = require('./config-view-and-data.js');
var Lmv = require('./view-and-data.js');

var lmv = new Lmv(config);
var modelsFolder = './model-upload-to-Forge/';
//var translateJobs = './translate-jobs/';
var translateJobs =modelsFolder;


var uploadFromFusion_Done = false;

router.get('/startTrans/:filename', function (req, res) {
    var filename =req.params.filename ;

    createBucketAndUpload(filename);

    res.end('ok');
});

router.use(multer({
    dest: modelsFolder,
    rename: function (fieldname, filename) {
        return filename.toLowerCase().replace(/[^0-9a-z-]/g,'');
    },
    onFileUploadStart: function (file) {
        console.log('onFileUploadStart');
        uploadFromFusion_Done = false;
    },
    onFileUploadComplete: function (file) {
        console.log(file.fieldname + ' uploaded to ' + file.path)
        console.log('onFileUploadComplete');
        uploadFromFusion_Done = true;

        //start to upload to Forge to translate
        //createBucketAndUpload(file.fieldname);
    }
}));

function storeJobStatus(jobId, status) {

    console.log('[Store Trans Status] ' + jobId + ' status:' + status);

    fs.writeFile(translateJobs + jobId + '.json', status,
        function (err) {
            if (err) {
                console.log('[Store Trans Status Error] ' + jobId + ' ' + err);
            }else {
                console.log('[Store Trans Status Succeeded] ' + jobId );
            }
        }
    );
}

router.post('/uploadfusionfile', function (req, res) {

    //var jobId = req.body.uuid.toLowerCase().replace(/[^0-9a-z-]/g,'')+'.step';
    var jobId = req.body.uuid.toLowerCase();

    var jobStatus = {jobId:jobId,
        filename:jobId,
        uploadprogress:0,
        translatingprogress: '%0',
        urn: '' };
    storeJobStatus(jobId, JSON.stringify(jobStatus));


    var emitstr = JSON.stringify({filename:jobId,
                               part_number:req.body.part_number,
                               part_count:req.body.part_count,
                               material_type:req.body.material_type,
                               snapshot:req.body.snapshot});

    if (uploadFromFusion_Done) {
        console.log('[Upload File From Fusion Done]');
       createBucketAndUpload(jobId);
        res.end('ok');
       req.app.io.emit('au_one_more_model',emitstr );
    }
});


router.get('/checkTransStatus/:filename', function (req, res) {

    var filename =req.params.filename ;
    console.log('[Check Trans Status]' + filename);

    if (filename) {
        fs.readFile(translateJobs + filename + '.json', function(err, blob){
            if (err) {
                console.log('[Check Trans Status] ' + filename + err);
                res.end();
            } else {
                console.log('[Check Trans Status]' + filename + ' ' + blob);
                res.send(blob);
            }
        });
    }
});

router.get('/downloadfusionfile/:filename', function (req, res) {
    console.log('[Download Fusion File: ' + req.params.filename );
    res.download(modelsFolder  + req.params.filename,req.params.filename );
}) ;


router.post('/uploadcncfile', function (req, res) {
    var jobId = req.body.uuid.toLowerCase();
    console.log(jobId);
    if (uploadFromFusion_Done) {
        res.end('ok');
     }
});

router.get('/cncdata/:filename', function (req, res) {

    var filename =req.params.filename ;
    console.log('[Get CNC DATA]' + filename);

    // <uuid>.json
    if (filename) {
        fs.readFile(modelsFolder + filename, function(err, blob){
            if (err) {
                console.log('[Get CNC DATA] ' + filename + err);
                res.end();
            } else {
                console.log('[Get CNC DATA]' + filename + ' ' );
                res.send(blob);
            }
        });
    }
});

//LMV workflow
router.get ('/gettoken', function (req, res) {

    console.log('[Get Forge Token]');
    lmv.getToken().then(
        function(response){
            console.log(response.access_token);
            res.send (response) ;
        },
        function(error){
            res.send ({'err':'failed!'}) ;
        });
});

function createBucketAndUpload(jobId) {

    var jobStatus = {jobId:jobId,
                    filename:jobId,
                    uploadprogress:0,
                    translatingprogress: '%0',
                    urn: '' };
    storeJobStatus(jobId, JSON.stringify(jobStatus));

    var serverFile =path.normalize (modelsFolder + jobId) ;

    function onError(error) {
        console.log('[Any Error When Tranlating Model on Forge] ' + jobId + ' ' +  error);
        res.send({'err':error});
    }

    function onInitialized(response) {

        var createIfNotExists = true;

        var bucketCreationData = {
            bucketKey: config.defaultBucketKey,
            servicesAllowed: [],
            policy: 'transient'
        };

        lmv.getBucket(config.defaultBucketKey,
            createIfNotExists,
            bucketCreationData).then(
            onBucketCreated,
            onError);
    }

    //bucket retrieved or created successfully
    function onBucketCreated(response) {

        console.log('[Uploading to A360 started...] ' +jobStatus.jobId);

        fs.stat(serverFile, function (err, stats) {
            if (err) {
                console.log('Uploading to A360 failed...' + err);
            }
            var total = stats.size;
            var chunkSize = config.fileResumableChunk * 1024 * 1024;

            if( total >  chunkSize)
            {
                console.log('   Resumable uploading for large file...' +jobStatus.jobId);

                lmv.resumableUpload(serverFile,
                    config.defaultBucketKey,
                    jobStatus.jobId,uploadProgressCallback).then(onResumableUploadCompleted, onError);
            }
            else
            {
                //single uploading
                console.log('   Single uploading for small file...' +jobStatus.jobId);
                lmv.upload(serverFile,
                    config.defaultBucketKey,
                    jobStatus.jobId).then(onSingleUploadCompleted, onError);
            }
        });
    }

    //single upload complete
    function onResumableUploadCompleted(response) {

        for(var index in response)
        {
            if(response[index].objects && response[index].objects[0].id)
            {
                var fileId = response[index].objects[0].id;
                urn = lmv.toBase64(fileId);
                console.log('upload to A360 done: ' +jobStatus.jobId + urn);

                lmv.register(urn, true).then(onRegister, onError);

                break;
            }
        }
    }

    //single upload complete
    function onSingleUploadCompleted(response) {

        var fileId = response.objects[0].id;
        urn = lmv.toBase64(fileId);
        console.log('upload to A360 done: ' + jobStatus.jobId + urn);

        lmv.register(urn, true).then(onRegister, onError);
    }

    //registration complete but may have failed
    //need to check result
    function onRegister(response) {

        if (response.Result === "Success") {

            console.log('Translation requested...' +jobStatus.jobId);
            //set a relative long time (15 minutes)
            lmv.checkTranslationStatus(
                urn, 1000 * 60 * 30, 1000 * 10,
                progressCallback).then(
                onTranslationCompleted,
                onError);

        }
        else {
            console.log(response.Result);
        }

    }

    function uploadProgressCallback(n,nbChunks){
        console.log('[Uploading to Forge] ' + jobStatus.jobId);
    }

    function progressCallback(progress) {
        console.log('[Translation Progress] ' + jobStatus.jobId + ' ' + progress);
        jobStatus.translatingprogress = progress;
        storeJobStatus(jobStatus.jobId, JSON.stringify(jobStatus));
     }

    //file ready for viewing
    function onTranslationCompleted(response) {
        console.log('[Translating Compeleted] URN =  ' + response.urn);

        jobStatus.translatingprogress =  'complete';
        jobStatus.urn =   response.urn;

        storeJobStatus(jobStatus.jobId, JSON.stringify(jobStatus));
    }

    //start the test
    lmv.initialize().then(onInitialized, onError);

}



module.exports =router ;