/*
 * upload Form with progress bar
 * requires: 
 *   1.) a div with id "progress-panel" for showing upload bar on submit (start the element as display none)
 *   2.) a "progress" element (must only have one such element) for graphical depiction of progress
 *   3.) an element with id "percentage" for text display of upload progress
 *   4.) URL must use 'POST' method
 * input is the url to call and the formdata (  built using formdata = new FormData($("form")[0]);  )
 */
function uploadFormShowFileProgress(urlstring, formdata) {
    $.ajax({
        url: urlstring,  //Server script to process data
        type: 'POST',
        xhr: function() {  // Custom XMLHttpRequest
            var myXhr = $.ajaxSettings.xhr();
            if(myXhr.upload){ // Check if upload property exists
                myXhr.upload.addEventListener('progress',progressHandlingFunction, false); // For handling the progress of the upload
            }
            return myXhr;
        },
        //Ajax events
        beforeSend: function() {
		$("#progress-panel").show();
	},
        success: function (results, textStatus, jqXHR) {
            console.log(results);
            console.log(textStatus);
            $('progress').attr({value:100,max:100});
            $("#percentage").text(100);
	},
        //error: errorHandler,
        data: formdata,
        cache: false,
        contentType: false,
        processData: false
    });
}

function progressHandlingFunction(e){
    if(e.lengthComputable){
        total = e.total + 100;
        $('progress').attr({value:e.loaded,max:total});
	var percentComplete = e.loaded / total;
        percentComplete = parseInt(percentComplete * 100);
        $("#percentage").text(percentComplete);
    }
}
