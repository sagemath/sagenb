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

/* At some point we may want to switch away from the 
 * current call/response system and instead use 
 * WebSockets.
 */

// the cell object
sagenb.worksheetapp.cell = function(id) {
	/* this allows us to access this cell object from 
	 * inner functions
	 */
	var this_cell = this;
	
	this_cell.id = id;
	this_cell.input = "";
	this_cell.output = "";
	this_cell.system = "";
	this_cell.percent_directives = null;
	
	this_cell.is_evaluate_cell = true;
	this_cell.is_evaluating = false;
	
	this_cell.codemirror = null;
	
	this_cell.worksheet = null;
	
	
	// this is the id of the interval for checking for new output
	this_cell.output_check_interval_id;
	
	// the amount of time in millisecs between update checks
	this_cell.output_check_interval = 500;

	
	///////////// UPDATING /////////////
	this_cell.update = function(render_container, auto_evaluate) {
		/* Update cell properties. Updates the codemirror mode (if necessary)
		 * and %hide stuff. Only performs rendering if a render_container is 
		 * given. If auto_evaluate is true and this is an #auto cell, it will
		 * be evaluated.
		 */
		async_request(this_cell.worksheet.worksheet_command("cell_properties"), this_cell.worksheet.generic_callback(function(status, response) {
			var X = decode_response(response);
			
			// set up all of the parameters
			this_cell.input = X.input;
			this_cell.output = X.output;
			this_cell.system = X.system;
			this_cell.percent_directives = X.percent_directives;
			
			// check for output_html
			if(X.output_html && $.trim(X.output_html) !== "") {
				this_cell.output = X.output_html;
			}
			
			this_cell.is_evaluate_cell = (X.type === "evaluate") ? true : false;
			
			// change the codemirror mode
			this_cell.update_codemirror_mode();
			
			if(render_container) {
				this_cell.render(render_container);
			}
			
			// if it's a %hide cell, hide it
			if(this_cell.is_hide()) {
				$("#cell_" + this_cell.id + " .input_cell").addClass("input_hidden");
			}
			
			// if it's an auto cell, evaluate
			if(auto_evaluate && this_cell.is_auto()) {
				this_cell.evaluate();
			}
		}),
		{
			id: this_cell.id
		});
	};
	this_cell.get_codemirror_mode = function() {
		/* This is a utility function to get the correct
		 * CodeMirror mode which this cell should be 
		 * rendered in.
		 */
		if(this_cell.system !== "" && this_cell.system !== null) {
			// specific cell system
			return system_to_codemirror_mode(this_cell.system);
		} else {
			// fall through to worksheet system
			return system_to_codemirror_mode(this_cell.worksheet.system);
		}
	}
	this_cell.update_codemirror_mode = function() {
		if(this_cell.codemirror) {
			if(this_cell.get_codemirror_mode() !== this_cell.codemirror.getOption("mode")) {
				// change the codemirror mode
				this_cell.codemirror.setOption("mode", this_cell.get_codemirror_mode());
			}
		}
	}
	
	//////// RENDER //////////
	this_cell.render = function(container) {
		if(this_cell.is_evaluate_cell) {
			// its an evaluate cell
		
			// render into the container
			$(container).html("<div class=\"cell evaluate_cell\" id=\"cell_" + this_cell.id + "\">" +
								"<div class=\"input_cell\">" +
								"</div>" +
							"</div> <!-- /cell -->");
			
			//set up extraKeys object
			/* because of some codemirror or chrome bug, we have to
			 * use = new Object(); instead of = {}; When we use = {};
			 * all of the key events are automatically passed to codemirror.
			 */
			var extrakeys = new Object();
			
			// set up autocomplete. we may want to use tab
			//extrakeys[sagenb.ctrlkey + "-Space"] = "autocomplete";
			
			// backspace handler
			extrakeys["Backspace"] = function(cm) {
				// check if it is empty
			
				// all of this is disabled for now
				if(cm.getValue() === "" && this_cell.worksheet.cells.length > 0) {
					// it's empty and not the only one -> delete it
					this_cell.delete();
				
					/* TODO: now we should focus on the cell above instead of 
					blurring everything and setting this back to -1 */
					this_cell.worksheet.focused_texarea_id = -1;
				} else {
					// not empty -> pass to the default behaviour
					throw CodeMirror.Pass;
				}
			};
			
			extrakeys["Shift-Enter"] = function(cm) {
				this_cell.evaluate();
			};
			
			extrakeys[sagenb.ctrlkey + "-N"] = function(cm) {
				this_cell.worksheet.new_worksheet();
			};
			extrakeys[sagenb.ctrlkey + "-S"] = function(cm) {
				this_cell.worksheet.save();
			};
			extrakeys[sagenb.ctrlkey + "-W"] = function(cm) {
				this_cell.worksheet.close();
			};
			extrakeys[sagenb.ctrlkey + "-P"] = function(cm) {
				this_cell.worksheet.print();
			};
			
			extrakeys["F1"] = function() {
				this_cell.worksheet.open_help();
			};
			
			// create the codemirror
			this_cell.codemirror = CodeMirror($(container).find(".input_cell")[0], {
				value: this_cell.input,
				
				mode: this_cell.get_codemirror_mode(),
				
				/* some of these may need to be settings */
				indentWithTabs: true,
				tabSize: 4,
				lineNumbers: false,
				matchBrackets: true,
				
				/* autofocus messes up when true */
				autofocus: false,
			
				onFocus: function() {
					// may need to make async_request here
					this_cell.worksheet.current_cell_id = this_cell.id;
					
					// unhide
					$("#cell_" + this_cell.id + " .input_cell").removeClass("input_hidden");
				},
				onBlur: function() {
					this_cell.worksheet.current_cell_id = -1;
					if(this_cell.input !== this_cell.codemirror.getValue()) {
						// the input has changed since the user focused
						// so we send it back to the server
						this_cell.send_input();
					}
					
					// update cell properties without rendering
					this_cell.update();
				},
			
				extraKeys: extrakeys
			});
			
			/* we may want to focus this cell here */
			
			// render the output
			this_cell.render_output();
		}
		else {
			// its a text cell
			$(container).html("<div class=\"cell text_cell\" id=\"cell_" + this_cell.id + "\">" + 
									"<div class=\"view_text\">" + this_cell.input + "</div>" + 
									"<div class=\"edit_text\">" + 
										"<textarea name=\"text_cell_textarea_" + this_cell.id + "\" id=\"text_cell_textarea_" + this_cell.id + "\">" + this_cell.input + "</textarea>" + 
										"<div class=\"buttons\">" + 
											"<button class=\"btn btn-danger delete_button pull-left\">Delete</button>" + 
											"<button class=\"btn cancel_button\">Cancel</button>" + 
											"<button class=\"btn btn-primary save_button\">Save</button>" + 
										"</div>" + 
									"</div>" + 
								"</div> <!-- /cell -->");
			
			
			// init tinyMCE
			// we may want to customize the editor some to include other buttons/features
			tinyMCE.init({
				mode: "exact",
				elements: ("text_cell_textarea_" + this_cell.id),
				theme: "advanced",
				
				width: "100%",
				height: "300"
			});
			
			var this_cell_dom = $("#cell_" + this_cell.id);
			
			// MathJax the text
			MathJax.Hub.Queue(["Typeset", MathJax.Hub, this_cell_dom.find(".view_text")[0]]);
			
			this_cell_dom.dblclick(function(e) {
				if(!this_cell.is_evaluate_cell) {
					// set the current_cell_id
					this_cell.worksheet.current_cell_id = this_cell.id;
					
					// lose any selection that was made
					if (window.getSelection) {
						window.getSelection().removeAllRanges();
					} else if (document.selection) {
						document.selection.empty();
					}
					
					// get tinymce instance
					//var ed = tinyMCE.get("text_cell_textarea_" + this_cell.id);
					
					// hide progress
					// ed.setProgressState(0);
					
					// add the edit class
					$("#cell_" + this_cell.id).addClass("edit");
				}
			});
			
			this_cell_dom.find(".delete_button").click(this_cell.delete);
			
			this_cell_dom.find(".cancel_button").click(function(e) {
				// get tinymce instance
				var ed = tinyMCE.get("text_cell_textarea_" + this_cell.id);
				
				// show progress
				// ed.setProgressState(1);
				
				// revert the text
				ed.setContent(this_cell.input);
				
				// remove the edit class
				$("#cell_" + this_cell.id).removeClass("edit");
			});
			
			this_cell_dom.find(".save_button").click(function(e) {
				// get tinymce instance
				var ed = tinyMCE.get("text_cell_textarea_" + this_cell.id);
				
				// show progress
				// ed.setProgressState(1);
				
				// send input
				this_cell.send_input();
				
				// update the cell
				this_cell_dom.find(".view_text").html(this_cell.input);
				
				// MathJax the text
				MathJax.Hub.Queue(["Typeset", MathJax.Hub, this_cell_dom.find(".view_text")[0]]);
				
				// remove the edit class
				$("#cell_" + this_cell.id).removeClass("edit");
			});
		}
	};
	this_cell.render_output = function(stuff_to_render) {
		/* Renders stuff_to_render as the cells output, 
		 * if given. If not, then it renders this_cell.output.
		 */
		
		// don't do anything for text cells
		if(!this_cell.is_evaluate_cell) return;
		
		var a = "";
		if(this_cell.output) a = this_cell.output;
		if(stuff_to_render) a = stuff_to_render;
		
		a = $.trim(a);
		
		function output_contains_latex(b) {
			return (b.indexOf('<span class="math">') !== -1) ||
				   (b.indexOf('<div class="math">') !== -1);
		}
		
		function output_contains_jmol(b) {
			return (b.indexOf('jmol_applet') !== -1);
		}
		
		// take the output off the dom
		$("#cell_" + this_cell.id + " .output_cell").detach();
		
		// it may be better to send a no_output value instead here
		if(a === "") {
			// if no output then don't do anything else
			return;
		}
		
		// the .output_cell div needs to be created
		var output_cell_dom = $("<div class=\"output_cell\" id=\"output_" + this_cell.id + "\"></div>").insertAfter("#cell_" + id + " .input_cell");
		
		/* TODO scrap JMOL, use three.js. Right now using 
		 applets screws up when you scoll an applet over the
		 navbar. Plus three.js is better supported, more modern,
		 etc.*/
		/* This method creates an iframe inside the output_cell
		 * and then dumps the output stuff inside the frame
		 */
		if(output_contains_jmol(a)) {
			var jmol_frame = $("<iframe />").addClass("jmol_frame").appendTo(output_cell_dom);
			window.cell_writer = jmol_frame[0].contentDocument;
			
			output_cell_dom.append(a);
			
			$(cell_writer.body).css("margin", "0");
			$(cell_writer.body).css("padding", "0");
			
			return;
		}
		
		// insert the new output
		output_cell_dom.html(a);
		
		if(output_contains_latex(a)) {
			/* \( \) is for inline and \[ \] is for block mathjax */
			
			var output_cell = $("#cell_" + this_cell.id + " .output_cell");
			
			if(output_cell.contents().length === 1) {
				// only one piece of math, make it big
				/* using contents instead of children guarantees that we
				 * get all other types of nodes including text and comments.
				 */
				
				output_cell.html("\\[" + output_cell.find(".math").html() + "\\]");
				
				// mathjax the ouput
				MathJax.Hub.Queue(["Typeset", MathJax.Hub, output_cell[0]]);
				
				return;
			}
			
			// mathjax each span with \( \)
			output_cell.find("span.math").each(function(i, element) {
				$(element).html("\\(" + $(element).html() + "\\)");
				MathJax.Hub.Queue(["Typeset", MathJax.Hub, element]);
			});
			
			// mathjax each div with \[ \]
			output_cell.find("div.math").each(function(i, element) {
				$(element).html("\\[" + $(element).html() + "\\]");
				MathJax.Hub.Queue(["Typeset", MathJax.Hub, element]);
			});
		}
	};
	
	////// FOCUS/BLUR ///////
	this_cell.focus = function() {
		if(this_cell.is_evaluate_cell) {
			this_cell.codemirror.focus();
		} else {
			// edit the tinyMCE
			$("#cell_" + this_cell.id).dblclick();
			tinyMCE.execCommand('mceFocus', false, "text_cell_textarea_" + this_cell.id);
		}
	}
	
	this_cell.is_focused = function() {
		return this_cell.worksheet.current_cell_id === this_cell.id;
	};
	this_cell.is_auto = function() {
		return (this_cell.percent_directives && $.inArray("auto", this_cell.percent_directives) >= 0);
	}
	this_cell.is_hide = function() {
		return (this_cell.percent_directives && $.inArray("hide", this_cell.percent_directives) >= 0);
	}
	
	/////// EVALUATION //////
	this_cell.send_input = function() {
		// mark the cell as changed
		$("#cell_" + this_cell.id).addClass("input_changed");
		
		// update the local input property
		if(this_cell.is_evaluate_cell) {
			this_cell.input = this_cell.codemirror.getValue();
		} else {
			// get tinymce instance
			var ed = tinyMCE.get("text_cell_textarea_" + this_cell.id);
			
			// set input
			this_cell.input = ed.getContent();
		}
		
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
			if (X.command === 'insert_cell') {
				// Insert a new cell after the evaluated cell.
				this_cell.worksheet.new_cell_after(this_cell.id);
			} /*else if (X.command === 'introspect') {
				//introspect[X.id].loaded = false;
				//update_introspection_text(X.id, 'loading...');
			} else if (in_slide_mode || doing_split_eval || is_interacting_cell(X.id)) {
				// Don't jump.
			} else {
				// "Plain" evaluation.  Jump to a later cell.
				//go_next(false, true);
			}*/
			
			this_cell.is_evaluating = true;
			
			// mark the cell as running
			$("#cell_" + this_cell.id).addClass("running");	
			this_cell.set_output_loading();
			
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
	};
	this_cell.check_for_output = function() {
		/* Currently, this function uses a setInterval command
		 * so that the result will be checked every X millisecs.
		 * In the future, we may want to implement an exponential
		 * pause system like the last notebook had.
		 */
		function stop_checking() {
			this_cell.is_evaluating = false;
			
			// mark the cell as done
			$("#cell_" + this_cell.id).removeClass("running");	
			
			// clear interval
			this_cell.output_check_interval_id = window.clearInterval(this_cell.output_check_interval_id);
		}
		
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
					stop_checking();
					return;
				}
				
				if(X.status === "d") {
					// evaluation done
					
					stop_checking();
					
					/* NOTE I'm not exactly sure what the interrupted property is for 
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
					
					// check for output_html
					// TODO it doesn't seem right to have a different property here
					// it seems like X.output is sufficient
					if($.trim(X.output_html) !== "") {
						this_cell.output = X.output_html;
					}
					
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
		// TODO we should maybe interrupt the cell if its running here
		async_request(this_cell.worksheet.worksheet_command('delete_cell_output'), this_cell.worksheet.generic_callback(function(status, response) {
			this_cell.output = "";
			this_cell.render_output();
		}), {
			id: toint(this_cell.id)
		});
	};
	
	this_cell.set_output_loading = function() {
		this_cell.render_output("<div class=\"progress progress-striped active\" style=\"width: 25%; margin: 0 auto;\">" + 
									"<div class=\"bar\" style=\"width: 100%;\"></div>" + 
								"</div>");
	};
	this_cell.set_output_hidden = function() {
		if($("#cell_" + this_cell.id + " .output_cell").length > 0) {
			this_cell.render_output("<hr>");
		}
	}
	this_cell.set_output_visible = function() {
		this_cell.render_output();
	}
	this_cell.has_input_hide = function() {
		// connect with Cell.percent_directives
		return this_cell.input.substring(0, 5) === "%hide";
	};
	
	this_cell.delete = function() {
		// TODO we should maybe interrupt the cell if its running here
		if(this_cell.is_evaluating) {
			// interrupt
			async_request(this_cell.worksheet.worksheet_command('interrupt'));
		}
		
		async_request(this_cell.worksheet.worksheet_command('delete_cell'), this_cell.worksheet.generic_callback(function(status, response) {
			X = decode_response(response);
			
			if(X.command === "ignore") return;
			
			this_cell.worksheet.cells[this_cell.id] = null;
			
			$("#cell_" + this_cell.id).parent().next().detach();
			$("#cell_" + this_cell.id).parent().detach();
		}), {
			id: toint(this_cell.id)
		});
	};
};

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
	// this may need to go somewhere else
	this_worksheet.generic_callback = function(extra_callback) {
		/* Constructs a generic callback function. The extra_callback
		 * argument is optional. If the callback receives a "success"
		 * status (and extra_callback is a function), extra_callback 
		 * will be called and passed the status and response arguments.
		 * If you use generic_callback with no extra_callback, you *must*
		 * call generic_callback() not just generic_callback because 
		 * this function is not a callback itself; it returns a callback
		 * function.
		 */
		
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
		/* for some reason pinging doesn't work well.
		 * the callback goes but jQuery throws a 404 error.
		 * this error may not be a bug, not sure...
		 */
		async_request(this_worksheet.worksheet_command('alive'), this_worksheet.generic_callback());
	};
	
	
	
	
	
	
	
	//////////// FILE MENU TYPE STUFF //////////
	this_worksheet.new_worksheet = function() {
		window.open("/new_worksheet");
	};
	this_worksheet.save = function() {
		async_request(this_worksheet.worksheet_command("save_snapshot"), this_worksheet.generic_callback());
	};
	this_worksheet.close = function() {
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
		window.print();
	};
	this_worksheet.open_help = function() {
		
	}
	
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
		// TODO
		for(cellid in this_worksheet.cells) {
			this_worksheet.cells[cellid].evaluate();
		}
	};
	this_worksheet.interrupt = function() {
		async_request(this_worksheet.worksheet_command('interrupt'), this_worksheet.generic_callback());
	};
	
	//// OUTPUT STUFF ////
	this_worksheet.hide_all_output = function() {
		async_request(this_worksheet.worksheet_command('hide_all'), this_worksheet.generic_callback(function(status, response) {
			$.each(this_worksheet.cells, function(i, cell) {
				if(cell) {
					cell.set_output_hidden();
				}
			});
		}));
	};
	this_worksheet.show_all_output = function() {
		async_request(this_worksheet.worksheet_command('show_all'), this_worksheet.generic_callback(function(status, response) {
			$.each(this_worksheet.cells, function(i, cell) {
				if(cell) {
					cell.set_output_visible();
				}
			});
		}));
	};
	this_worksheet.delete_all_output = function() {
		async_request(this_worksheet.worksheet_command('delete_all_output'), this_worksheet.generic_callback(function(status, response) {
			$.each(this_worksheet.cells, function(i, cell) {
				if(cell) {
					cell.output = "";
					cell.render_output();
				}
			});
		}));
	};
	
	this_worksheet.change_system = function(newsystem) {
		async_request(this_worksheet.worksheet_command("system/" + newsystem), this_worksheet.generic_callback(function(status, response) {
			this_worksheet.system = newsystem;
			
			$.each(this_worksheet.cells, function(i, cell) {
				if(cell) {
					cell.update_codemirror_mode();
				}
			});
		}));
	};
	this_worksheet.set_pretty_print = function(s) {
		async_request(this_worksheet.worksheet_command("pretty_print/" + s), this_worksheet.generic_callback());
	};
	
	//// NEW CELL /////
	this_worksheet.new_cell_before = function(id) {
		async_request(this_worksheet.worksheet_command("new_cell_before"), function(status, response) {
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
		async_request(this_worksheet.worksheet_command("new_cell_after"), function(status, response) {
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
		async_request(this_worksheet.worksheet_command("new_text_cell_before"), function(status, response) {
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
		async_request(this_worksheet.worksheet_command("new_text_cell_after"), function(status, response) {
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
		async_request(this_worksheet.worksheet_command("worksheet_properties"), this_worksheet.generic_callback(function(status, response) {
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
		async_request(this_worksheet.worksheet_command("cell_list"), this_worksheet.generic_callback(function(status, response) {
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
	}
	
	
	//////////////// INITIALIZATION ////////////////////
	this_worksheet.init = function() {
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
		
		////////// TYPESETTING CHECKBOX //////////
		$("#typesetting_checkbox").change(function(e) {
			this_worksheet.set_pretty_print($("#typesetting_checkbox").prop("checked"));
			
			// update
			this_worksheet.worksheet_update();
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
			async_request(this_worksheet.worksheet_command("invite_collab"), this_worksheet.generic_callback(), {
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
			
			async_request(command, this_worksheet.generic_callback(function(status, response) {
				this_worksheet.worksheet_update();
			}));
		});
		$("#auto_republish_checkbox").change(function(e) {
			// for some reason, auto is a toggle command
			async_request(this_worksheet.worksheet_command("publish?auto"), this_worksheet.generic_callback(function(status, response) {
				this_worksheet.worksheet_update();
			}))
		});
		
		// IMPORT DIALOG
		$("#import_modal .btn-primary").click(function(e) {
			$("#import_modal .tab-pane.active form").submit();
		});
		$("#import_modal .btn").click(function(e) {
			$.each($("#import_modal form"), function(i, form) {
				form.reset();
			});
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
			
			$.each(this_worksheet.cells, function(i, e) {
				if(e) numcells++;
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
		
		
		////////// EVALUATION ///////////
		$("#evaluate_all_cells").click();
		$("#interrupt").click(this_worksheet.interrupt);
		$("#restart_worksheet").click();
		// change system doesn't require event handler here
		$("#hide_all_output").click(this_worksheet.hide_all_output);
		$("#show_all_output").click(this_worksheet.show_all_output);
		$("#delete_all_output").click(this_worksheet.delete_all_output);
		
		// TODO
	}
};