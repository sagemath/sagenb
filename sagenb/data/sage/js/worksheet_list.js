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
		
		$this.find("input").change(function(e) {
			this_row.checked = $this.find("input").prop("checked");
		});
		
		$this.find("td.worksheet_name_cell").html('<a href="/home/' + sagenb.username + '/' + this_row.props.id_number + '">' + this_row.props.name + '</a>');
		
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
		
		
	};
	
	this_row.remove = function() {
		// TODO remove DOM
		$this.slideUp("slow", function() {
			$this.detach();
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
	
	// TODO get rid of this, use json array instead
	var SEP = '___S_A_G_E___';
	
	this_list.init = function() {
		this_list.load();
		
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
		
	};
	
	///////// FOR EACH ///////////
	this_list.for_each_listing = function(f) {
		$.each(this_list.rows, function(i, list_row) {
			if(list_row) f(list_row);
		});
	};
	this_list.for_each_checked_listing = function(f) {
		$.each(this_list.rows, function(i, list_row) {
			if(list_row && list_row.checked) f(list_row);
		});
	};
	
	////////// CHECKING //////////
	this_list.check_all = function() {
		this_list.for_each_listing(function(list_row) {
			list_row.check();
		});
	};
	this_list.check_none = function() {
		this_list.for_each_listing(function(list_row) {
			list_row.uncheck();
		});
	};
	
	/////////// FILENAMES ////////////
	this_list.checked_worksheet_filenames = function() {
		var r = [];
		this_list.for_each_checked_listing(function(list_row) {
			r.push(list_row.props.filename);
		});
		return r;
	};
	
	////////// COMMANDS //////////////
	this_list.new_worksheet = function() {
		window.open("/new_worksheet");
	};
	/*this_list.upload_worksheet = function() {
		
	};*/
	this_list.download_all_active = function() {
		
	};
	
	this_list.checked_action = function(action) {
		alert(this_list.checked_worksheet_filenames());
		sagenb.async_request(action, sagenb.generic_callback(), {
			"filenames": this_list.checked_worksheet_filenames(),
			"sep": SEP
		});
	}
	this_list.archive = function() {
		this_list.checked_action("/send_to_archive");
	};
	this_list.delete = function() {
		this_list.checked_action("/send_to_trash");
	};
	this_list.stop = function() {
		this_list.checked_action("/send_to_stop");
	};
	this_list.download = function() {
		window.location.replace("/download_worksheets?filenames=" + this_list.checked_worksheet_filenames() + "&sep=" + SEP);
	};
	
	this_list.clear_list = function() {
		$("table tbody tr").detach();
	};
	this_list.load = function() {
		this_list.clear_list();
		
		sagenb.async_request("/worksheet_list", sagenb.generic_callback(function(status, response) {
			var X = decode_response(response);
			for(i in X.worksheets) {
				var row = new sagenb.worksheetlistapp.list_row();
				
				row.props = X.worksheets[i];
				row.list = this_list;
				
				this_list.rows[row.props.id_number] = row;
				
				row.render();
			}
		}));
	};
};