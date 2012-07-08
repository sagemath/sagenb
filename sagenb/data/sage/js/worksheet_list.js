/* Javascript for worksheet_list.html
 * 
 * AUTHOR - Samuel Ainsworth (samuel_ainsworth@brown.edu)
 */

// simulated namespace
sagenb.worksheetlistapp = {};

sagenb.worksheetlistapp.list_row = function() {
	var _this = this;
	
	var $this = null;
	
	// properties object
	_this.props = null;
	_this.checked = false;
	_this.list = null;
	
	_this.init = function() {
		
	};
	
	_this.render = function() {
		$("tbody").append('<tr id="row_' + _this.props.id_number + '">' + 
				'<td class="checkbox_cell"><input type="checkbox"></td>' + 
				'<td class="worksheet_name_cell"></td>' + 
				'<td class="owner_cell"></td>' + 
				'<td class="last_edit_cell"></td>' + 
			'</tr>');
		
		$this = $("#row_" + _this.props.id_number);
		
		// checkbox
		$this.find("input").change(function(e) {
			_this.checked = $this.find("input").prop("checked");
		});
		
		// name/running
		var name_html = '<a href="/home/' + sagenb.username + '/' + _this.props.id_number + '" target="_blank">' + _this.props.name + '</a>';
		if(_this.props.running) {
			// TODO gettext
			name_html += '<span class="label label-important pull-right running_label">running</span>';
		}
		$this.find("td.worksheet_name_cell").html(name_html);
		
		// owner/collaborators/published
		var owner_html = _this.props.owner;
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
		// TODO gettext
		$this.find("td.last_edit_cell").text(_this.props.last_change_pretty + " ago");
	};
	
	_this.remove = function() {
		$this.hide("slow", function() {
			$this.detach();
			delete _this.list.rows[_this.props.id_number];
		});
	}
	
	_this.check = function() {
		_this.checked = true;
		$this.find("input").prop("checked", true);
	};
	
	_this.uncheck = function() {
		_this.checked = false;
		$this.find("input").prop("checked", false);
	};
};

sagenb.worksheetlistapp.worksheet_list = function() {
	var _this = this;
	
	_this.rows = [];
	
	_this.refresh_interval_id = null;
	_this.refresh_interval = 10 * 1000;
	
	_this.init = function() {
		_this.show_active();
		
		$("#main_checkbox").change(function(e) {
			if($("#main_checkbox").prop("checked")) {
				// checked -> check all
				_this.check_all();
			} else {
				// unchecked -> uncheck all
				_this.check_none();
			}
		});
		
		$("#send_to_archive_button").click(_this.archive);
		$("#delete_button").click(_this.delete);
		$("#stop_button").click(_this.stop);
		$("#download_button").click(_this.download);
		
		$("#show_active").click(_this.show_active);
		$("#show_archive").click(_this.show_archive);
		$("#show_trash").click(_this.show_trash);
		
		$("#submit_search").click(_this.do_search);
		
		// not going to mess with this for now
		// $("#action_buttons button").addClass("disabled");
		
		// Bind hotkeys
		$(document).bind("keydown", sagenb.ctrlkey + "+N", function(evt) { _this.new_worksheet(); return false; });
	};
	
	///////// FOR EACH ///////////
	_this.for_each_row = function(f) {
		$.each(_this.rows, function(i, list_row) {
			if(list_row) f(list_row);
		});
	};
	_this.for_each_checked_row = function(f) {
		$.each(_this.rows, function(i, list_row) {
			if(list_row && list_row.checked) f(list_row);
		});
	};
	
	////////// CHECKING //////////
	_this.check_all = function() {
		_this.for_each_row(function(list_row) {
			list_row.check();
		});
	};
	_this.check_none = function() {
		_this.for_each_row(function(list_row) {
			list_row.uncheck();
		});
	};
	
	/////////// FILENAMES ////////////
	_this.checked_worksheet_filenames = function() {
		var r = [];
		_this.for_each_checked_row(function(list_row) {
			r.push(list_row.props.filename);
		});
		return r;
	};
	
	////////// COMMANDS //////////////
	_this.new_worksheet = function() {
		window.open("/new_worksheet");
	};
	_this.upload_worksheet = function() {
		// TODO
	};
	_this.download_all_active = function() {
		window.location.replace("/download_worksheets.zip");
	};
	
	_this.checked_action = function(action, extra_callback) {
		// don't do anything if none are selected
		if(_this.checked_worksheet_filenames().length === 0) return;
		
		var callback = sagenb.generic_callback();
		if(extra_callback) callback = sagenb.generic_callback(extra_callback);
		
		sagenb.async_request(action, callback, {
			filenames: encode_response(_this.checked_worksheet_filenames())
		});
	}
	_this.archive = function() {
		_this.checked_action("/send_to_archive", function(status, response) {
			_this.for_each_checked_row(function(row) {
				row.remove();
			});
		});
	};
	_this.delete = function() {
		//TODO Are you sure?
		_this.checked_action("/send_to_trash", function(status, response) {
			_this.for_each_checked_row(function(row) {
				row.remove();
			});
		});
	};
	_this.stop = function() {
		_this.checked_action("/send_to_stop", function(status, response) {
			_this.for_each_checked_row(function(row) {
				$("#row_" + row.props.id_number + " .running_label").fadeOut('slow', function() {
					$(this).detach();
					row.uncheck();
				});
			});
		});
	};
	_this.download = function() {
		// don't download if none are selected
		if(_this.checked_worksheet_filenames().length === 0) return;
		
		window.location.replace("/download_worksheets.zip?filenames=" + encode_response(_this.checked_worksheet_filenames()));
	};
	
	_this.clear_list = function() {
		$("table tbody tr").detach();
		_this.rows = [];
	};
	_this.load = function(params) {
		var url = "/worksheet_list";
		if(params) {
			url += "?" + encodeURI(params);
		}
		
		sagenb.async_request(url, sagenb.generic_callback(function(status, response) {
			_this.clear_list();
			
			var X = decode_response(response);
			for(i in X.worksheets) {
				var row = new sagenb.worksheetlistapp.list_row();
				
				row.props = X.worksheets[i];
				row.list = _this;
				
				_this.rows[row.props.id_number] = row;
				
				row.render();
			}
			
			if($("table tbody tr").length === 0) {
				// no rows
				$("tbody").append('<tr class="empty_table_row">' + 
				// TODO gettext
					'<td colspan="4">Nothing here!</td>' + 
				'</tr>');
			}
			
			// Set up refresh_interval
			clearInterval(_this.refresh_interval_id)
			_this.refresh_interval_id = setInterval(function() {
				_this.load(params);
			}, _this.refresh_interval);
		}));
	};
	
	//// VIEWS ////
	_this.show_active = function() {
		_this.load();
		
		// TODO gettext
		$(".title").text("My Notebook");
		document.title = "My Notebook - Sage";
		$("#search_input").val("");
	};
	_this.show_archive = function() {
		_this.load("type=archive");
		
		// TODO gettext
		$(".title").text("My Notebook - Archive");
		document.title = "My Notebook - Archive - Sage";
		$("#search_input").val("");
	};
	_this.show_trash = function() {
		_this.load("type=trash");
		
		// TODO gettext
		$(".title").text("My Notebook - Trash");
		document.title = "My Notebook - Trash - Sage";
		$("#search_input").val("");
	};
	_this.do_search = function() {
		var q = $("#search_input").val();
		if($.trim(q) === "") return;
		
		$("#type_buttons button").removeClass("active");
		
		_this.load("search=" + q);
		
		// TODO gettext
		document.title = "My Notebook - Search - Sage";
		$(".title").text("My Notebook - Search");
	}
};