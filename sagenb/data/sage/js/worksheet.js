/*
 * Javascript functionality for the worksheet page
 * 
 * AUTHOR - Samuel Ainsworth (samuel_ainsworth@brown.edu)
 */

// simulated namespace
sagenb.worksheetapp = {};

sagenb.worksheetapp.worksheet = function() {
	/* this allows us to access this cell object from 
	 * inner functions
	 */
	var _this = this;
	
	/* Array of all of the cells. This is a sparse array because 
	 * cells get deleted etc. Because it is sparse, you have to 
	 * use a conditional when you loop over each element. See
	 * hide_all_output, show_all_output, etc.
	 */
	_this.cells = {};
	
	// Worksheet information from worksheet.py
	_this.state_number = -1;
	
	// Current worksheet info, set in notebook.py.
	_this.filename = "";
	_this.name = "";
	_this.owner = "";
	_this.id = -1;
	_this.is_published = false;
	_this.system = "";
	_this.pretty_print = false;
	
	// sharing
	_this.collaborators = [];
	_this.auto_publish = false;
	_this.published_id_number = -1;
	_this.published_url = null;
	_this.published_time = null;

	// data
	_this.attached_data_files = [];
	
	// Ping the server periodically for worksheet updates.
	_this.server_ping_time = 10000;
	
	// Focus / blur.
	_this.current_cell_id = -1;
	
	// Evaluate all
	_this.is_evaluating_all = false;
	
	
	// other variables go here
	
	///////////// COMMANDS ////////////
	_this.worksheet_command = function(cmd) {
		/*
		Create a string formatted as a URL to send back to the server and
		execute the given cmd on the current worksheet.

		INPUT:
			cmd -- string
		OUTPUT:
			a string
		*/
		if (cmd === 'eval' 
		|| cmd === 'new_cell_before' 
		|| cmd === 'new_cell_after'
		|| cmd === 'new_text_cell_before'
		|| cmd === 'new_text_cell_after') {
			_this.state_number = parseInt(_this.state_number, 10) + 1;
		}
		// worksheet_filename differs from actual url for public interacts
		// users see /home/pub but worksheet_filename is /home/_sage_
		return ('/home/' + _this.filename + '/' + cmd);
	};
	
	//// MISC ////
	_this.forEachCell = function(f) {
		/* Execute the given function on all cells in 
		 * this worksheet. This is useful since some values 
		 * in _this.cells are null.
		 */
		$.each(_this.cells, function(i, cell) {
			if(cell) f(cell);
		});
	}
	
	///////////////// PINGS //////////////////
	_this.ping_server = function() {
		/* for some reason pinging doesn't work well.
		 * the callback goes but jQuery throws a 404 error.
		 * this error may not be a bug, not sure...
		 */
		sagenb.async_request(_this.worksheet_command('alive'), sagenb.generic_callback(function(status, response) {
			/*  Each time the server is up and responds, the server includes
				the worksheet state_number is the response.  If this number is out
				of sync with our view of the worksheet state, then we force a
				refresh of the list of cells.  This is very useful in case the
				user uses the back button and the browser cache displays an
				invalid worksheet list (which can cause massive confusion), or the
				user open the same worksheet in multiple browsers, or multiple
				users open the same shared worksheet.
			*/
			if (_this.state_number >= 0 && parseInt(response, 10) > _this.state_number) {
				// Force a refresh of just the cells in the body.
				_this.worksheet_update();
				_this.cell_list_update();
			}
		}));
	};
	
	function close_window() {
		// this is a hack which gets close working
		window.open('', '_self', '');
		close();
		window.close();
		self.close();
	}
	
	//////////// FILE MENU TYPE STUFF //////////
	_this.new_worksheet = function() {
		if(_this.published_mode) return;
		window.open("/new_worksheet");
	};
	_this.save = function() {
		if(_this.published_mode) return;
		sagenb.async_request(_this.worksheet_command("save_snapshot"), sagenb.generic_callback());
	};
	_this.close = function() {
		if(_this.name === gettext("Untitled") && !_this.published_mode) {
			$(".alert_rename").show();
		} else {
			// maybe other stuff here??
			close_window();
		}
	};
	_this.print = function() {
		/* here we may want to convert MathJax expressions into
		 * something more readily printable eg images. I think 
		 * there may be some issues with printing using whatever 
		 * we have as default. I haven't seen this issue yet
		 * but it may exist.
		 */
		window.print();
	};
	
	//////// EXPORT/IMPORT ///////
	_this.export_worksheet = function() {
		window.open(_this.worksheet_command("download/" + _this.name + ".sws"));
	};
	_this.import_worksheet = function() {
	
	};
	
	////////// INSERT CELL //////////////
	_this.add_new_cell_button_after = function(obj) {
		/* Add a new cell button after the given
		 * DOM/jQuery object
		 */
		var button = $("<div class=\"new_cell_button\">" + 
							"<div class=\"line\"></div>" + 
						"</div>");
		
		button.insertAfter(obj);
		button.click(function(event) {
			// get the cell above this button in the dom
			// here 'this' references the button that was clicked
			if($(this).prev(".cell_wrapper").find(".cell").length > 0) {
				// this is not the first button
				var after_cell_id = toint($(this).prev(".cell_wrapper").find(".cell").attr("id").substring(5));
				
				if(event.shiftKey) {
					_this.new_text_cell_after(after_cell_id);
				} else {
					_this.new_cell_after(after_cell_id);
				}
			}
			else {
				// this is the first button
				var before_cell_id = toint($(this).next(".cell_wrapper").find(".cell").attr("id").substring(5));
				
				if(event.shiftKey) {
					_this.new_text_cell_before(before_cell_id);
				} else {
					_this.new_cell_before(before_cell_id);
				}
			}
		});
	};
	
	////////////// EVALUATION ///////////////
	_this.evaluate_all = function() {
		if(_this.published_mode) return;
		_this.is_evaluating_all = true;
		
		_this.forEachCell(function(cell) {
			cell.set_output_loading();
		});
		
		var firstcell_id = parseInt($(".cell").attr("id").substring(5));
		_this.cells[firstcell_id].evaluate();
	};
	_this.interrupt = function() {
		if(_this.published_mode) return;
		sagenb.async_request(_this.worksheet_command('interrupt'), sagenb.generic_callback());
	};
	_this.restart_sage = function() {
		if(_this.published_mode) return;
		_this.forEachCell(function(cell) {
			if(cell.is_evaluating) cell.render_output("");
		});
		sagenb.async_request(_this.worksheet_command('restart_sage'), sagenb.generic_callback());
	};
	
	//// OUTPUT STUFF ////
	_this.hide_all_output = function() {
		if(_this.published_mode) return;
		sagenb.async_request(_this.worksheet_command('hide_all'), sagenb.generic_callback(function(status, response) {
			_this.forEachCell(function(cell) {
				cell.set_output_hidden();
			});
		}));
	};
	_this.show_all_output = function() {
		if(_this.published_mode) return;
		sagenb.async_request(_this.worksheet_command('show_all'), sagenb.generic_callback(function(status, response) {
			_this.forEachCell(function(cell) {
				cell.set_output_visible();
			});
		}));
	};
	_this.delete_all_output = function() {
		if(_this.published_mode) return;
		sagenb.async_request(_this.worksheet_command('delete_all_output'), sagenb.generic_callback(function(status, response) {
			_this.forEachCell(function(cell) {
				cell.output = "";
				cell.render_output();
			});
		}));
	};
	
	_this.change_system = function(newsystem) {
		if(_this.published_mode) return;
		sagenb.async_request(_this.worksheet_command("system/" + newsystem), sagenb.generic_callback(function(status, response) {
			_this.system = newsystem;
			
			_this.forEachCell(function(cell) {
				cell.update_codemirror_mode();
			});
		}));
	};
	_this.set_pretty_print = function(s) {
		if(_this.published_mode) return;
		sagenb.async_request(_this.worksheet_command("pretty_print/" + s), sagenb.generic_callback());
	};
	
	//// NEW CELL /////
	_this.new_cell_before = function(id) {
		if(_this.published_mode) return;
		sagenb.async_request(_this.worksheet_command("new_cell_before"), function(status, response) {
			if(response === "locked") {
				$(".alert_locked").show();
				return;
			}
			
			var X = decode_response(response);
			var new_cell = new sagenb.worksheetapp.cell(X.new_id);
			var a = $("#cell_" + X.id).parent().prev();
			var wrapper = $("<div></div>").addClass("cell_wrapper").insertAfter(a);
			new_cell.worksheet = _this;
			new_cell.update(wrapper);
			
			// add the next new cell button
			_this.add_new_cell_button_after(wrapper);
			
			// wait for the render to finish
			setTimeout(new_cell.focus, 50);
			
			_this.cells[new_cell.id] = new_cell;
		},
		{
			id: id
		});
	};
	_this.new_cell_after = function(id) {
		if(_this.published_mode) return;
		sagenb.async_request(_this.worksheet_command("new_cell_after"), function(status, response) {
			if(response === "locked") {
				$(".alert_locked").show();
				return;
			}
			
			var X = decode_response(response);
			var new_cell = new sagenb.worksheetapp.cell(X.new_id);
			var a = $("#cell_" + X.id).parent().next();
			var wrapper = $("<div></div>").addClass("cell_wrapper").insertAfter(a);
			new_cell.worksheet = _this;
			new_cell.update(wrapper);
			
			// add the next new cell button
			_this.add_new_cell_button_after(wrapper);
			
			// wait for the render to finish
			setTimeout(new_cell.focus, 50);
			
			_this.cells[new_cell.id] = new_cell;
		},
		{
			id: id
		});
	};
	
	_this.new_text_cell_before = function(id) {
		if(_this.published_mode) return;
		sagenb.async_request(_this.worksheet_command("new_text_cell_before"), function(status, response) {
			if(response === "locked") {
				$(".alert_locked").show();
				return;
			}
			
			var X = decode_response(response);
			var new_cell = new sagenb.worksheetapp.cell(X.new_id);
			var a = $("#cell_" + X.id).parent().prev();
			var wrapper = $("<div></div>").addClass("cell_wrapper").insertAfter(a);
			new_cell.worksheet = _this;
			new_cell.update(wrapper);
			
			// add the next new cell button
			_this.add_new_cell_button_after(wrapper);
			
			// wait for the render to finish
			setTimeout(new_cell.focus, 50);
			
			_this.cells[new_cell.id] = new_cell;
		},
		{
			id: id
		});
	};
	_this.new_text_cell_after = function(id) {
		if(_this.published_mode) return;
		sagenb.async_request(_this.worksheet_command("new_text_cell_after"), function(status, response) {
			if(response === "locked") {
				$(".alert_locked").show();
				return;
			}
			
			var X = decode_response(response);
			var new_cell = new sagenb.worksheetapp.cell(X.new_id);
			var a = $("#cell_" + X.id).parent().next();
			var wrapper = $("<div></div>").addClass("cell_wrapper").insertAfter(a);
			new_cell.worksheet = _this;
			new_cell.update(wrapper);
			
			// add the next new cell button
			_this.add_new_cell_button_after(wrapper);
			
			// wait for the render to finish
			setTimeout(new_cell.focus, 50);
			
			_this.cells[new_cell.id] = new_cell;
		},
		{
			id: id
		});
	};
	
	
	/////////////// WORKSHEET UPDATE //////////////////////
	_this.worksheet_update = function() {
		sagenb.async_request(_this.worksheet_command("worksheet_properties"), sagenb.generic_callback(function(status, response) {
			var X = decode_response(response);
			
			_this.id = X.id_number;
			_this.name = X.name;
			_this.owner = X.owner;
			_this.system = X.system;
			_this.pretty_print = X.pretty_print;
			_this.collaborators = X.collaborators;
			
			if(X.published) {
				_this.published_url = X.published_url;
				_this.published_time = X.published_time;
				_this.auto_publish = X.auto_publish;
				_this.published_id_number = X.published_id_number;
			}
			else {
				_this.published_url = null;
				_this.published_time = null;
				_this.auto_publish = null;
				_this.published_id_number = null;
			}

			_this.running = X.running;
			
			_this.attached_data_files = X.attached_data_files;

			// update the title
			document.title = _this.name + " - Sage";
			$(".worksheet_name h1").text(_this.name);
			
			// update the typesetting checkbox
			$("#typesetting_checkbox").prop("checked", _this.pretty_print);
			
			// set the system select
			$("#system_select").val(_this.system);
			
			// sharing
			if(_this.published_id_number !== null && _this.published_id_number >= 0) {
				$("#publish_checkbox").prop("checked", true);
				$("#auto_republish_checkbox").removeAttr("disabled");
				
				$("#auto_republish_checkbox").prop("checked", _this.auto_publish);
				
				$("#worksheet_url a").text(_this.published_url);
				$("#worksheet_url").show();
			} else {
				$("#publish_checkbox").prop("checked", false);
				$("#auto_republish_checkbox").prop("checked", false);
				$("#auto_republish_checkbox").attr("disabled", true);
				
				$("#worksheet_url").hide();
			}

			$("#collaborators").val(_this.collaborators.join(", "));
			
			// data
			$("#data_list ul *").detach();
			for(var i in _this.attached_data_files) {
				var datafile = _this.attached_data_files[i];

				$("#data_list ul").append('<li>' + 
												'<a href="#" class="filename">' + datafile + '</a>' + 
												'<div class="btn-group">' + 
													'<a href="#" class="btn btn-mini copy_path_btn" rel="tooltip" title="Get Path"><i class="icon-edit"></i></a>' + 
													'<a href="data/' + datafile + '" class="btn btn-mini download_btn" rel="tooltip" title="Download" target="_blank"><i class="icon-download"></i></a>' + 
													'<a href="#" class="btn btn-mini delete_btn" rel="tooltip" title="Delete"><i class="icon-remove"></i></a>' + 
												'</div>' + 
											'</li>');

				var elem = $("#data_list li").last();

				// cannot access datastore variable in these functions because it will change by the time they are called
				elem.find(".copy_path_btn").click(function(e) {
					window.prompt(gettext("Copy to clipboard: ") + sagenb.ctrlkey + "-C, Enter", "DATA+'" + $(this).parent().prev().text() + "'");
				});
				elem.find(".delete_btn").click(function(e) {
					var fn = $(this).parent().prev().text();
					$(this).parent().parent().fadeOut("slow", function() {
						sagenb.async_request(_this.worksheet_command("delete_datafile"), sagenb.generic_callback(function(status, response) {
							_this.worksheet_update();
						}),
						{
							name: fn
						});
					});
				});
			}
			$("#data_list ul .btn-group a").tooltip();

			if($("#data_list ul li").length === 0) {
				$("#data_list ul").append('<li class="no_data_files"><a href="#" class="filename">No data files</a></li>');
			}
		}));
	};
	_this.cell_list_update = function() {
		// load in cells
		sagenb.async_request(_this.worksheet_command("cell_list"), sagenb.generic_callback(function(status, response) {
			var X = decode_response(response);
			
			// set the state_number
			_this.state_number = X.state_number;
			
			// remove all previous cells
			$(".cell_wrapper").detach();
			$(".new_cell_button").detach();
			
			// add the first new cell button
			_this.add_new_cell_button_after($(".the_page .worksheet_name"));

			// load in cells
			for(i in X.cell_list) {
				// create wrapper
				var wrapper = $("<div></div>").addClass("cell_wrapper").appendTo(".the_page");
				
				var cell_obj = X.cell_list[i];
				
				// create the new cell
				var newcell = new sagenb.worksheetapp.cell(toint(cell_obj.id));
				
				// connect it to this worksheet
				newcell.worksheet = _this;
				
				// update all of the cell properties and render it into wrapper
				newcell.update(wrapper, true);
				
				// add the next new cell button
				_this.add_new_cell_button_after(wrapper);
				
				// put the cell in the array
				_this.cells[cell_obj.id] = newcell;
			}
		}));
	};
	
	
	
	_this.on_load_done = function() {
		/* This is the stuff that gets done
		 * after the entire worksheet and all 
		 * of the cells are loaded into the 
		 * DOM.
		 */
		
		// check for # in url commands
		if(window.location.hash) {
			// there is some #hashanchor at the end of the url
			// #hashtext -> hashtext
			var hash = window.location.hash.substring(1);
			
			// do stuff
			// something like #single_cell#cell8
			var splithash = hash.split("#");
			
			$.each(splithash, function(i, e) {
				if(e.substring(0, 5) === "cell_") {
					$('html, body').animate({
						// -40 for navbar and -20 extra
						scrollTop: $("#" + e).offset().top - 60
					}, "slow");
					
					$("#" + e).addClass("current_cell");
					
					// break each loop
					return false;
				}
			});
			
			if($.inArray("single_cell", splithash) >= 0) {
				// #single_cell is in hash
				$("#single_cell_mode_radio").click();
			}
		}
		
		sagenb.done_loading();
	};
	
	
	//////////////// INITIALIZATION ////////////////////
	_this.init = function() {
		// show the spinner
		sagenb.start_loading();
		
		// do the actual load
		_this.worksheet_update();
		
		_this.cell_list_update();
		
		// published mode
		if(_this.published_mode) {
			$("body").addClass("published_mode");
		}

		/////////// setup up the title stuff ////////////
		if(!_this.published_mode) {
			$(".worksheet_name").click(function(e) {
				if(!$(".worksheet_name").hasClass("edit")) {
					$(".worksheet_name input").val(_this.name);
					$(".worksheet_name").addClass("edit");
					$(".worksheet_name input").focus();
				}
			});
		}
		
		// this is the event handler for the input
		var worksheet_name_input_handler = function(e) {
			$(".worksheet_name").removeClass("edit");
			
			if(_this.name !== $(".worksheet_name input").val()) {
				// send to the server
				sagenb.async_request(_this.worksheet_command("rename"), sagenb.generic_callback(function(status, response) {
					// update the title when we get good response
					_this.worksheet_update();
				}), {
					name: $(".worksheet_name input").val()
				});
			}
		};
		
		$(".worksheet_name input").blur(worksheet_name_input_handler).keypress(function(e) {
			if(e.which === 13) {
				// they hit enter
				worksheet_name_input_handler(e);
			}
		});
		
		////////// TYPESETTING CHECKBOX //////////
		$("#typesetting_checkbox").change(function(e) {
			_this.set_pretty_print($("#typesetting_checkbox").prop("checked"));
			
			// update
			_this.worksheet_update();
		});
		
		////////// SINGLE/MULTI CELL ///////////
		function update_single_cell_controls() {
			var current_index = $(".cell").index($(".current_cell")) + 1;
			var num_of_cells = $(".cell").length;
			
			window.location.hash = "#single_cell#" + $(".current_cell").attr("id");
			
			$(".progress_text").text(current_index + "/" + num_of_cells);
			$(".progress .bar").css("width", current_index / num_of_cells * 100 + "%");
			
			if(current_index / num_of_cells < 0.55) {
				$(".progress_text").css("color", "#222");
			}
			else {
				$(".progress_text").css("color", "#eee");
			}
			
			if(current_index === 1) {
				$("#first_cell, #previous_cell").attr("disabled", "disabled");
			}
			else {
				$("#first_cell, #previous_cell").removeAttr("disabled");
			}
			
			if(current_index === num_of_cells) {
				$("#last_cell, #next_cell").attr("disabled", "disabled");
			}
			else {
				$("#last_cell, #next_cell").removeAttr("disabled");
			}
		}
		
		$("#first_cell").click(function(e) {
			$(".cell").removeClass("current_cell");
			$(".cell").first().addClass("current_cell");
			update_single_cell_controls();
		});
		$("#last_cell").click(function(e) {
			$(".cell").removeClass("current_cell");
			$(".cell").last().addClass("current_cell");
			update_single_cell_controls();
		});
		
		$("#previous_cell").click(function(e) {
			$(".current_cell").removeClass("current_cell").parent().prev().prev().find(".cell").addClass("current_cell");
			update_single_cell_controls();
		});
		$("#next_cell").click(function(e) {
			$(".current_cell").removeClass("current_cell").parent().next().next().find(".cell").addClass("current_cell");
			update_single_cell_controls();
		});
		
		$("[name=cell_mode_radio]").change(function(e) {
			if($("[name=cell_mode_radio]:checked").val() === "single") {
				// single cell mode
				var $current_cell = $(".current_cell");
				if($current_cell.length === 0) {
					$current_cell = $(".cell").first().addClass("current_cell");
				}
				$("body").addClass("single_cell_mode");
				update_single_cell_controls();
			}
			else {
				// multi cell mode
				window.location.hash = "";
				$("body").removeClass("single_cell_mode");
			}
			
			// fix codemirror bug
			_this.forEachCell(function(cell) {
				if(cell.codemirror) {
					cell.codemirror.refresh();
				}
			});
		});
		
		////////// LINE NUMBERS CHECKBOX //////////
		$("#line_numbers_checkbox").change(function(e) {
			_this.forEachCell(function(cell) {
				if(cell.is_evaluate_cell) {
					cell.codemirror.setOption("lineNumbers", $("#line_numbers_checkbox").prop("checked"));
				}
			});
		});
		
		/////// RENAME ALERT //////
		$(".alert_rename .rename").click(function(e) {
			$(".worksheet_name").click();
			$(".alert_rename").hide();
		});
		$(".alert_rename .cancel").click(close_window);
		
		///////// LOCKED ALERT //////////
		$(".alert_locked button").click(function(e) {
			$(".alert_locked").hide();
		});
		
		/////// CHANGE SYSTEM DIALOG //////////
		$("#system_modal .btn-primary").click(function(e) {
			_this.change_system($("#system_select").val());
		});
		
		
		//////// SHARING DIALOG ///////////
		$("#sharing_modal .btn-primary").click(function(e) {
			sagenb.async_request(_this.worksheet_command("invite_collab"), sagenb.generic_callback(), {
				collaborators: $("#collaborators").val()
			});
		});
		$("#publish_checkbox").change(function(e) {
			var command;
			if($("#publish_checkbox").prop("checked")) {
				command = _this.worksheet_command("publish?publish_on");
			} else {
				command = _this.worksheet_command("publish?publish_off");
			}
			
			sagenb.async_request(command, sagenb.generic_callback(function(status, response) {
				_this.worksheet_update();
			}));
		});
		$("#auto_republish_checkbox").change(function(e) {
			var command;
			if($("#auto_republish_checkbox").prop("checked")) {
				command = _this.worksheet_command("publish?auto_on");
			} else {
				command = _this.worksheet_command("publish?auto_off");
			}
			
			// for some reason, auto is a toggle command
			sagenb.async_request(command, sagenb.generic_callback(function(status, response) {
				_this.worksheet_update();
			}));
		});


		///////// DATA DIALOG //////////
		$("#data_modal ul.nav a").click(function(e) {
			setTimeout(function() {
				if($("#data_modal .tab-pane.active").attr("id") !== "manage_tab") {
					$("#data_modal #upload_button").show();
					$("#data_modal #done_button").hide();
				} else {
					$("#data_modal #upload_button").removeClass("disabled").hide();
					$("#data_modal #done_button").show();
					$("#data_modal input").val("");
					_this.worksheet_update();
				}
			}, 50);
		});

		$("#data_modal #upload_button").click(function(e) {
			if($(this).hasClass("disabled")) return;

			var current_tab = $("#data_modal .tab-pane.active").attr("id");
			$(this).addClass("disabled");

			if(current_tab === "upload_data_file_tab") {
				$("body").append('<iframe name="upload_frame" id="upload_frame" />');
				var upload_frame = $("iframe#upload_frame");
				upload_frame.hide();
				$("#upload_data_file_tab form").submit();
				upload_frame.load(function() {
					if($.trim(upload_frame.text()) !== "") {
						alert(upload_frame.text());
					}
					else {
						$("#manage_tab_button").click();
					}
					upload_frame.detach();
				});
			}
			else if(current_tab === "file_from_url_tab") {
				sagenb.async_request(_this.worksheet_command("datafile_from_url"), sagenb.generic_callback(function(status, response) {
					$("#manage_tab_button").click();
				}), {
					url: $("#data_modal #file_from_url_tab input#url").val(),
					name: $("#data_modal #file_from_url_tab input#name").val()
				});
			}
			else if(current_tab === "new_file_tab") {
				sagenb.async_request(_this.worksheet_command("new_datafile"), sagenb.generic_callback(function(status, response) {
					$("#manage_tab_button").click();
				}), {
					"new": $("#data_modal #new_file_tab input#new").val()
				});
			}
		});
		
		// start the ping interval
		_this.ping_interval_id = window.setInterval(_this.ping_server, _this.server_ping_time);
		
		var load_done_interval = setInterval(function() {
			/* because the cells array is sparse we need this.
			 * it may be easier/faster to use $.grep either way...
			 */
			var numcells = 0;
			
			_this.forEachCell(function(cell) {
				numcells++;
			});
			
			if(numcells > 0 && numcells === $(".cell").length) {
				_this.on_load_done();
				clearInterval(load_done_interval);
			}
		},
			1000
		);
		
		// load js-hotkeys
		/* TODO notes on hotkeys: these don't work on all browsers consistently
		but they are included in the best case scenario that they are all 
		accepted. I have not checked all of the official hotkeys for Sage NB
		so this list may not be complete but will be updated later. */
		$(document).bind("keydown", sagenb.ctrlkey + "+N", function(evt) { _this.new_worksheet(); return false; });
		$(document).bind("keydown", sagenb.ctrlkey + "+S", function(evt) { _this.save(); return false; });
		$(document).bind("keydown", sagenb.ctrlkey + "+W", function(evt) { _this.close(); return false; });
		$(document).bind("keydown", sagenb.ctrlkey + "+P", function(evt) { _this.print(); return false; });
				
		/////// FILE MENU ////////
		$("#new_worksheet").click(_this.new_worksheet);
		$("#save_worksheet").click(_this.save);
		$("#close_worksheet").click(_this.close);
		$("#export_to_file").click(_this.export_worksheet);
		// $("#import_from_file").click(_this.import_worksheet);
		$("#print").click(_this.print);
				
		////////// EVALUATION ///////////
		$("#evaluate_all_cells").click(_this.evaluate_all);
		$("#interrupt").click(_this.interrupt);
		$("#restart_worksheet").click();
		// change system doesn't require event handler here
		$("#hide_all_output").click(_this.hide_all_output);
		$("#show_all_output").click(_this.show_all_output);
		$("#delete_all_output").click(_this.delete_all_output);
	};
};