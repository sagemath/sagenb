sagenb.Jmol = {};

sagenb.Jmol.Jmol_instance = function(container) {
	var _this = this;

	if(!container.hasClass("Jmol_instance")) {
		throw "Not a Jmol container";
		return;
	}

	_this.container = container;
	_this.url = _this.container.data("url");
	_this.static_img_url = _this.container.data("img");
	_this.dimensions = [500, 500];
	_this.popup_win = null;

	_this.state_script = null;

	// get random id
	_this.suffix = Math.floor(Math.random() * 1000000);
	while($("#Jmol_instance" + _this.suffix).length > 0) {
		_this.suffix = Math.floor(Math.random() * 1000000);
	}
	_this.container.attr("id", "Jmol_instance" + _this.suffix);

	_this.is_alive = function() {
		return _this.container.hasClass("alive");
	};
	_this.appletify = function() {
		_this.container.children().detach();
		_this.update_state_script();

		jmolSetDocument(false);
		var sleep_btn = $("<button />")
			.text("Show Static Image")
			.addClass("btn")
			.css({
				"margin-bottom": "5px",
				"margin-right": "5px"
			})
			.click(_this.sleep);
		var popup_btn = $("<button />")
			.text("Popout")
			.addClass("btn")
			.css({ "margin-bottom": "5px" })
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
			_this.static_img_url = "data:image/jpeg;base64, " + jmolGetPropertyAsString("image", "", _this.suffix);
		}
		_this.container.children().detach();
		_this.container.removeClass("alive");
		var appletify_btn = $("<button />")
			.text("Open Interactive View")
			.addClass("btn")
			.css({ "margin-bottom": "5px" })
			.click(_this.appletify);
		var static_img = $("<img />").attr("src", _this.static_img_url);
		_this.container.append(appletify_btn, $("<br>"), static_img);
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
		_this.popup_win = window.open("", "jmol_viewer" + _this.suffix, "width=600,height=600,resizable=1,statusbar=0");
		_this.popup_win.document.title = "Sage 3d Viewer";
		jmolSetDocument(_this.popup_win.document);
		jmolApplet("100%", _this.state_script, _this.suffix);
		$(_this.popup_win.document.body).css({ "margin": "0" });
		_this.popup_win.focus();
	};
	_this.spin = function(s) {
		if(s) {
			jmolScriptWait("spin on", _this.suffix);
		}
		else {
			jmolScriptWait("spin off", _this.suffix);
		}
	};
	_this.antialias = function(s) {
		if(s) {
			jmolScriptWait("set antialiasdisplay on", _this.suffix);
		}
		else {
			jmolScriptWait("set antialiasdisplay off", _this.suffix);
		}
	};

	_this.sleep();
}