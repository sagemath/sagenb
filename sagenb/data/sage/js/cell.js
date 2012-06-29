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
	
	this_cell.introspect_state = null;
	this_cell.is_evaluate_cell = true;
	this_cell.is_evaluating = false;
	
	this_cell.codemirror = null;
	
	this_cell.worksheet = null;
	
	
	// this is the id of the interval for checking for new output
	this_cell.output_check_interval_id;
	
	// the amount of time in millisecs between update checks
	this_cell.output_check_interval = 250;

	
	///////////// UPDATING /////////////
	this_cell.update = function(render_container, auto_evaluate) {
		/* Update cell properties. Updates the codemirror mode (if necessary)
		 * and %hide stuff. Only performs rendering if a render_container is 
		 * given. If auto_evaluate is true and this is an #auto cell, it will
		 * be evaluated.
		 */
		sagenb.async_request(this_cell.worksheet.worksheet_command("cell_properties"), sagenb.generic_callback(function(status, response) {
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
			extrakeys[sagenb.ctrlkey + "-Space"] = function(cm) {
				this_cell.introspect();
			};
			
			// backspace handler
			extrakeys["Backspace"] = function(cm) {
				// check if it is empty
			
				// all of this is disabled for now
				if(cm.getValue() === "" && this_cell.worksheet.cells.length > 0) {
					// it's empty and not the only one -> delete it
					this_cell.delete();
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
				
				/* some of these may need to be settings */
				indentWithTabs: false,
				tabSize: 4,
				lineNumbers: false,
				matchBrackets: true,
				
				mode: this_cell.get_codemirror_mode(),
				
				/* autofocus messes up when true */
				autofocus: false,
			
				onFocus: function() {
					// may need to make sagenb.async_request here
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
			
			var $this_cell = $("#cell_" + this_cell.id);
			
			// MathJax the text
			MathJax.Hub.Queue(["Typeset", MathJax.Hub, $this_cell.find(".view_text")[0]]);
			
			$this_cell.dblclick(function(e) {
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
			
			$this_cell.find(".delete_button").click(this_cell.delete);
			
			$this_cell.find(".cancel_button").click(function(e) {
				// get tinymce instance
				var ed = tinyMCE.get("text_cell_textarea_" + this_cell.id);
				
				// show progress
				// ed.setProgressState(1);
				
				// revert the text
				ed.setContent(this_cell.input);
				
				// remove the edit class
				$("#cell_" + this_cell.id).removeClass("edit");
			});
			
			$this_cell.find(".save_button").click(function(e) {
				// get tinymce instance
				var ed = tinyMCE.get("text_cell_textarea_" + this_cell.id);
				
				// show progress
				// ed.setProgressState(1);
				
				// send input
				this_cell.send_input();
				
				// update the cell
				$this_cell.find(".view_text").html(this_cell.input);
				
				// MathJax the text
				MathJax.Hub.Queue(["Typeset", MathJax.Hub, $this_cell.find(".view_text")[0]]);
				
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
		sagenb.async_request(this_cell.worksheet.worksheet_command("eval"), sagenb.generic_callback, {
			save_only: 1,
			id: this_cell.id,
			input: this_cell.input
		});
	};
	this_cell.evaluate = function() {
		if(!this_cell.is_evaluate_cell) {
			// we're a text cell
			this_cell.continue_evaluating_all();
			return;
		}
		
		// we're an evaluate cell
		sagenb.async_request(this_cell.worksheet.worksheet_command("eval"), sagenb.generic_callback(function(status, response) {
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
				
				// don't need anything
			}*/
			
			/* else if (in_slide_mode || doing_split_eval || is_interacting_cell(X.id)) {
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
	this_cell.introspect = function() {
		if(!this_cell.is_evaluate_cell) return;
		
		/* split up the text cell and get before and after */
		var before = "";
		var after = "";
		
		var pos = this_cell.codemirror.getCursor(false);
		var lines = this_cell.codemirror.getValue().split("\n");
		
		before += lines.slice(0, pos.line).join("\n");
		if(pos.ch > 0) {
			if(pos.line > 0) {
				before += "\n";
			}
			before += lines[pos.line].substring(0, pos.ch);
		}
		
		after += lines[pos.line].substring(pos.ch);
		if(pos.line < lines.length - 1) {
			after += "\n";
			after += lines.slice(pos.line + 1).join("\n");
		}
		
		
		/* set up introspection state */
		this_cell.introspect_state = {};
		this_cell.introspect_state.before_replacing_word = before;
		this_cell.introspect_state.after_cursor = after;
		
		/*  */
		var command_pat = "([a-zA-Z_][a-zA-Z._0-9]*)$";
		var function_pat = "([a-zA-Z_][a-zA-Z._0-9]*)\\([^()]*$";
		try {
			command_pat = new RegExp(command_pat);
			//function_pat = new RegExp(function_pat);
		} catch (e) {}
		
		m = command_pat.exec(before);
		//f = function_pat.exec(before);
		
		if (before.slice(-1) === "?") {
			// We're starting with a docstring or source code.
			this_cell.introspect_state.docstring = true;
		} else if (m) {
			// We're starting with a list of completions.
			this_cell.introspect_state.replacing = true;
			this_cell.introspect_state.replacing_word = m[1];
			this_cell.introspect_state.before_replacing_word = before.substring(0, before.length - m[1].length);
		} else if (f !== null) {
			// We're in an open function paren -- give info on the
			// function.
			before = f[1] + "?";
			// We're starting with a docstring or source code.
			this_cell.introspect_state.docstring = true;
		}/* else {
			// Just a tab.
			cell_has_changed = true;
			do_replacement(id, '    ', false);
			return;
		}*/
		
		sagenb.async_request(this_cell.worksheet.worksheet_command("introspect"), sagenb.generic_callback(function(status, response) {
			/* INTROSPECT CALLBACK */
			
			// start checking for output
			this_cell.check_for_output();
		}),
		
		/* REQUEST OPTIONS */
		{
			id: toint(this_cell.id),
			before_cursor: before,
			after_cursor: after
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
			sagenb.async_request(this_cell.worksheet.worksheet_command("cell_update"), sagenb.generic_callback(function(status, response) {
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
							
							// here we need to set the new cursor position if 
							// we are in introspect
							if(this_cell.introspect_state) {
								var after_lines = this_cell.introspect_state.after_cursor.split("\n");
								var val_lines = this_cell.codemirror.getValue().split("\n");
								
								var pos = {};
								pos.line = val_lines.length - after_lines.length;
								pos.ch = val_lines[pos.line].length - after_lines[0].length;
								
								this_cell.codemirror.setCursor(pos);
							}
						} else {
							/* I don't think we need to do anything for TinyMCE
							 * but it would go here
							 */
						}
					}
					
					// introspect
					if(X.introspect_completions && X.introspect_completions.length > 0) {
						// open codemirror simple hint
						
						var editor = this_cell.codemirror;
						
						/* stolen from simpleHint */
						// We want a single cursor position.
						// if (editor.somethingSelected()) return;
						
						//var result = getHints(editor);
						//if (!result || !result.list.length) return;
						var completions = X.introspect_completions;
						
						/* Insert the given completion str into the input */
						function insert(str) {
							var oldpos = editor.getCursor();
							var newpos = {};
							newpos.line = oldpos.line;
							newpos.ch = oldpos.ch + str.length;
							
							editor.setValue(this_cell.introspect_state.before_replacing_word + str + this_cell.introspect_state.after_cursor);
							
							editor.setCursor(newpos);
						}
						
						// When there is only one completion, use it directly.
						if (completions.length === 1) {insert(completions[0]); return true;}
						
						// Build the select widget
						/* Because this code is stolen directly from simple-hint.js
						 * it does not use jQuery for any of the DOM manipulation.
						 */
						var complete = document.createElement("div");
						complete.className = "CodeMirror-completions";
						var sel = complete.appendChild(document.createElement("select"));
						// Opera doesn't move the selection when pressing up/down in a
						// multi-select, but it does properly support the size property on
						// single-selects, so no multi-select is necessary.
						if (!window.opera) sel.multiple = true;
						for (var i = 0; i < completions.length; ++i) {
							var opt = sel.appendChild(document.createElement("option"));
							opt.appendChild(document.createTextNode(completions[i]));
						}
						sel.firstChild.selected = true;
						sel.size = Math.min(10, completions.length);
						var pos = editor.cursorCoords();
						complete.style.left = pos.x + "px";
						complete.style.top = pos.yBot + "px";
						document.body.appendChild(complete);
						// If we're at the edge of the screen, then we want the menu to appear on the left of the cursor.
						var winW = window.innerWidth || Math.max(document.body.offsetWidth, document.documentElement.offsetWidth);
						if(winW - pos.x < sel.clientWidth)
						complete.style.left = (pos.x - sel.clientWidth) + "px";
						// Hack to hide the scrollbar.
						if (completions.length <= 10)
						complete.style.width = (sel.clientWidth - 1) + "px";

						
						/* Close the completions menu */
						var done = false;
						function close() {
							if (done) return;
							done = true;
							complete.parentNode.removeChild(complete);
						}
						
						/* Pick and insert the currently highlighted completion */
						function pick() {
							insert(completions[sel.selectedIndex]);
							close();
							setTimeout(function(){editor.focus();}, 50);
						}
						
						CodeMirror.connect(sel, "blur", close);
						CodeMirror.connect(sel, "keydown", function(event) {
							var code = event.keyCode;
							// Enter
							if (code === 13) {CodeMirror.e_stop(event); pick();}
							
							// Escape
							else if (code === 27) {CodeMirror.e_stop(event); close(); editor.focus();}
							
							// Backspace
							else if (code === 8) {
								close();
								editor.focus();
								editor.triggerOnKeyDown(event);
							}
							
							// Everything else besides up/down
							else if (code !== 38 && code !== 40) {
								close(); editor.focus();
								
								// Pass the event to the CodeMirror instance so that it can handle things like backspace properly.
								editor.triggerOnKeyDown(event);
								
								setTimeout(this_cell.introspect, 50);
							}
						});
						CodeMirror.connect(sel, "dblclick", pick);

						sel.focus();
						// Opera sometimes ignores focusing a freshly created node
						if (window.opera) setTimeout(function(){if (!done) sel.focus();}, 100);
						return true;
					}
					
					// update the output
					this_cell.output = X.output;
					
					// check for output_html
					// it doesn't seem right to have a different property here
					// it seems like X.output is sufficient
					if($.trim(X.output_html) !== "") {
						this_cell.output = X.output_html;
					}
					
					// render to the DOM
					this_cell.render_output();
					
					// EVALUATE ALL STUFF
					this_cell.continue_evaluating_all();
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
	
	this_cell.continue_evaluating_all = function() {
		if(this_cell.worksheet.is_evaluating_all) {
			// go evaluate the next cell
			var $nextcell = $("#cell_" + this_cell.id).parent().next().next().find(".cell");
			
			if($nextcell.length > 0) {
				// we're not the last cell -> evaluate next
				var nextcell_id = parseInt($nextcell.attr("id").substring(5));
				
				this_cell.worksheet.cells[nextcell_id].evaluate();
			} else {
				// we're the last cell -> stop evaluating all
				this_cell.worksheet.is_evaluating_all = false;
			}
		}
	}
	
	this_cell.is_interact_cell = function() {
		
	};
	
	
	/////// OUTPUT ///////
	this_cell.delete_output = function() {
		// TODO we should maybe interrupt the cell if its running here
		sagenb.async_request(this_cell.worksheet.worksheet_command('delete_cell_output'), sagenb.generic_callback(function(status, response) {
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
		if(this_cell.is_evaluating) {
			// interrupt
			sagenb.async_request(this_cell.worksheet.worksheet_command('interrupt'));
		}
		
		sagenb.async_request(this_cell.worksheet.worksheet_command('delete_cell'), sagenb.generic_callback(function(status, response) {
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


