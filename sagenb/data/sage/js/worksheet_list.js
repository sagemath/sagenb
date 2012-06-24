/* Javascript for worksheet_list.html
 * 
 * AUTHOR - Samuel Ainsworth (samuel_ainsworth@brown.edu)
 */

// simulated namespace
sagenb.worksheetlistapp = {};

sagenb.worksheetlistapp.list_row = function() {
	var this_row = this;
	
	var $this = null;
	
	// properties object
	this_row.props = null;
	this_row.checked = false;
	this_row.list = null;
	
	this_row.init = function() {
		
	};
	
	this_row.render = function() {
		$("tbody").append('<tr id="row_' + this_row.props.id_number + '">' + 
				'<td class="checkbox_cell"><input type="checkbox"></td>' + 
				'<td class="worksheet_name_cell"></td>' + 
				'<td class="owner_cell"></td>' + 
				'<td class="last_edit_cell"></td>' + 
			'</tr>');
		
		$this = $("#row_" + this_row.props.id_number);
		
		// checkbox
		$this.find("input").change(function(e) {
			this_row.checked = $this.find("input").prop("checked");
		});
		
		// name/running
		var name_html = '<a href="/home/' + sagenb.username + '/' + this_row.props.id_number + '" target="_blank">' + this_row.props.name + '</a>';
		if(this_row.props.running) {
			name_html += '<span class="label label-important pull-right running_label">running</span>';
		}
		$this.find("td.worksheet_name_cell").html(name_html);
		
		// owner/collaborators/published
		var owner_html = this_row.props.owner;
		if(this.props.collaborators && this.props.collaborators.length) {
			// there are collaborators
			owner_html += ' and <a href="#">2 others</a>';
		}
		if(this.props.published_id_number) {
			// it's published
			owner_html += '<span class="published_badge badge badge-info pull-right"><i class="icon-share-alt icon-white"></i></span>';
		}
		$this.find("td.owner_cell").html(owner_html);
		
		// last change
		$this.find("td.last_edit_cell").text(this_row.props.last_change_pretty + " ago");
	};
	
	this_row.remove = function() {
		$this.hide("slow", function() {
			$this.detach();
			delete this_row.list.rows[this_row.props.id_number];
		});
	}
	
	this_row.check = function() {
		this_row.checked = true;
		$this.find("input").prop("checked", true);
	};
	
	this_row.uncheck = function() {
		this_row.checked = false;
		$this.find("input").prop("checked", false);
	};
};

sagenb.worksheetlistapp.worksheet_list = function() {
	var this_list = this;
	
	this_list.rows = [];
	
	this_list.init = function() {
		this_list.show_active();
		
		$("#main_checkbox").change(function(e) {
			if($("#main_checkbox").prop("checked")) {
				// checked -> check all
				this_list.check_all();
			} else {
				// unchecked -> uncheck all
				this_list.check_none();
			}
		});
		
		$("#send_to_archive_button").click(this_list.archive);
		$("#delete_button").click(this_list.delete);
		$("#stop_button").click(this_list.stop);
		$("#download_button").click(this_list.download);
		
		$("#show_active").click(this_list.show_active);
		$("#show_archive").click(this_list.show_archive);
		$("#show_trash").click(this_list.show_trash);
		
		// not going to mess with this for now
		// $("#action_buttons button").addClass("disabled");
	};
	
	///////// FOR EACH ///////////
	this_list.for_each_row = function(f) {
		$.each(this_list.rows, function(i, list_row) {
			if(list_row) f(list_row);
		});
	};
	this_list.for_each_checked_row = function(f) {
		$.each(this_list.rows, function(i, list_row) {
			if(list_row && list_row.checked) f(list_row);
		});
	};
	
	////////// CHECKING //////////
	this_list.check_all = function() {
		this_list.for_each_row(function(list_row) {
			list_row.check();
		});
	};
	this_list.check_none = function() {
		this_list.for_each_row(function(list_row) {
			list_row.uncheck();
		});
	};
	
	/////////// FILENAMES ////////////
	this_list.checked_worksheet_filenames = function() {
		var r = [];
		this_list.for_each_checked_row(function(list_row) {
			r.push(list_row.props.filename);
		});
		return r;
	};
	
	////////// COMMANDS //////////////
	/*this_list.new_worksheet = function() {
		window.open("/new_worksheet");
	};*/
	/*this_list.upload_worksheet = function() {
		// data-toggle takes care of this
	};*/
	/*this_list.download_all_active = function() {
		window.location.replace("/download_worksheets.zip");
	};*/
	
	this_list.checked_action = function(action, extra_callback) {
		// don't do anything if none are selected
		if(this_list.checked_worksheet_filenames().length === 0) return;
		
		var callback = sagenb.generic_callback();
		if(extra_callback) callback = sagenb.generic_callback(extra_callback);
		
		sagenb.async_request(action, callback, {
			filenames: encode_response(this_list.checked_worksheet_filenames())
		});
	}
	this_list.archive = function() {
		this_list.checked_action("/send_to_archive");
	};
	this_list.delete = function() {
		//TODO Are you sure?
		this_list.checked_action("/send_to_trash", function(status, response) {
			this_list.for_each_checked_row(function(row) {
				row.remove();
			});
		});
	};
	this_list.stop = function() {
		this_list.checked_action("/send_to_stop", function(status, response) {
			this_list.for_each_checked_row(function(row) {
				$("#row_" + row.props.id_number + " .running_label").fadeOut('slow', function() {
					$(this).detach();
					row.uncheck();
				});
			});
		});
	};
	this_list.download = function() {
		// don't download if none are selected
		if(this_list.checked_worksheet_filenames().length === 0) return;
		
		window.location.replace("/download_worksheets.zip?filenames=" + encode_response(this_list.checked_worksheet_filenames()));
	};
	
	this_list.clear_list = function() {
		$("table tbody tr").detach();
		this_list.rows = [];
	};
	this_list.load = function(params) {
		var url = "/worksheet_list";
		if(params) url += "?" + encodeURI(params);
		
		this_list.clear_list();
		
		sagenb.async_request(url, sagenb.generic_callback(function(status, response) {
			var X = decode_response(response);
			for(i in X.worksheets) {
				var row = new sagenb.worksheetlistapp.list_row();
				
				row.props = X.worksheets[i];
				row.list = this_list;
				
				this_list.rows[row.props.id_number] = row;
				
				row.render();
			}
			
			if($("table tbody tr").length === 0) {
				// no rows
				$("tbody").append('<tr class="empty_table_row">' + 
					'<td colspan="4">Nothing here!</td>' + 
				'</tr>');
			}
		}));
	};
	
	//// VIEWS ////
	this_list.show_active = function() {
		this_list.load();
		
		$(".title").text("My Notebook");
	};
	this_list.show_archive = function() {
		this_list.load("typ=archive");
		
		$(".title").text("My Notebook - Archive");
	};
	this_list.show_trash = function() {
		this_list.load("typ=trash");
		
		$(".title").text("My Notebook - Trash");
	};
	
};