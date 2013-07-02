sagenb.jmol = {};

sagenb.jmol.jmol_inline = function(container) {
	var _this = this;

	if(!container.hasClass("jmol_instance")) {
		throw "Not a Jmol container";
		return;
	}

	_this.container = container;
	_this.url = _this.container.data("url");
	_this.static_img_url = _this.container.data("img");
	_this.dimensions = [500, 500];
	_this.popup_win = null;

	_this.state_script = null;

	_this.init = function() {
		// get random id
		_this.suffix = Math.floor(Math.random() * 1000000);
		while($("#jmol_instance" + _this.suffix).length > 0) {
			_this.suffix = Math.floor(Math.random() * 1000000);
		}
		_this.container.attr("id", "jmol_instance" + _this.suffix);

		_this.sleep();
	};

	_this.is_alive = function() {
		return _this.container.hasClass("alive");
	};
	_this.appletify = function() {
		_this.container.children().detach();
		_this.update_state_script();

		jmolSetDocument(false);
		var sleep_btn = $("<button />")
			.text(gettext("Show Static Image"))
			.addClass("btn")
			.click(_this.sleep);
		var popup_btn = $("<button />")
			.text(gettext("Popout"))
			.addClass("btn")
			.click(_this.popup);
		_this.container.append(sleep_btn,
							   popup_btn,
							   $("<br>"),
							   jmolApplet(_this.dimensions, _this.state_script, _this.suffix));

		_this.container.addClass("alive");
	};
	_this.sleep = function() {
		if (_this.is_alive()) {
			_this.update_state_script();
			// _this.static_img_url = "data:image/jpeg;base64, " + jmolGetPropertyAsString("image", "", _this.suffix);
		}
		_this.container.children().detach();
		_this.container.removeClass("alive");
		var appletify_btn = $("<button />")
			.text(gettext("Open Interactive View"))
			.addClass("btn")
			.click(_this.appletify);
		var popup_btn = $("<button />")
			.text(gettext("Popout"))
			.addClass("btn")
			.click(_this.popup);
		var static_img = $("<img />").attr("src", _this.static_img_url);
		_this.container.append(appletify_btn, popup_btn, $("<br>"), static_img);
	};
	_this.resize = function(dimensions) {
		_this.dimensions = dimensions;
		jmolResizeApplet(dimensions, _this.suffix);
	};
	_this.update_state_script = function() {
		var default_dir = _this.url.split("?")[0];

		/*if(_this.is_alive()) {
			var stateStr = "#a comment to guarrantee one line\n";
			stateStr += jmolGetPropertyAsString("stateInfo", "", _this.suffix);
			var re_modelinline = /data "model list"(.|\n|\r)*end "model list"/;
			if(stateStr.match(re_modelinline)) {
				//If we didn't get a good response we'll ignore and get later
				var modelStr = (stateStr.match(re_modelinline))[0];
				modelStr = modelStr.replace(/\r\n/g, '|').replace(/\r/g, '|').replace(/\n/g, '|').replace(/\|\|/g, '|');
				modelStr = 'fix between here ' + modelStr + ' and here';
				stateStr = stateStr.replace(re_modelinline, modelStr);
			}

			_this.state_script = 'set defaultdirectory="' + default_dir + '";\n' + stateStr;
		}*/

		if(!_this.state_script) {
			_this.state_script = 'set defaultdirectory "' + default_dir + '";' + 
								 'script "' + _this.url + '";' + 
								 'isosurface fullylit;' + 
								 'pmesh o* fullylit;' + 
								 'set antialiasdisplay on;' + 
								 'set repaintWaitMs 1500;' + 
								 'x=defaultdirectory;' + 
								 'data "directory @x";' + 
								 'set MessageCallback "jmolMessageHandler";' + 
								 'show defaultdirectory;';
		}
	};
	_this.popup = function() {
		_this.sleep();
		_this.update_state_script();
		_this.popup_win = window.open("jmol_popup.html", "jmol_viewer" + _this.suffix, "width=600,height=600,resizable=1,statusbar=0");
		_this.popup_win.onload = function() {
			_this.popup_win.the_popup = new sagenb.jmol.jmol_popup(_this.popup_win);
			_this.popup_win.the_popup.state_script = _this.state_script;
			_this.popup_win.the_popup.url = _this.url;
			_this.popup_win.the_popup.suffix = _this.suffix + "popup";
			_this.popup_win.the_popup.init();
			_this.popup_win.focus();
		};
	};
}

sagenb.jmol.jmol_popup = function(win) {
	var _this = this;

	_this.win = win;
	_this.container = $(".jmol_instance", _this.win.document);
	
	_this.init = function() {
		jmolSetDocument(false);
		_this.container.html(jmolApplet("100%", _this.state_script, _this.suffix));

		function on_resize() {
			_this.container.height(_this.container.width());
		}
		$(_this.win).resize(on_resize);
		on_resize();
	};

	_this.spin = function(s) {
		if(s) {
			jmolScriptWait("spin on", "");
		}
		else {
			jmolScriptWait("spin off", "");
		}
	};
	_this.antialias = function(s) {
		if(s) {
			jmolScriptWait("set antialiasdisplay on", "");
		}
		else {
			jmolScriptWait("set antialiasdisplay off", "");
		}
	};
}