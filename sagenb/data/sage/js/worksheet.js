/*
 * Javascript functionality for the worksheet layout
 * 
 * AUTHOR - Samuel Ainsworth
 */

// simulated namespace
var worksheetapp = {};

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

/* At some point we may want to switch away from the 
 * current call/response system and instead use 
 * WebSockets.
 */

/* swap control/command on mac operating system */
var ctrlkey = "Ctrl";
if(navigator.userAgent.indexOf("Mac") !== -1) {
	ctrlkey = "Cmd";
}

// the cell object
worksheetapp.cell = function(id) {
	/* this allows us to access this cell object from 
	 * inner functions
	 */
	var this_cell = this;
	
	this_cell.id = id;
	this_cell.input = "";
	this_cell.output = "";
	
	this_cell.is_evalute_cell = true;
	
	this_cell.codemirror = null;
	this_cell.tinymce = null;
	
	this_cell.worksheet = null;
	
	
	// this is the id of the interval for checking for new output
	this_cell.output_check_interval_id;
	
	// the amount of time in millisecs between update checks
	this_cell.output_check_interval = 500;
	
	
	
	
	this_cell.render = function(container) {
		if(this_cell.is_evaluate_cell) {
			// its an evaluate cell
		
			// render into the container
			$(container).html("<div class=\"cell\" id=\"cell_" + this_cell.id + "\">\
								<div class=\"input_cell\">\
								</div>\
							</div> <!-- /cell -->");
			
			//set up extraKeys object
			/* because of some codemirror or chrome bug, we have to
			 * use = new Object(); instead of = {}; When we use = {};
			 * all of the key events are automatically passed to codemirror.
			 */
			var extrakeys = new Object();
			
			// set up autocomplete. we may want to use tab
			//extrakeys[ctrlkey + "-Space"] = "autocomplete";
			
			// backspace handler
			extrakeys["Backspace"] = function(cm) {
				// check if it is empty
				// TODO: checking if it's the last cell should maybe be done by the nb
			
				// all of this is disabled for now
				//if(cm.getValue() === "" && $(".cell").length > 1) {
				if(false) {
					// it's empty and not the only one -> delete it
					//deleteCell(id);
				
					/* TODO: now we should focus on the cell above instead of 
					blurring everything and setting this back to -1 */
					focused_texarea_id = -1;
				} else {
					// not empty -> pass to the default behaviour
					throw CodeMirror.Pass;
				}
			};
			
			extrakeys["Shift-Enter"] = function(cm) {
				this_cell.evaluate();
			};
			
			extrakeys[ctrlkey + "-N"] = function(cm) {
				this_cell.worksheet.new_worksheet();
			};
			extrakeys[ctrlkey + "-S"] = function(cm) {
				this_cell.worksheet.save();
			};
			extrakeys[ctrlkey + "-W"] = function(cm) {
				this_cell.worksheet.close();
			};
			extrakeys[ctrlkey + "-P"] = function(cm) {
				this_cell.worksheet.print();
			};
			
			extrakeys["F1"] = function() {
				this_cell.worksheet.open_help();
			};
			
			//extrakeys["fallthrough"] = "default";
			
			// create the codemirror
			this_cell.codemirror = CodeMirror($(container).find(".input_cell")[0], {
				value: this_cell.input,
				
				/* some of these may need to be settings */
				indentWithTabs: true,
				tabSize: 2,
				lineNumbers: false,
				matchBrackets: true,
				
				/* autofocus messes up when true */
				autofocus: false,
			
				onFocus: function() {
					// may need to make async_request here
					this_cell.worksheet.current_cell_id = this_cell.id;
				},
				onBlur: function() {
					this_cell.worksheet.current_cell_id = -1;
					if(this_cell.input !== this_cell.codemirror.getValue()) {
						// the input has changed since the user focused
						// so we send it back to the server
						this_cell.send_input();
					}
				},
			
				extraKeys: extrakeys
			});
			
			/* we may want to focus this cell here */
			
			// render the output
			this_cell.render_output();
		}
		else {
			// its a text cell
			// TODO
			$(container).html("text cell");
		}
	};
	
	////// FOCUS/BLUR ///////
	// not sure if we even need these methods
	this_cell.focus = function() {
		if(this_cell.is_evaluate_cell) {
			this_cell.codemirror.focus();
		}
		else {
			// do whatever for tinymce
		}
	};
	this_cell.blur = function() {
		// codemirror doesn't have blur
	};
	this_cell.is_focused = function() {
		return this_cell.worksheet.current_cell_id === this_cell.id;
	};
	
	this_cell.send_input = function() {
		// mark the cell as changed
		$("#cell_" + this_cell.id).addClass("input_changed");
		
		// update the local input property
		this_cell.input = this_cell.codemirror.getValue();
		
		// update the server input property
		async_request(this_cell.worksheet.worksheet_command("eval"), this_cell.worksheet.generic_callback, {
			save_only: 1,
			id: this_cell.id,
			input: this_cell.input
		});
	};
	this_cell.evaluate = function() {		
		//alert("eval" + this_cell.id);
		async_request(this_cell.worksheet.worksheet_command("eval"), this_cell.worksheet.generic_callback(function(status, response) {
			/* EVALUATION CALLBACK */
		
			var X = decode_response(response);
			
			// figure out whether or not we are interacting
			// seems like this is redundant
			X.interact = X.interact ? true : false;
			
			if (X.id !== this_cell.id) {
				// Something went wrong, e.g., cell id's don't match
				return;
			}

			if (X.command && (X.command.slice(0, 5) === 'error')) {
				// TODO: use a bootstrap error message
				// console.log(X, X.id, X.command, X.message);
				return;
			}
			
			// not sure about these commands
			/*if (X.command === 'insert_cell') {
				// Insert a new cell after the evaluated cell.
				//do_insert_new_cell_after(X.id, X.new_cell_id, X.new_cell_html);
				//jump_to_cell(X.new_cell_id, 0);
			} else if (X.command === 'introspect') {
				//introspect[X.id].loaded = false;
				//update_introspection_text(X.id, 'loading...');
			} else if (in_slide_mode || doing_split_eval || is_interacting_cell(X.id)) {
				// Don't jump.
			} else {
				// "Plain" evaluation.  Jump to a later cell.
				//go_next(false, true);
			}*/
			
			// start checking for output
			this_cell.check_for_output();
		}),
		
		/* REQUEST OPTIONS */
		{
			// 0 = false, 1 = true this needs some conditional
			newcell: 0,
			
			id: toint(this_cell.id),
			
			/* it's necessary to get the codemirror value because the user
			 * may have made changes and not blurred the codemirror so the 
			 * changes haven't been put in this_cell.input
			 */
			input: this_cell.codemirror.getValue()
		});
		
		// mark the cell as running
		$("#cell_" + this_cell.id).addClass("running");	
		this_cell.set_output_loading();
	};
	this_cell.check_for_output = function() {
		/* Currently, this function uses a setInterval command
		 * so that the result will be checked every X millisecs.
		 * In the future, we may want to implement an exponential
		 * pause system like the last notebook had.
		 */
		function do_check() {
			async_request(this_cell.worksheet.worksheet_command("cell_update"), this_cell.worksheet.generic_callback(function(status, response) {
				/* we may want to implement an error threshold system for errors 
				like the old notebook had. that would go here */
				
				if(response === "") {
					// empty response, try again after a little bit
					// setTimeout(this_cell.check_for_output, 500);
					return;
				}
				
				var X = decode_response(response);
				
				if(X.status === "e") {
					// there was an error, stop checking
					this_cell.worksheet.show_connection_error();
					this_cell.output_check_interval_id = window.clearInterval(this_cell.output_check_interval_id);
					return;
				}
				
				if(X.status === "d") {
					// evaluation done
					
					// clear checking interval
					this_cell.output_check_interval_id = window.clearInterval(this_cell.output_check_interval_id);
					
					// mark the cell as done
					$("#cell_" + this_cell.id).removeClass("running");	
					
					/* I'm not exactly sure what the interrupted property is for 
					* so I'm not sure that this is necessary 
					*/
					/*
					if(X.interrupted === "restart") {
						// restart_sage()
					}
					else if(X.interrupted === "false") {
						
					}
					else {
						
					}
					*/
					
					if(X.new_input !== "") {
						// update the input
						this_cell.input = X.new_input;
						
						// update codemirror/tinymce
						if(this_cell.is_evaluate_cell) {
							this_cell.codemirror.setValue(this_cell.input);
						} else {
							// tinymce
						}
					}
					
					// update the output
					this_cell.output = X.output;
					
					// render to the DOM
					this_cell.render_output();
				}
			}),
				{
					id: this_cell.id
				}
				
			);
		}
		
		// start checking
		this_cell.output_check_interval_id = window.setInterval(do_check, this_cell.output_check_interval);
	};
	
	this_cell.is_interact_cell = function() {
		
	};
	
	
	/////// OUTPUT ///////
	this_cell.delete_output = function() {
		
	};
	this_cell.hide_output = function() {
		
	};
	this_cell.show_output = function() {
		
	};
	this_cell.output_contain_latex = function() {
		return (this_cell.output.indexOf('<span class="math">') !== -1) ||
			   (this_cell.output.indexOf('<div class="math">') !== -1);
	};
	this_cell.render_output = function() {
		// take the output off the dom
		$("#cell_" + this_cell.id + " .output_cell").detach();
		
		// it may be better to send a no_output value instead here
		if(lstrip(this_cell.output) === "") {
			// if no output then don't do anything else
			return;
		}
		
		if($("#cell_" + this_cell.id + " .output_cell").length < 1) {
			// the .output_cell div needs to be created
			// insert the new output
			$("<div class=\"output_cell\" id=\"output_" + this_cell.id + "\">" + this_cell.output + "</div>").insertAfter("#cell_" + id + " .input_cell");
		}
		
		if(this_cell.output_contain_latex()) {
			/* TODO: it would be better to send some cell property
			 * that describes whether or not the output contains 
			 * latex and drop the whole <span class="math"></span>
			 * nonsense.
			 */
			
			// scrap the span.math or div.math wrapper tags
			var output_cell = $("#cell_" + this_cell.id + " .output_cell");
			output_cell.html("\\[" + output_cell.find(".math").html() + "\\]");
			
			// mathjax the ouput
			MathJax.Hub.Queue(["Typeset", MathJax.Hub, output_cell[0]]);
		}
	};
	this_cell.set_output_loading = function() {
		this_cell.output = "<div class=\"progress progress-striped active\" style=\"width: 25%; margin: 0 auto;\">\
							<div class=\"bar\" style=\"width: 100%;\"></div>\
						</div>";
		this_cell.render_output();
	};
	
	
	/* read the %gap, %sh, etc tag and return string
	null for none defined */
	this_cell.get_system = function() {
		
	};
	this_cell.has_input_hide = function() {
		// connect with Cell.percent_directives
		return this_cell.input.substring(0, 5) === "%hide";
	};
	
	this_cell.remove = function() {
		alert("delete" + this_cell.id);
	};
};

worksheetapp.worksheet = function() {
	/* this allows us to access this cell object from 
	 * inner functions
	 */
	var this_worksheet = this;
	
	this_worksheet.cells = [];
	
	// Worksheet information from worksheet.py
	this_worksheet.locked = false;
	this_worksheet.state_number = -1;
	
	// Current worksheet info, set in notebook.py.
	this_worksheet.filename = "";
	this_worksheet.name = "";
	this_worksheet.username = "";
	this_worksheet.owner = "";
	this_worksheet.id = -1;
	this_worksheet.is_published = false;
	this_worksheet.system = "";
	
	// Ping the server periodically for worksheet updates.
	this_worksheet.server_ping_time = 10000;
	
	// Interact constants.  See interact.py and related files.
	// Present in wrapped output, forces re-evaluation of ambient cell.
	this_worksheet.INTERACT_RESTART = '__SAGE_INTERACT_RESTART__';
	// Delimit updated markup.
	this_worksheet.INTERACT_START = '<?__SAGE__START>';
	this_worksheet.INTERACT_END = '<?__SAGE__END>';
	
	// Focus / blur.
	this_worksheet.current_cell_id = -1;
	
	// Single/Multi cell mode
	this_worksheet.single_cell_mode = false;
	
	// other variables go here
	
	
	///////////////// INSTANTIATE ////////////////
	
	///////////// COMMANDS ////////////
	// this must be defined before it's called
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
	this_worksheet.generic_callback = function(extra_callback) {
		return function(status, response) {
			if(status !== "success") {
				this_worksheet.show_connection_error();
				
				// don't continue to extra_callback
				return;
			} else {
				// status was good, hide alert
				this_worksheet.hide_connection_error();
			}
		
			// call the extra callback if it was given
			if($.isFunction(extra_callback)) {
				extra_callback(status, response);
			}
		}
	};
	
	///////////////// PINGS //////////////////
	this_worksheet.show_connection_error = function() {
		$(".alert_connection").show();
	};
	this_worksheet.hide_connection_error = function() {
		$(".alert_connection").hide();
	};
	this_worksheet.ping_server = function() {
		/* TODO for some reason pinging doesn't work
		 * instead of the callback showing an error
		 * jQuery throws some error
		 */
		async_request(this_worksheet.worksheet_command('alive'), this_worksheet.generic_callback);
	};
	
	
	
	
	
	
	
	//////////// FILE MENU TYPE STUFF //////////
	this_worksheet.new_worksheet = function() {
		
	};
	this_worksheet.save = function() {
		
	};
	this_worksheet.close = function() {
		
	};
	this_worksheet.print = function() {
		
	};
	this_worksheet.open_help = function() {
		
	}
	
	//////// EXPORT/IMPORT ///////
	this_worksheet.export_worksheet = function() {
	
	};
	this_worksheet.import_worksheet = function() {
	
	};
	
	////////// INSERT CELL //////////////
	this_worksheet.add_new_cell_button_after = function(obj) {
		/* Add a new cell button after the given
		 * DOM/jQuery object
		 */
		var button = $("<div class=\"new_cell_button\">\
							<div class=\"line\"></div>\
						</div>");
		
		button.insertAfter(obj);
		button.click(function(event) {
			/* BUTTON EVENT HANDLER */
			
			// TODO
			
			// get the cell above this button in the dom
			// here 'this' references the button that was clicked
			var after_cell_id = $(this).prev(".cell_wrapper").find(".cell").attr("id").substring(5);
			
			alert("new cell" + after_cell_id);
		});
	};
	
	////////////// EVALUATION ///////////////
	this_worksheet.evaluate_all = function() {
		for(cellid in cells) {
			cells[cellid].evaluate();
		}
	};
	this_worksheet.interrupt = function() {
		
	};
	
	//// OUTPUT STUFF ////
	this_worksheet.hide_all_output = function() {
		for(cellid in cells) {
			cells[cellid].hide_output();
		}
	};
	this_worksheet.show_all_output = function() {
		for(cellid in cells) {
			cells[cellid].show_output();
		}
	};
	this_worksheet.delete_all_output = function() {
		for(cellid in cells) {
			cells[cellid].delete_output();
		}
	};
	
	this_worksheet.change_system = function(newsystem) {
		
	};
	this_worksheet.set_pretty_print = function(s) {
		
	};
	
	//// NEW CELL /////
	this_worksheet.new_cell_before = function(id) {
		
	};
	this_worksheet.new_after_before = function(id) {
		
	};
	
	
	/////////////// WORKSHEET UPDATE //////////////////////
	this_worksheet.worksheet_update = function() {
		async_request(this_worksheet.worksheet_command("worksheet_properties_json"), this_worksheet.generic_callback(function(status, response) {
			var X = decode_response(response);
			
			this_worksheet.id = X.id_number;
			this_worksheet.name = X.name;
			this_worksheet.owner = X.owner;
			this_worksheet.system = X.system;
			
			// update the title
			document.title = this_worksheet.name + " - Sage";
			$(".worksheet_name h1").text(this_worksheet.name);
			
			// TODO other stuff goes here, not sure what yet
		}));
	};
	this_worksheet.cell_list_update = function() {
		// load in cells
		async_request(this_worksheet.worksheet_command("cell_list_json"), this_worksheet.generic_callback(function(status, response) {
			var X = decode_response(response);
			
			// set the state_number
			this_worksheet.state_number = X.state_number;
			
			// remove all previous cells
			$(".cell").detach();
			$(".new_cell_button").detach();
			
			// add the first new cell button
			this_worksheet.add_new_cell_button_after($(".the_page .worksheet_name"));
			
			// set up temporary rendering area
			//var renderarea = $("<div></div>").appendTo(".the_page");
			
			// load in cells
			for(i in X.cell_list) {
				// create wrapper
				var wrapper = $("<div></div>").appendTo(".the_page");
				wrapper.addClass("cell_wrapper");
				
				var cell_obj = X.cell_list[i];
				
				// create the new cell
				var newcell = new worksheetapp.cell(cell_obj.id);
				
				// set up all of the parameters
				newcell.input = cell_obj.input;
				newcell.output = cell_obj.output;
				newcell.is_evaluate_cell = (cell_obj.type === "evaluate") ? true : false;
				
				// connect it to this worksheet
				newcell.worksheet = this_worksheet;
				
				// render it to the renderarea div
				newcell.render(wrapper);
				
				if(wrapper.html() === "") alert(cell_obj);
				
				// move it out of the renderarea and into the page
				//var cell_dom = renderarea.find("div.cell");
				//cell_dom.appendTo(".the_page");
				
				// add the next new cell button
				this_worksheet.add_new_cell_button_after(wrapper);
				
				// put the cell in the array
				this_worksheet.cells[cell_obj.id] = newcell;
			}
			
			// remove the renderarea
			//renderarea.detach();
		}));
	}
	
	
	
	
	
	
	//////////////// INITIALIZATION ////////////////////
	this_worksheet.init = function() {
		// do the actual load
		this_worksheet.worksheet_update();
		
		this_worksheet.cell_list_update();
		
		// setup up the title stuff
		$(".worksheet_name").click(function(e) {
			$(".worksheet_name input").val(this_worksheet.name);
			$(".worksheet_name").addClass("edit");
			$(".worksheet_name input").focus();
		});
		
		
		var worksheet_name_input_handler = function(e) {
			$(".worksheet_name").removeClass("edit");
			
			if(this_worksheet.name !== $(".worksheet_name input").val()) {
				// send to the server
				async_request(this_worksheet.worksheet_command("rename"), this_worksheet.generic_callback(function(status, response) {
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
		
		
		// start the ping interval
		this_worksheet.ping_interval_id = window.setInterval(this_worksheet.ping_server, this_worksheet.server_ping_time);
		
		// set up codemirror autocomplete
		// TODO set up autocomplete
		/*CodeMirror.commands.autocomplete = function(cm) {
			CodeMirror.simpleHint(cm, CodeMirror.javascriptHint);
		};*/
		
		
		
		// check for # in url commands
		if(window.location.hash) {
			// there is some #hashanchor at the end of the url
			var hash = window.location.hash.substring(1);
			
			// do stuff
		}
		
		// load js-hotkeys
		/* notes on hotkeys: these don't work on all browsers consistently
		but they are included in the best case scenario that they are all 
		accepted. I have not checked all of the official hotkeys for Sage NB
		so this list may not be complete but will be updated later. */
		$(document).bind("keydown", ctrlkey + "+N", function(evt) { this_worksheet.new_worksheet(); return false; });
		$(document).bind("keydown", ctrlkey + "+S", function(evt) { this_worksheet.save(); return false; });
		$(document).bind("keydown", ctrlkey + "+W", function(evt) { this_worksheet.close(); return false; });
		$(document).bind("keydown", ctrlkey + "+P", function(evt) { this_worksheet.print(); return false; });
		
		$(document).bind("keydown", "F1", function(evt) { this_worksheet.open_help(); return false; });
		
		
		// bind buttons to functions
		
		/////// FILE MENU ////////
		$("#new_worksheet").click(this_worksheet.new_worksheet);
		$("#save_worksheet").click(this_worksheet.save);
		$("#close_worksheet").click(this_worksheet.close);
		$("#export_to_file").click(this_worksheet.export_worksheet);
		$("#import_from_file").click(this_worksheet.import_worksheet);
		$("#print").click(this_worksheet.print);
		
		////// VIEW //////
		
		// TODO
	}
};