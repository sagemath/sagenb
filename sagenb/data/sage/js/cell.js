// the cell object
sagenb.worksheetapp.cell = function(id) {
	/* this allows us to access this cell object from 
	 * inner functions
	 */
	var _this = this;
	
	_this.id = id;
	_this.input = "";
	_this.output = "";
	_this.system = "";
	_this.percent_directives = null;
	
	_this.introspect_state = null;
	_this.is_evaluate_cell = true;
	_this.is_evaluating = false;
	
	_this.codemirror = null;

	_this.worksheet = null;
	
	// this is the id of the interval for checking for new output
	_this.output_check_interval_id;
	
	// the amount of time in millisecs between update checks
	_this.output_check_interval = 250;

	
	///////////// UPDATING /////////////
	_this.update = function(render_container, auto_evaluate) {
		/* Update cell properties. Updates the codemirror mode (if necessary)
		 * and %hide stuff. Only performs rendering if a render_container is 
		 * given. If auto_evaluate is true and this is an #auto cell, it will
		 * be evaluated.
		 */
		sagenb.async_request(_this.worksheet.worksheet_command("cell_properties"), sagenb.generic_callback(function(status, response) {
			var X = decode_response(response);
			
			// set up all of the parameters
			_this.input = X.input;
			_this.output = X.output;
			_this.system = X.system;
			_this.percent_directives = X.percent_directives;
			
			// it doesn't seem right to have a different property here
			// it seems like X.output is sufficient
			if($.trim(X.output_html) !== "") {
				_this.output = X.output_html;
			}
			if($.trim(X.output_wrapped) !== "") {
				_this.output = X.output_wrapped;
			}
					
			_this.is_evaluate_cell = (X.type === "evaluate") ? true : false;
			
			// change the codemirror mode
			_this.update_codemirror_mode();
			
			if(render_container) {
				_this.render(render_container);
			}
			
			// if it's a %hide cell, hide it
			if(_this.is_hide()) {
				$("#cell_" + _this.id + " .input_cell").addClass("input_hidden");
			}
			
			// if it's an auto cell, evaluate
			if(auto_evaluate && _this.is_auto()) {
				_this.evaluate();
			}
		}),
		{
			id: _this.id
		});
	};
	_this.get_codemirror_mode = function() {
		/* This is a utility function to get the correct
		 * CodeMirror mode which this cell should be 
		 * rendered in.
		 */
		if(_this.system !== "" && _this.system !== null) {
			// specific cell system
			return system_to_codemirror_mode(_this.system);
		} else {
			// fall through to worksheet system
			return system_to_codemirror_mode(_this.worksheet.system);
		}
	}
	_this.update_codemirror_mode = function() {
		if(_this.codemirror) {
			if(_this.get_codemirror_mode() !== _this.codemirror.getOption("mode")) {
				// change the codemirror mode
				_this.codemirror.setOption("mode", _this.get_codemirror_mode());
			}
		}
	}
	
	//////// RENDER //////////
	_this.render = function(container) {
		if(_this.is_evaluate_cell) {
			// its an evaluate cell
		
			// render into the container
			$(container).html("<div class=\"cell evaluate_cell\" id=\"cell_" + _this.id + "\">" +
									"<div class=\"input_cell\"></div>" +
									"<div class=\"evaluate_button_container\">" + 
										"<a href=\"#\" class=\"btn evaluate_button\">" + gettext("Evaluate") + "</a>" +
									"</div>" +
								"</div> <!-- /cell -->");
			
			// Bind the evaluate button
			$(container).find(".evaluate_button").click(_this.evaluate);

			//set up extraKeys object
			/* because of some codemirror or chrome bug, we have to
			 * use = new Object(); instead of = {}; When we use = {};
			 * all of the key events are automatically passed to codemirror.
			 */
			var extrakeys = new Object();
			
			// set up autocomplete. we may want to use tab
			//extrakeys[sagenb.ctrlkey + "-Space"] = "autocomplete";
			extrakeys[sagenb.ctrlkey + "-Space"] = function(cm) {
				_this.introspect();
			};
			
			extrakeys["Tab"] = function(cm) {
				if(!_this.introspect() && cm.getCursor(true).line != cm.getCursor().line) {
					CodeMirror.commands.indentMore(cm);
				}
			};
			
			extrakeys["Shift-Tab"] = "indentLess";
			
			// backspace handler
			extrakeys["Backspace"] = function(cm) {
				// check if it is empty
				_this.cancel_introspect();

				var key, count = 0;
				for(key in _this.worksheet.cells) count++;
				if(cm.getValue() === "" && count > 0 && !($("body").hasClass("single_cell_mode"))) {
					// it's empty and not the only one -> delete it
					_this.delete();
				} else {
					// not empty -> pass to the default behaviour
					throw CodeMirror.Pass;
				}
			};
			
			extrakeys["Shift-Enter"] = function(cm) {
				_this.evaluate();
			};
			
			extrakeys[sagenb.ctrlkey + "-N"] = function(cm) {
				_this.worksheet.new_worksheet();
			};
			extrakeys[sagenb.ctrlkey + "-S"] = function(cm) {
				_this.worksheet.save();
			};
			extrakeys[sagenb.ctrlkey + "-W"] = function(cm) {
				_this.worksheet.close();
			};
			extrakeys[sagenb.ctrlkey + "-P"] = function(cm) {
				_this.worksheet.print();
			};
			
			extrakeys["F1"] = function() {
				_this.worksheet.open_help();
			};
			
			// create the codemirror
			_this.codemirror = CodeMirror($(container).find(".input_cell")[0], {
				value: _this.input,
				
				/* some of these may need to be settings */
				indentWithTabs: false,
				tabSize: 4,
				indentUnit: 4,
				lineNumbers: $("#line_numbers_checkbox").prop("checked"),
				matchBrackets: true,
				
				readOnly: (_this.worksheet.published_mode ? true : false),

				mode: _this.get_codemirror_mode(),
				
				/* autofocus messes up when true */
				autofocus: false,
			
				onChange: function(cm, chg) {
					if(chg.text[0] === "(") {
						_this.introspect();
					}
					else if(chg.text[0] === ")") {
						_this.cancel_introspect();
					}
				},

				onFocus: function() {
					// may need to make sagenb.async_request here
					_this.worksheet.current_cell_id = _this.id;
					
					$(".cell").removeClass("current_cell");
					$("#cell_" + _this.id).addClass("current_cell");
					
					// unhide
					$("#cell_" + _this.id + " .input_cell").removeClass("input_hidden");
				},
				onBlur: function() {
					if(!($("body").hasClass("single_cell_mode"))) {
						$("#cell_" + _this.id).removeClass("current_cell");
					}
					
					if(_this.input !== _this.codemirror.getValue()) {
						// the input has changed since the user focused
						// so we send it back to the server
						_this.send_input();
					}
					
					// update cell properties without rendering
					_this.update();
				},
			
				extraKeys: extrakeys
			});
			
			// render the output
			_this.render_output();
		}
		else {
			// its a text cell
			if(_this.worksheet.published_mode) {
				$(container).html("<div class=\"cell text_cell\" id=\"cell_" + _this.id + "\">" + 
										"<div class=\"view_text\">" + _this.input + "</div>" + 
									"</div> <!-- /cell -->");

				var $_this = $("#cell_" + _this.id);
			
				// MathJax the text
				MathJax.Hub.Queue(["Typeset", MathJax.Hub, $_this.find(".view_text")[0]]);
			}
			else {
				$(container).html("<div class=\"cell text_cell\" id=\"cell_" + _this.id + "\">" + 
										"<div class=\"view_text\">" + _this.input + "</div>" + 
										"<div class=\"edit_text\">" + 
											"<textarea name=\"text_cell_textarea_" + _this.id + "\" id=\"text_cell_textarea_" + _this.id + "\">" + _this.input + "</textarea>" + 
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
					elements: ("text_cell_textarea_" + _this.id),
					theme: "advanced",
					
					width: "100%",
					height: "300"
				});
				
				var $_this = $("#cell_" + _this.id);
				
				// MathJax the text
				MathJax.Hub.Queue(["Typeset", MathJax.Hub, $_this.find(".view_text")[0]]);
				
				$_this.dblclick(function(e) {
					if(!_this.is_evaluate_cell) {
						// set the current_cell_id
						_this.worksheet.current_cell_id = _this.id;
						
						// lose any selection that was made
						if (window.getSelection) {
							window.getSelection().removeAllRanges();
						} else if (document.selection) {
							document.selection.empty();
						}
						
						// add the edit class
						$("#cell_" + _this.id).addClass("edit");
					}
				});
				
				$_this.find(".delete_button").click(_this.delete);
				
				$_this.find(".cancel_button").click(function(e) {
					// get tinymce instance
					var ed = tinyMCE.get("text_cell_textarea_" + _this.id);
					
					// revert the text
					ed.setContent(_this.input);
					
					// remove the edit class
					$("#cell_" + _this.id).removeClass("edit");
				});
				
				$_this.find(".save_button").click(function(e) {
					// get tinymce instance
					var ed = tinyMCE.get("text_cell_textarea_" + _this.id);
					
					// send input
					_this.send_input();
					
					// update the cell
					$_this.find(".view_text").html(_this.input);
					
					// MathJax the text
					MathJax.Hub.Queue(["Typeset", MathJax.Hub, $_this.find(".view_text")[0]]);
					
					// remove the edit class
					$("#cell_" + _this.id).removeClass("edit");
				});
			}
		}
	};
	_this.render_output = function(stuff_to_render) {
		/* Renders stuff_to_render as the cells output, 
		 * if given. If not, then it renders _this.output.
		 */
		
		// don't do anything for text cells
		if(!_this.is_evaluate_cell) return;
		
		stuff_to_render = stuff_to_render ? stuff_to_render : _this.output;
		stuff_to_render = $.trim(stuff_to_render);
		
		// if no output then don't do anything else
		if(!stuff_to_render) {
			// take the output off the dom
			$("#cell_" + _this.id + " .output_cell").detach();
			return;
		}

		var $output_cell = $("#output_" + _this.id);
		if($output_cell.length === 0) {
			$output_cell = $("<div class=\"output_cell\" id=\"output_" + _this.id + "\"></div>")
				.appendTo("#cell_" + _this.id);
		}

		// Interact constants.  See interact.py and related files.
		// Present in wrapped output, forces re-evaluation of ambient cell.
		var INTERACT_RESTART = '<!--__SAGE_INTERACT_RESTART__-->';
		// Delimit updated markup.
		var INTERACT_START = '<!--__SAGE__START-->';
		var INTERACT_END = '<!--__SAGE__END-->';

		if(stuff_to_render.indexOf(INTERACT_RESTART) > -1) {
			_this.evaluate();
			return;
		}

		var istart = stuff_to_render.indexOf(INTERACT_START);
		var iend = stuff_to_render.indexOf(INTERACT_END);
		if(istart > -1 && iend > -1) {
			if(_this.has_interact()) {
				// update interact
				stuff_to_render = stuff_to_render.slice(istart + INTERACT_START.length, iend);
				$("#cell-interact-" + _this.id).html(stuff_to_render);
			}
			else {
				// start interact
				$output_cell.html(stuff_to_render);
				_this.evaluate_interact({}, 1);
			}
		}
		else {
			// create the .output_cell div
			$output_cell.html(stuff_to_render);
		}

		if($output_cell.find(".jmol_instance").length > 0) {
			// TODO Is it possible to have multiple Jmol's in a single cell output?
			// If so, we would need to call jmol_inline.init(), etc on all of them
			var jmol_instance = new sagenb.jmol.jmol_inline($output_cell.find(".jmol_instance"));
			jmol_instance.init();
		}
		
		if($output_cell.find(".math").length > 0 ||
		   $output_cell.find("script[type='math/tex']").length > 0) {
			/* \( \) is for inline and \[ \] is for block mathjax */
			
			if($output_cell.contents().length === 1) {
				// only one piece of math, make it big
				/* using contents instead of children guarantees that we
				 * get all other types of nodes including text and comments.
				 */
				$output_cell.html("\\[" + $output_cell.find("script[type='math/tex']").html() + "\\]");
			}
			else {
				// NOTE: these may be obsolete

				// mathjax each span with \( \)
				$output_cell.find("span.math").each(function(i, element) {
					$(element).html("\\(" + $(element).html() + "\\)");
				});
				
				// mathjax each div with \[ \]
				$output_cell.find("div.math").each(function(i, element) {
					$(element).html("\\[" + $(element).html() + "\\]");
				});
			}

			MathJax.Hub.Queue(["Typeset", MathJax.Hub, $output_cell[0]]);
		}
	};
	
	////// FOCUS/BLUR ///////
	_this.focus = function() {
		if(_this.codemirror) {
			_this.codemirror.focus();
		} else {
			// edit the tinyMCE
			$("#cell_" + _this.id).dblclick();
			tinyMCE.execCommand('mceFocus', false, "text_cell_textarea_" + _this.id);
		}
	}
	
	_this.is_focused = function() {
		return _this.worksheet.current_cell_id === _this.id;
	};
	_this.is_auto = function() {
		return (_this.percent_directives && $.inArray("auto", _this.percent_directives) >= 0);
	};
	_this.is_hide = function() {
		return (_this.percent_directives && $.inArray("hide", _this.percent_directives) >= 0);
	};

	_this.has_interact = function() {
		return $("#cell-interact-" + _this.id).length > 0;
	};

	///// POPOVER /////
	_this.hide_popover = function() {
		$(".tooltip_root").popover("hide");
		$(".tooltip_root").detach();
	}
	_this.show_popover = function(content) {
		_this.hide_popover();
		var tooltip_root = $("<div />").addClass("tooltip_root").appendTo("body");
		var pos = _this.codemirror.cursorCoords();
		tooltip_root.css({
			"position": "absolute",
			"left": pos.x,
			"top": pos.yBot
		});

		tooltip_root.popover({
			placement: "bottom",
			trigger: "manual",
			content: content
		});

		tooltip_root.popover("show");
		MathJax.Hub.Queue(["Typeset", MathJax.Hub, $(".popover")[0]]);

		var safety = 50;
		var off = $(".popover-inner").offset();
		var pop_w = $(".popover-inner").width();
		var window_w = $(window).width();
		if(off.left < safety) {
			$(".popover-inner").offset({left: safety, top: off.top});
		}
		else if(off.left + pop_w > window_w - safety) {
			$(".popover-inner").offset({left: window_w - safety - pop_w, top: off.top});
		}

		$("body").click(function(e) {
			_this.cancel_introspect();
		}).keydown(function(e) {
			if(e.which === 27) {
				// Esc
				_this.cancel_introspect();
			}
		});
	}
	
	/////// EVALUATION //////
	var _evaluate_callback = sagenb.generic_callback(function(status, response) {
		var X = decode_response(response);
		
		// figure out whether or not we are interacting
		// seems like this is redundant
		// X.interact = X.interact ? true : false;
		
		// Something went wrong, e.g., cell id's don't match
		if (X.id !== _this.id) return;

		if (X.command && (X.command.slice(0, 5) === 'error')) {
			// TODO: use a bootstrap error message
			console.log(X, X.id, X.command, X.message);
			return;
		}
		
		// not sure about these commands
		if (X.command === 'insert_cell') {
			// Insert a new cell after the evaluated cell.
			_this.worksheet.new_cell_after(_this.id);
		}

		_this.is_evaluating = true;
		$("#cell_" + _this.id).addClass("running");	
		
		// start checking for output
		_this.check_for_output();
	});

	_this.send_input = function() {
		if(_this.worksheet.published_mode) return;

		// mark the cell as changed
		$("#cell_" + _this.id).addClass("input_changed");
		
		// update the local input property
		if(_this.is_evaluate_cell) {
			_this.input = _this.codemirror.getValue();
		} else {
			// get tinymce instance
			var ed = tinyMCE.get("text_cell_textarea_" + _this.id);
			
			// set input
			_this.input = ed.getContent();
		}
		
		// update the server input property
		sagenb.async_request(_this.worksheet.worksheet_command("eval"), sagenb.generic_callback, {
			save_only: 1,
			id: _this.id,
			input: _this.input
		});
	};
	_this.evaluate = function() {
		if(_this.worksheet.published_mode) return;
		if(!_this.is_evaluate_cell) {
			// we're a text cell
			_this.continue_evaluating_all();
			return;
		}
		
		if(_this.is_evaluating) {
			return;
		}

		_this.cancel_introspect();
		_this.set_output_loading();

		// we're an evaluate cell
		sagenb.async_request(_this.worksheet.worksheet_command("eval"), _evaluate_callback, {
			// 0 = false, 1 = true this needs some conditional
			newcell: 0,
			
			id: toint(_this.id),
			
			/* It's necessary to get the codemirror value because the user
			 * may have made changes and not blurred the codemirror so the 
			 * changes haven't been put in _this.input
			 */
			input: _this.codemirror.getValue()
		});
	};
	_this.evaluate_interact = function(update, recompute) {
		if(_this.worksheet.published_mode) return;
		sagenb.async_request(_this.worksheet.worksheet_command("eval"), _evaluate_callback, {
			id: toint(_this.id),
			interact: 1,
			variable: update.variable || '',
			adapt_number: update.adapt_number || -1,
			value: update.value || '',
			recompute: recompute,
			newcell: 0
		});
	};
	_this.introspect = function() {
		/* Attempts to begin an introspection. Firstly, it splits the input 
		 * according to the cursor position. Then it matches the text before 
		 * the cursor to some regex expression to check which type of 
		 * introspection we are doing. Once it determines the type of introspection,
		 * it stores some properties in the introspect_state variable. If 
		 * there is nothing to introspect, it returns false. Otherwise, 
		 * it executes the introspection and returns true. Handling of the 
		 * introspection result is done in the check_for_output function.
		 */
		
		if(!_this.is_evaluate_cell) return false;
		if(_this.worksheet.published_mode) return false;
		if($(".tooltip_root").length > 0) return false;
		if(_this.is_evaluating) return false;
		// if(_this.introspect_state) return false;
		
		/* split up the text cell and get before and after */
		var before = "";
		var after = "";
		
		var pos = _this.codemirror.getCursor(false);
		var lines = _this.codemirror.getValue().split("\n");
		
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
		_this.introspect_state = {};
		_this.introspect_state.before_replacing_word = before;
		_this.introspect_state.after_cursor = after;
		_this.introspect_state.previous_value = _this.codemirror.getValue();
		
		/* Regexes */
		var command_pat = "([a-zA-Z_][a-zA-Z._0-9]*)$";
		var function_pat = "([a-zA-Z_][a-zA-Z._0-9]*)\\([^()]*$";
		try {
			command_pat = new RegExp(command_pat);
			function_pat = new RegExp(function_pat);
		} catch (e) {}
		
		m = command_pat.exec(before);
		f = function_pat.exec(before);
		
		if (before.slice(-1) === "?") {
			// We're starting with a docstring or source code.
			_this.introspect_state.docstring = true;
		} else if (m) {
			// We're starting with a list of completions.
			_this.introspect_state.code_completion = true;
			_this.introspect_state.replacing_word = m[1];
			_this.introspect_state.before_replacing_word = before.substring(0, before.length - m[1].length);
		} else if (f !== null) {
			// We're in an open function paren -- give info on the
			// function.
			before = f[1] + "?";
			// We're starting with a docstring or source code.
			_this.introspect_state.docstring = true;
		} else {
			// Just a tab.
			return false;
		}
		
		sagenb.async_request(_this.worksheet.worksheet_command("introspect"), sagenb.generic_callback(function(status, response) {
			/* INTROSPECT CALLBACK */
			_this.is_evaluating = true;
			
			// start checking for output
			_this.check_for_output();
		}),
		
		/* REQUEST OPTIONS */
		{
			id: toint(_this.id),
			before_cursor: before,
			after_cursor: after
		});
		
		return true;
	};
	_this.cancel_introspect = function() {
		_this.hide_popover();
		_this.introspect_state = null;
	};
	_this.check_for_output = function() {
		function stop_checking() {
			_this.is_evaluating = false;
			
			// mark the cell as done
			$("#cell_" + _this.id).removeClass("running");	
			
			// clear interval
			_this.output_check_interval_id = window.clearInterval(_this.output_check_interval_id);
		}
		
		function do_check() {
			sagenb.async_request(_this.worksheet.worksheet_command("cell_update"), sagenb.generic_callback(function(status, response) {
				if(response === "") {
					// empty response, try again after a little bit
					// setTimeout(_this.check_for_output, 500);
					return;
				}
				
				var X = decode_response(response);
				
				if(X.status === "e") {
					// there was an error, stop checking
					_this.worksheet.show_connection_error();
					stop_checking();
					return;
				}

				// check if introspect was cancelled
				if(X.introspect_output && $.trim(X.introspect_output).length > 0 && _this.introspect_state == null) {
					// introspect cancelled
					stop_checking();
					return;
				}
				
				if(X.status === "d") {
					// evaluation done
					stop_checking();
					
					if(X.new_input !== "") {
						// if the editor has changed, re-introspect
						// This is buggy
						/*if(_this.codemirror.getValue() !== _this.introspect_state.previous_value) {
							setTimeout(_this.introspect, 50);
							return;
						}*/
						
						// update the input
						_this.input = X.new_input;
						
						// update codemirror/tinymce
						if(_this.is_evaluate_cell) {
							_this.codemirror.setValue(_this.input);
							
							// here we need to set the new cursor position if 
							// we are in introspect
							if(_this.introspect_state) {
								var after_lines = _this.introspect_state.after_cursor.split("\n");
								var val_lines = _this.codemirror.getValue().split("\n");
								
								var pos = {};
								pos.line = val_lines.length - after_lines.length;
								pos.ch = val_lines[pos.line].length - after_lines[0].length;
								
								_this.codemirror.setCursor(pos);
							}
						}
					}
					
					// introspect
					if(X.introspect_output && $.trim(X.introspect_output).length > 0) {
						if(_this.introspect_state.code_completion) {
							// open codemirror simple hint
							var editor = _this.codemirror;

							/* stolen from simpleHint */
							// We want a single cursor position.
							// if (editor.somethingSelected()) return;
							
							//var result = getHints(editor);
							//if (!result || !result.list.length) return;
							var completions = $.trim(X.introspect_output).split("\n");
							
							/* Insert the given completion str into the input */
							function insert(str) {
								// we can take this out in the next release of CodeMirror
								str = str.replace("\r", "");

								var newpos = {};
								var lines = _this.introspect_state.before_replacing_word.split("\n");
								newpos.line = lines.length - 1;
								newpos.ch = lines[lines.length - 1].length + str.length;
								
								editor.setValue(_this.introspect_state.before_replacing_word + str + _this.introspect_state.after_cursor);
								
								editor.setCursor(newpos);
							}
							
							// When there is only one completion, use it directly.
							// TODO we can't do return here since more commands come after introspection stuff
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
									
									// This is buggy
									// setTimeout(_this.introspect, 50);
								}
							});
							CodeMirror.connect(sel, "dblclick", pick);

							sel.focus();
							// Opera sometimes ignores focusing a freshly created node
							if (window.opera) setTimeout(function(){if (!done) sel.focus();}, 100);
							//return true;
						}
						else {
							// docstring
							_this.show_popover($.trim(X.introspect_output));
						}
					}

					// update the output
					_this.output = X.output;
					
					// it doesn't seem right to have a different property here
					// it seems like X.output is sufficient
					if($.trim(X.output_html) !== "") {
						_this.output = X.output_html;
					}
					if($.trim(X.output_wrapped) !== "") {
						_this.output = X.output_wrapped;
					}
					
					// render to the DOM
					_this.render_output();
					
					// EVALUATE ALL STUFF
					_this.continue_evaluating_all();
				}
			}),
				{
					id: _this.id
				}
			);
		}

		// clear interval
		_this.output_check_interval_id = window.clearInterval(_this.output_check_interval_id);
		
		// start checking
		_this.output_check_interval_id = window.setInterval(do_check, _this.output_check_interval);
	};
	
	_this.continue_evaluating_all = function() {
		if(_this.worksheet.published_mode) return;
		if(_this.worksheet.is_evaluating_all) {
			// go evaluate the next cell
			var $nextcell = $("#cell_" + _this.id).parent().next().next().find(".cell");
			
			if($nextcell.length > 0) {
				// we're not the last cell -> evaluate next
				var nextcell_id = parseInt($nextcell.attr("id").substring(5));
				
				_this.worksheet.cells[nextcell_id].evaluate();
			} else {
				// we're the last cell -> stop evaluating all
				_this.worksheet.is_evaluating_all = false;
			}
		}
	}
	
	/////// OUTPUT ///////
	_this.delete_output = function() {
		if(_this.worksheet.published_mode) return;
		// TODO we should maybe interrupt the cell if its running here
		sagenb.async_request(_this.worksheet.worksheet_command('delete_cell_output'), sagenb.generic_callback(function(status, response) {
			_this.output = "";
			_this.render_output();
		}), {
			id: toint(_this.id)
		});
	};
	
	_this.set_output_loading = function() {
		if(_this.worksheet.published_mode) return;
		_this.render_output("<div class=\"progress progress-striped active\" style=\"width: 25%; margin: 0 auto;\">" + 
									"<div class=\"bar\" style=\"width: 100%;\"></div>" + 
								"</div>");
	};
	_this.set_output_hidden = function() {
		if(_this.worksheet.published_mode) return;
		if($("#cell_" + _this.id + " .output_cell").length > 0) {
			_this.render_output("<hr>");
		}
	}
	_this.set_output_visible = function() {
		if(_this.worksheet.published_mode) return;
		_this.render_output();
	}
	_this.has_input_hide = function() {
		// connect with Cell.percent_directives
		return _this.input.substring(0, 5) === "%hide";
	};
	
	_this.delete = function() {
		if(_this.worksheet.published_mode) return;
		if(_this.is_evaluating) {
			// interrupt
			sagenb.async_request(_this.worksheet.worksheet_command('interrupt'));
		}
		
		sagenb.async_request(_this.worksheet.worksheet_command('delete_cell'), sagenb.generic_callback(function(status, response) {
			X = decode_response(response);
			if(X.command === "ignore") return;
			
			delete _this.worksheet.cells[_this.id];
			
			$("#cell_" + _this.id).parent().next().detach();
			$("#cell_" + _this.id).parent().detach();
		}), {
			id: toint(_this.id)
		});
	};
};