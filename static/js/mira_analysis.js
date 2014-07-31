/* MiRA analysis Javascript
 * 
 * Updates fields in form as user changes selections
 */
var currentproj = -1;

$('document').ready(function (ev) {
  loaddataset();
});

$('form select[name=dataset]').change(function (ev) {
  loadmethods();
});

$('form select[name=method]').change(function (ev) {
  loadcategories();
});

function loaddataset() {
    var query = $('select[name=query]');
    var projectID = $("#currentproj").val();
    var activeval = $('select[name=dataset]').val();
    if (projectID) {
        $.ajax({
            type: 'GET',
            url: "/mira/api/ListDatasets/",
            data: "projectID="+projectID+"&format=json",
            dataType: 'json',
            async: false,
            success: function (data) {
                $('select[name=dataset]').empty();
                for (i in data) {
                    $('select[name=dataset]').append("<option value='"+data[i]+"'>"+data[i]+"</option>");
                }
                if (activeval) { $('select[name=dataset] option[value='+activeval+']').attr('selected', 'selected');}
            },
            complete: function() {
                loadmethods();
            },
        });
    }
}

function loadmethods() {
    var query = $('select[name=query]');
    var projectID = $("#currentproj").val();
    var dataset =  $('select[name=dataset]').val();
    var activeval = $('select[name=method]').val();
    if (dataset && projectID) {
        $.ajax({
            type: 'GET',
            url: "/mira/api/ListMethods/",
            data: "projectID="+projectID+"&dataset="+dataset+"&format=json",
            dataType: 'json',
            async: false,
            success: function (data) {
                $('select[name=method]').empty();
                for (i in data) {
                    $('select[name=method]').append("<option value='"+data[i]+"'>"+data[i]+"</option>");
                }
                if (activeval) { $('select[name=method] option[value='+activeval+']').attr('selected', 'selected');}
            },
            complete: function() {
                loadcategories();
            },
        });
    }
}

function loadcategories() {
    var query = $('select[name=query]');
    var projectID = $("#currentproj").val();
    var dataset =  $('select[name=dataset]').val();
    var method =  $('select[name=method]').val();
    var activeval = $('select[name=category]').val();
    if (dataset && projectID && method) {
        $.ajax({
            type: 'GET',
            url: "/mira/api/ListCategories/",
            data: "projectID="+projectID+"&dataset="+dataset+"&method="+method+"&format=json",
            dataType: 'json',
            async: false,
            success: function (data) {
                $('select[name=category]').empty();
                for (i in data) {
                    $('select[name=category]').append("<option value='"+data[i]+"'>"+data[i]+"</option>");
                }
                if (activeval) { $('select[name=category] option[value='+activeval+']').attr('selected', 'selected');}
            },
        });
    }
}
