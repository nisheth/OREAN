// gets a parameter from query string by name, returns false if no such string exists
function getQueryVariable(variable)
{
       var query = window.location.search.substring(1);
       var vars = query.split("&");
       for (var i=0;i<vars.length;i++) {
               var pair = vars[i].split("=");
               if(pair[0] == variable){return pair[1];}
       }
       return(false);
}


function PageArchive() {
	var self = this;
	this.accordion = document.getElementById('accordion');
	this.form = null;
	this.data = null
	if (this.accordion) {
		self.form = $(self.accordion).find("form");
	}
	var savePageForm = document.getElementById('savePageForm');
	

	this.save = function(page) {
		if (self.form) {
			var saveValues = {};
			$.each($(self.form).serializeArray(), function(i, field) {
				if (field.name !== "csrfmiddlewaretoken") {
					if(!saveValues.hasOwnProperty(field.name)) {saveValues[field.name] = []}
					saveValues[field.name].push(field.value);
				}
			});
			var saveData = {};
			$.each($(savePageForm).serializeArray(), function(i, field) {
				saveData[field.name] = field.value;
                        });
			saveData["datablob"] = JSON.stringify(saveValues);
                        saveData["url"] = window.location.pathname;
	        	//alert("SAVING TO ARCHIVE!<br>" + JSON.stringify(saveValues));
			$.ajax({
				method: "POST",
				url: $(savePageForm).attr("action"), 
				data: saveData 
			})
			.success(function( msg ) {
				self.writeMessage(msg, 'success')
				$('#pageSaveModal').modal('hide');	
			})
			.error(function(jqXHR, textStatus, errorThrown) {
  				self.writeMessage(jqXHR.responseText, 'danger');
			})
			.always(function() {
                                $('#pageSaveModal').modal('hide');
			});
		} else {
			$('#pageSaveModal').modal('hide');	
			self.writeMessage("No data to save!", 'danger');
		}
	}

	this.fetch = function(data) {
        	var archiveURL = "/archive/fetch/"+data+"/";	
		$.ajax({
			method: "GET",
			url: archiveURL
		})
		.success(function( msg ) {
			self.data = msg;
			self.writeMessage( JSON.stringify(msg), 'success' )
			self.fillForm( msg );
			$(self.form).find('button')[0].click();
			
		})
		.error(function(jqXHR, textStatus, errorThrown) {
                        self.writeMessage(jqXHR.responseText, 'danger');
                });
	}

	this.writeMessage = function(msg, msgtype) {
		msgtype = (typeof msgtype === 'undefined') ? 'info' : msgtype;
		content = "<div class=\"alert alert-" + msgtype + " alert-dismissible text-center\" role=\"alert\"><button type=\"button\" class=\"close\" data-dismiss=\"alert\" aria-label=\"Close\"><span aria-hidden=\"true\">&times;</span></button>" + msg + "</div>";
		$("div.messagebin").prepend(content);	
	}

	this.fillForm = function ( data ) {
		for (var key in data) {
    		// skip loop if the property is from prototype
    			if (!data.hasOwnProperty(key)) continue;
			foundElement = $(self.form).find("[name="+key+"]")[0];
			for (var i = 0; i < data[key].length; i++) {
				var myValue = data[key][i];
				if (foundElement.nodeName==="SELECT") {
					$(foundElement).find("option[value=\""+myValue+ "\"]").attr("selected", "selected");
					//$(foundElement).val(data[key]);
				} else if (foundElement.nodeName==="INPUT") {
					$(foundElement).val(data[key][i]);
				}
			}
			$(foundElement).trigger("change");
		}
	}

}

$(document).ready(function() {
	// setup an archive object
	pageArchive = new PageArchive();

	// save the form when the user clicks
	document.getElementById("submitSavePageButton").onclick = pageArchive.save;

	var archive_id = getQueryVariable("archive_id")
	if ( archive_id ) {
		pageArchive.fetch(archive_id);
	}
	
});

