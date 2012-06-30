/*
 * Javascript functionality for the worksheet page
 * 
 * AUTHOR - Samuel Ainsworth (samuel_ainsworth@brown.edu)
 */

// simulated namespace
sagenb.worksheetapp = {};

/* We may wish to switch our object oriented approach 
away from using functions and instead taking advantage
of prototypes. Supposedly, there may be some memory 
advantages to prototypes over functions but this is not 
clear. I'm not convinced. See

http://stackoverflow.com/questions/1441212/javascript-instance-functions-versus-prototype-functions
http://stackoverflow.com/questions/310870/use-of-prototype-vs-this-in-javascript
http://blogs.msdn.com/b/kristoffer/archive/2007/02/13/javascript-prototype-versus-closure-execution-speed.aspx
http://www.nczonline.net/blog/2009/04/13/computer-science-in-javascript-linked-list/

*/

sagenb.worksheetapp.worksheet = function() {
	/* this allows us to access this cell object from 
	 * inner functions
	 */
	var this_worksheet = this;
	
	/* Array of all of the cells. This is a sparse array because 
	 * cells get deleted etc. Because it is sparse, you have to 
	 * use a conditional when you loop over each element. See
	 * hide_all_output, show_all_output, etc.
	 */
	this_worksheet.cells = [];
	
	// Worksheet information from worksheet.py
	this_worksheet.state_number = -1;
	
	// Current worksheet info, set in notebook.py.
	this_worksheet.filename = "";
	this_worksheet.name = "";
	this_worksheet.owner = "";
	this_worksheet.id = -1;
	this_worksheet.is_published = false;
	this_worksheet.system = "";
	this_worksheet.pretty_print = false;
	
	// sharing
	this_worksheet.collaborators = [];
	this_worksheet.auto_publish = false;
	this_worksheet.published_id_number = -1;
	this_worksheet.published_url = null;
	this_worksheet.published_time = null;
	
	// Ping the server periodically for worksheet updates.
	this_worksheet.server_ping_time = 10000;
	
	// Focus / blur.
	this_worksheet.current_cell_id = -1;
	
	// Single/Multi cell mode
	this_worksheet.single_cell_mode = false;
	
	// Evaluate all
	this_worksheet.is_evaluating_all = false;
	
	
	// other variables go here
	
	///////////// COMMANDS ////////////
	this_worksheet.worksheet_command = function(cmd) {
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
			this_worksheet.state_number = parseInt(this_worksheet.state_number, 10) + 1;
		}
		// worksheet_filename differs from actual url for public interacts
		// users see /home/pub but worksheet_filename is /home/_sage_
		return ('/home/' + this_worksheet.filename + '/' + cmd);
	};
	
	//// MISC ////
	this_worksheet.forEachCell = function(f) {
		/* Execute the given function on all cells in 
		 * this worksheet. This is useful since some values 
		 * in this_worksheet.cells are null.
		 */
		$.each(this_worksheet.cells, function(i, cell) {
			if(cell) f(cell);
		});
	}
	
	///////////////// PINGS //////////////////
	this_worksheet.ping_server = function() {
		/* for some reason pinging doesn't work well.
		 * the callback goes but jQuery throws a 404 error.
		 * this error may not be a bug, not sure...
		 */
		sagenb.async_request(this_worksheet.worksheet_command('alive'), sagenb.generic_callback(function(status, response) {
			/*  Each time the server is up and responds, the server includes
				the worksheet state_number is the response.  If this number is out
				of sync with our view of the worksheet state, then we force a
				refresh of the list of cells.  This is very useful in case the
				user uses the back button and the browser cache displays an
				invalid worksheet list (which can cause massive confusion), or the
				user open the same worksheet in multiple browsers, or multiple
				users open the same shared worksheet.
			*/
			if (this_worksheet.state_number >= 0 && parseInt(response, 10) > this_worksheet.state_number) {
				// Force a refresh of just the cells in the body.
				this_worksheet.worksheet_update();
				this_worksheet.cell_list_update();
			}
		}));
	};
	
	
	
	//////////// FILE MENU TYPE STUFF //////////
	this_worksheet.new_worksheet = function() {
		window.open("/new_worksheet");
	};
	this_worksheet.save = function() {
		sagenb.async_request(this_worksheet.worksheet_command("save_snapshot"), sagenb.generic_callback());
	};
	this_worksheet.close = function() {
		// TODO gettext
		if(this_worksheet.name === "Untitled") {
			$(".alert_rename").show();
		} else {
			// maybe other stuff here??
			
			// this is a hack which gets close working
			window.open('', '_self', '');
			close();
			window.close();
			self.close();
		}
	};
	this_worksheet.print = function() {
		/* here we may want to convert MathJax expressions into
		 * something more readily printable eg images. I think 
		 * there may be some issues with printing using whatever 
		 * we have as default. I haven't seen this issue yet
		 * but it may exist.
		 */
		console.log("my name is " + this_worksheet.name);
		//window.open('/home/');
	};
	
	//////// EXPORT/IMPORT ///////
	this_worksheet.export_worksheet = function() {
		window.open(this_worksheet.worksheet_command("download/" + this_worksheet.name + ".sws"));
	};
	this_worksheet.import_worksheet = function() {
	
	};
	
	////////// INSERT CELL //////////////
	this_worksheet.add_new_cell_button_after = function(obj) {
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
					this_worksheet.new_text_cell_after(after_cell_id);
				} else {
					this_worksheet.new_cell_after(after_cell_id);
				}
			}
			else {
				// this is the first button
				var before_cell_id = toint($(this).next(".cell_wrapper").find(".cell").attr("id").substring(5));
				
				if(event.shiftKey) {
					this_worksheet.new_text_cell_before(before_cell_id);
				} else {
					this_worksheet.new_cell_before(before_cell_id);
				}
			}
		});
	};
	
	////////////// EVALUATION ///////////////
	this_worksheet.evaluate_all = function() {
		this_worksheet.is_evaluating_all = true;
		
		this_worksheet.forEachCell(function(cell) {
			cell.set_output_loading();
		});
		
		var firstcell_id = parseInt($(".cell").attr("id").substring(5));
		this_worksheet.cells[firstcell_id].evaluate();
	};
	this_worksheet.interrupt = function() {
		sagenb.async_request(this_worksheet.worksheet_command('interrupt'), sagenb.generic_callback());
	};
	this_worksheet.restart_sage = function() {
		this_worksheet.forEachCell(function(cell) {
			if(cell.is_evaluating) cell.render_output("");
		});
		sagenb.async_request(this_worksheet.worksheet_command('restart_sage'), sagenb.generic_callback());
	};
	
	//// OUTPUT STUFF ////
	this_worksheet.hide_all_output = function() {
		sagenb.async_request(this_worksheet.worksheet_command('hide_all'), sagenb.generic_callback(function(status, response) {
			this_worksheet.forEachCell(function(cell) {
				cell.set_output_hidden();
			});
		}));
	};
	this_worksheet.show_all_output = function() {
		sagenb.async_request(this_worksheet.worksheet_command('show_all'), sagenb.generic_callback(function(status, response) {
			this_worksheet.forEachCell(function(cell) {
				cell.set_output_visible();
			});
		}));
	};
	this_worksheet.delete_all_output = function() {
		sagenb.async_request(this_worksheet.worksheet_command('delete_all_output'), sagenb.generic_callback(function(status, response) {
			this_worksheet.forEachCell(function(cell) {
				cell.output = "";
				cell.render_output();
			});
		}));
	};
	
	this_worksheet.change_system = function(newsystem) {
		sagenb.async_request(this_worksheet.worksheet_command("system/" + newsystem), sagenb.generic_callback(function(status, response) {
			this_worksheet.system = newsystem;
			
			this_worksheet.forEachCell(function(cell) {
				cell.update_codemirror_mode();
			});
		}));
	};
	this_worksheet.set_pretty_print = function(s) {
		sagenb.async_request(this_worksheet.worksheet_command("pretty_print/" + s), sagenb.generic_callback());
	};
	
	//// NEW CELL /////
	this_worksheet.new_cell_before = function(id) {
		sagenb.async_request(this_worksheet.worksheet_command("new_cell_before"), function(status, response) {
			if(response === "locked") {
				$(".alert_locked").show();
				return;
			}
			
			var X = decode_response(response);
			
			var new_cell = new sagenb.worksheetapp.cell(X.new_id);
			
			var a = $("#cell_" + X.id).parent().prev();
			
			var wrapper = $("<div></div>").addClass("cell_wrapper").insertAfter(a);
			
			new_cell.worksheet = this_worksheet;
			
			new_cell.update(wrapper);
			
			// add the next new cell button
			this_worksheet.add_new_cell_button_after(wrapper);
			
			// wait for the render to finish
			setTimeout(new_cell.focus, 50);
			
			this_worksheet.cells[new_cell.id] = new_cell;
		},
		{
			id: id
		});
	};
	this_worksheet.new_cell_after = function(id) {
		sagenb.async_request(this_worksheet.worksheet_command("new_cell_after"), function(status, response) {
			if(response === "locked") {
				$(".alert_locked").show();
				return;
			}
			
			var X = decode_response(response);
			
			var new_cell = new sagenb.worksheetapp.cell(X.new_id);
			
			var a = $("#cell_" + X.id).parent().next();
			
			var wrapper = $("<div></div>").addClass("cell_wrapper").insertAfter(a);
			
			new_cell.worksheet = this_worksheet;
			
			new_cell.update(wrapper);
			
			// add the next new cell button
			this_worksheet.add_new_cell_button_after(wrapper);
			
			// wait for the render to finish
			setTimeout(new_cell.focus, 50);
			
			this_worksheet.cells[new_cell.id] = new_cell;
		},
		{
			id: id
		});
	};
	
	this_worksheet.new_text_cell_before = function(id) {
		sagenb.async_request(this_worksheet.worksheet_command("new_text_cell_before"), function(status, response) {
			if(response === "locked") {
				$(".alert_locked").show();
				return;
			}
			
			var X = decode_response(response);
			
			var new_cell = new sagenb.worksheetapp.cell(X.new_id);
			
			var a = $("#cell_" + X.id).parent().prev();
			
			var wrapper = $("<div></div>").addClass("cell_wrapper").insertAfter(a);
			
			new_cell.worksheet = this_worksheet;
			
			new_cell.update(wrapper);
			
			// add the next new cell button
			this_worksheet.add_new_cell_button_after(wrapper);
			
			// wait for the render to finish
			setTimeout(new_cell.focus, 50);
			
			this_worksheet.cells[new_cell.id] = new_cell;
		},
		{
			id: id
		});
	};
	this_worksheet.new_text_cell_after = function(id) {
		sagenb.async_request(this_worksheet.worksheet_command("new_text_cell_after"), function(status, response) {
			if(response === "locked") {
				$(".alert_locked").show();
				return;
			}
			
			var X = decode_response(response);
			
			var new_cell = new sagenb.worksheetapp.cell(X.new_id);
			
			var a = $("#cell_" + X.id).parent().next();
			
			var wrapper = $("<div></div>").addClass("cell_wrapper").insertAfter(a);
			
			new_cell.worksheet = this_worksheet;
			
			new_cell.update(wrapper);
			
			// add the next new cell button
			this_worksheet.add_new_cell_button_after(wrapper);
			
			// wait for the render to finish
			setTimeout(new_cell.focus, 50);
			
			this_worksheet.cells[new_cell.id] = new_cell;
		},
		{
			id: id
		});
	};
	
	
	/////////////// WORKSHEET UPDATE //////////////////////
	this_worksheet.worksheet_update = function() {
		sagenb.async_request(this_worksheet.worksheet_command("worksheet_properties"), sagenb.generic_callback(function(status, response) {
			var X = decode_response(response);
			
			this_worksheet.id = X.id_number;
			this_worksheet.name = X.name;
			this_worksheet.owner = X.owner;
			this_worksheet.system = X.system;
			this_worksheet.pretty_print = X.pretty_print;
			
			this_worksheet.collaborators = X.collaborators;
			this_worksheet.auto_publish = X.auto_publish;
			this_worksheet.published_id_number = X.published_id_number;
			if(X.published_url) {
				this_worksheet.published_url = X.published_url;
			}
			if(X.published_time) {
				this_worksheet.published_time = X.published_time;
			}
			
			this_worksheet.running = X.running;
			
			// update the title
			document.title = this_worksheet.name + " - Sage";
			$(".worksheet_name h1").text(this_worksheet.name);
			
			// update the typesetting checkbox
			$("#typesetting_checkbox").prop("checked", this_worksheet.pretty_print);
			
			// set the system select
			$("#system_select").val(this_worksheet.system);
			
			if(this_worksheet.published_id_number !== null && this_worksheet.published_id_number >= 0) {
				$("#publish_checkbox").prop("checked", true);
				$("#auto_republish_checkbox").removeAttr("disabled");
				
				$("#auto_republish_checkbox").prop("checked", this_worksheet.auto_publish);
				
				$("#worksheet_url a").text(this_worksheet.published_url);
				$("#worksheet_url").show();
			} else {
				$("#publish_checkbox").prop("checked", false);
				$("#auto_republish_checkbox").prop("checked", false);
				$("#auto_republish_checkbox").attr("disabled", true);
				
				$("#worksheet_url").hide();
			}
			
			$("#collaborators").val(this_worksheet.collaborators.join(", "));
			
			
			// TODO other stuff goes here, not sure what yet
		}));
	};
	this_worksheet.cell_list_update = function() {
		// load in cells
		sagenb.async_request(this_worksheet.worksheet_command("cell_list"), sagenb.generic_callback(function(status, response) {
			var X = decode_response(response);
			
			// set the state_number
			this_worksheet.state_number = X.state_number;
			
			// remove all previous cells
			$(".cell").detach();
			$(".new_cell_button").detach();
			
			// add the first new cell button
			this_worksheet.add_new_cell_button_after($(".the_page .worksheet_name"));

			// load in cells
			for(i in X.cell_list) {
				// create wrapper
				var wrapper = $("<div></div>").addClass("cell_wrapper").appendTo(".the_page");
				
				var cell_obj = X.cell_list[i];
				
				// create the new cell
				var newcell = new sagenb.worksheetapp.cell(toint(cell_obj.id));
				
				// connect it to this worksheet
				newcell.worksheet = this_worksheet;
				
				// update all of the cell properties and render it into wrapper
				newcell.update(wrapper, true);
				
				// add the next new cell button
				this_worksheet.add_new_cell_button_after(wrapper);
				
				// put the cell in the array
				this_worksheet.cells[cell_obj.id] = newcell;
			}
		}));
	}
	
	
	
	this_worksheet.on_load_done = function() {
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
			
			if($.inArray("single_cell", splithash) >= 0) {
				// #single_cell is in hash
				// TODO
			}
			
			$.each(splithash, function(i, e) {
				if(e.substring(0, 4) === "cell") {
					$('html, body').animate({
						// -40 for navbar and -20 extra
						scrollTop: $("#cell_" + e.substring(4)).offset().top - 60
					}, "slow");
					
					// break each loop
					return false;
				}
			});
		}
		
		sagenb.done_loading();
	}
	
	
	//////////////// INITIALIZATION ////////////////////
	this_worksheet.init = function() {
		// show the spinner
		sagenb.start_loading();
		
		// do the actual load
		this_worksheet.worksheet_update();
		
		this_worksheet.cell_list_update();
		
		/////////// setup up the title stuff ////////////
		$(".worksheet_name").click(function(e) {
			if(!$(".worksheet_name").hasClass("edit")) {
				$(".worksheet_name input").val(this_worksheet.name);
				$(".worksheet_name").addClass("edit");
				$(".worksheet_name input").focus();
			}
		});
		
		// this is the event handler for the input
		var worksheet_name_input_handler = function(e) {
			$(".worksheet_name").removeClass("edit");
			
			if(this_worksheet.name !== $(".worksheet_name input").val()) {
				// send to the server
				sagenb.async_request(this_worksheet.worksheet_command("rename"), sagenb.generic_callback(function(status, response) {
					// update the title when we get good response
					this_worksheet.worksheet_update();
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
			this_worksheet.set_pretty_print($("#typesetting_checkbox").prop("checked"));
			
			// update
			this_worksheet.worksheet_update();
		});
		
		////////// LINE NUMBERS CHECKBOX //////////
		$("#line_numbers_checkbox").change(function(e) {
			this_worksheet.forEachCell(function(cell) {
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
		$(".alert_rename .cancel").click(window.close);
		
		///////// LOCKED ALERT //////////
		$(".alert_locked button").click(function(e) {
			$(".alert_locked").hide();
		});
		
		/////// CHANGE SYSTEM DIALOG //////////
		$("#system_modal .btn-primary").click(function(e) {
			this_worksheet.change_system($("#system_select").val());
		});
		
		
		//////// SHARING DIALOG ///////////
		$("#sharing_dialog .btn-primary").click(function(e) {
			sagenb.async_request(this_worksheet.worksheet_command("invite_collab"), sagenb.generic_callback(), {
				collaborators: $("#collaborators").val()
			});
		});
		$("#publish_checkbox").change(function(e) {
			var command;
			if($("#publish_checkbox").prop("checked")) {
				command = this_worksheet.worksheet_command("publish?yes");
			} else {
				command = this_worksheet.worksheet_command("publish?stop");
			}
			
			sagenb.async_request(command, sagenb.generic_callback(function(status, response) {
				this_worksheet.worksheet_update();
			}));
		});
		$("#auto_republish_checkbox").change(function(e) {
			// for some reason, auto is a toggle command
			sagenb.async_request(this_worksheet.worksheet_command("publish?auto"), sagenb.generic_callback(function(status, response) {
				this_worksheet.worksheet_update();
			}));
		});
		
		
		// start the ping interval
		this_worksheet.ping_interval_id = window.setInterval(this_worksheet.ping_server, this_worksheet.server_ping_time);
		
		// set up codemirror autocomplete
		// TODO set up autocomplete
		/*CodeMirror.commands.autocomplete = function(cm) {
			CodeMirror.simpleHint(cm, CodeMirror.javascriptHint);
		};*/
		
		
		var load_done_interval = setInterval(function() {
			/* because the cells array is sparse we need this.
			 * it may be easier/faster to use $.grep either way...
			 */
			var numcells = 0;
			
			this_worksheet.forEachCell(function(cell) {
				numcells++;
			});
			
			if(numcells > 0 && numcells === $(".cell").length) {
				this_worksheet.on_load_done();
				clearInterval(load_done_interval);
			}
		},
			1000
		);
		
		// load js-hotkeys
		/* notes on hotkeys: these don't work on all browsers consistently
		but they are included in the best case scenario that they are all 
		accepted. I have not checked all of the official hotkeys for Sage NB
		so this list may not be complete but will be updated later. */
		$(document).bind("keydown", sagenb.ctrlkey + "+N", function(evt) { this_worksheet.new_worksheet(); return false; });
		$(document).bind("keydown", sagenb.ctrlkey + "+S", function(evt) { this_worksheet.save(); return false; });
		$(document).bind("keydown", sagenb.ctrlkey + "+W", function(evt) { this_worksheet.close(); return false; });
		$(document).bind("keydown", sagenb.ctrlkey + "+P", function(evt) { this_worksheet.print(); return false; });
		
		
		// bind buttons to functions
		
		/////// FILE MENU ////////
		$("#new_worksheet").click(this_worksheet.new_worksheet);
		$("#save_worksheet").click(this_worksheet.save);
		$("#close_worksheet").click(this_worksheet.close);
		$("#export_to_file").click(this_worksheet.export_worksheet);
		// $("#import_from_file").click(this_worksheet.import_worksheet);
		$("#print").click(this_worksheet.print);
		
		////// VIEW //////
		
		
		////////// EVALUATION ///////////
		$("#evaluate_all_cells").click(this_worksheet.evaluate_all);
		$("#interrupt").click(this_worksheet.interrupt);
		$("#restart_worksheet").click();
		// change system doesn't require event handler here
		$("#hide_all_output").click(this_worksheet.hide_all_output);
		$("#show_all_output").click(this_worksheet.show_all_output);
		$("#delete_all_output").click(this_worksheet.delete_all_output);
		
		// TODO
	}
};
