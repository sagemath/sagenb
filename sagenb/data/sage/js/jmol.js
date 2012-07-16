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
		_this.container.addClass("alive");

		if(!_this.state_script) {
			var default_dir = _this.url.split("?")[0];
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

		jmolSetDocument(false);
		var sleep_btn = $("<button />")
			.text("Show Static Image")
			.addClass("btn")
			.css({ "margin-bottom": "5px" })
			.click(_this.sleep);
		_this.container.append(sleep_btn, $("<br>"), jmolApplet(_this.dimensions, _this.state_script, _this.suffix));
	};
	_this.sleep = function() {
		if (_this.is_alive()) {
			//_this.update_state_script();
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
		// it seems like we could use _this.url here instead
		var default_dir = jmolEvaluate("x", _this.suffix);

		var stateStr = "#a comment to guarrantee one line\n";
		stateStr += jmolGetPropertyAsString("stateInfo", "", _this.suffix);
		var re_modelinline = /data "model list"(.|\n|\r)*end "model list"/;
		if(stateStr.match(re_modelinline)) {
			//If we didn't get a good response we'll ignore and get later
			var modelStr = (stateStr.match(re_modelinline))[0];
			modelStr = modelStr.replace(/\r\n/g,'|').replace(/\r/g, '|').replace(/\n/g,'|').replace(/\|\|/g, '|');
			modelStr = 'fix between here ' + modelStr + ' and here';
			stateStr = stateStr.replace(re_modelinline, modelStr);
		}

		_this.state_script = 'set defaultdirectory=\"' + default_dir +'\";\n' + stateStr;
	};
	_this.popup = function() {
		_this.sleep();
		var win = window.open("", "jmol viewer", "width=600,height=600,resizable=1,statusbar=0");
		win.document.body.innerHTML = "";
		win.document.title = "Sage 3d Viewer";
		// win.document.writeln("<h1 align=center>Sage 3d Viewer</h1>");
		jmolSetDocument(win.document);
		jmolApplet("100%", _this.get_state_script(), _this.suffix);
		win.focus();
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