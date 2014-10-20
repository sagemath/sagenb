

SageJmolManager = function() {
    this._count = 0;
    this._applets = {};  
    this._lru_names = [];      // most recently used (uncovered) applet name
    this._limit = 3;           // allow at most this many active jmols.
    if (typeof(Jmol) !== 'undefined') {
        this._prepare_jmol();
        this._watcher = setInterval(this.activator.bind(this), 500);
    }
};

SageJmolManager.prototype._prepare_jmol = function() {
    // Turn off the JSmolCore.js: synchronous binary file transfer is
    // requested but not available" warning
    Jmol._alertNoBinary = false;
};


SageJmolManager.prototype.default_info = function() {
    // Before adding anything here make sure it is not overwritten in
    // add_applet()
    return {
        // actual size is controlled by the parent <div id='#sage_jmol_N'>
        width: "95%", //This allows the jquery resize to work do not set to 100%
        height: "95%",
        // debug=true will pop up alert boxes
        debug: false,
        color: "white",
        addSelectionOptions: false,
        use: "HTML5 WebGL Java", //This should probably only be HTML5
        // Tooltip when the mouse is over the static image
        coverTitle: 
            'Click on 3-D image to make it live. ' + 
            'Right-click on live image for a control menu.',
        deferApplet: true,                  // wait to load applet until click
        deferUncover: true,                 // wait to uncover applet until script completed
        //The paths below assume your server is set up with standard JSmol directory.  If not
        //they will need modification for the page to work.
        jarPath: "/jsmol/java", //path to applet .jar files on server.
        j2sPath: "/jsmol/j2s",//path to javascript version.
        makeLiveImg:"/jsmol/j2s/img/play_make_live.jpg",  //path to activate 3-D image.
        jarFile: "JmolAppletSigned0.jar",
        isSigned: true,
        //disableJ2SLoadMonitor: true,
        disableInitialConsole: true,
        script: "",
        z: 5,
        zIndexBase: 5,
        menuFile: "/java/jmol/appletweb/SageMenu.mnu", //special sagemenu
        //platformSpeed: 6, does not work have to do it in the ready function
    };
};

SageJmolManager.prototype.ready_callback = function (name, applet) {
    console.log('Jmol applet has launched ' + name);
    this._applets[name] = applet;
    this._lru_names.push(name);
    Jmol.script(applet, "set platformSpeed 6;");
    this.enforce_limit();
    jQuery('#'+name).parent().append('<div id="'+name+'_hint">Right-click to get options menu.</div>');
};

// Get the most recently used applet names
/* Remove duplicate and stale applet names from this._lru_names as a
 * side effect
 */
SageJmolManager.prototype.most_recently_used = function () {
    var result = [];
    for (i = this._lru_names.length-1; i >= 0; i--) {
        var name = this._lru_names[i];
        if (result.indexOf(name) >= 0)
            continue;
        if (name in this._applets)
            result.push(name);
    }
    result.reverse();
    this._lru_names = result;
    return result;
};

// Make sure that there are not too many active applets
SageJmolManager.prototype.enforce_limit = function() {
    var applet_names = this.most_recently_used();
    for (i = 0; i < applet_names.length - this._limit; i++) {
        var name = applet_names[i];
        var applet = this._applets[name];
        console.log('Covening applet ' + name);
        Jmol.coverApplet(applet, true);
        jQuery('#'+name+'_hint').remove();
    }
};


SageJmolManager.prototype.add_applet = 
    function (size, image, script, server_url, cell_num) 
{
    // The id of the container div holding the applet html, use this
    // to query the dom later to see if the applet is stil there.
    var applet_name = 'jmolApplet' + this._count;
    var info = this.default_info();
    info.coverImage = image;
    info.script = 'script ' + script;
    info.serverURL = server_url;
    info.readyFunction = this.ready_callback.bind(this, applet_name);
    var live_3d = jQuery('#3D_check').prop('checked');
    info.deferUncover = !live_3d;
    info.deferApplet = !live_3d;
    var use_java=$('#3D_use_java').prop('checked');
    if (use_java) {info.use='JAVA';}

    // append container to dom
    jQuery('#sage_jmol_' + cell_num).append(
        '<div id="'+applet_name+'" style="height:'+size+'px; width:'+size+'px;" ></div>');
    //make resizable
    $('#'+applet_name).resizable({aspectRatio:true});
    $('#'+applet_name).append('<div id="'+applet_name+'_wrapper" style="height:100%;width:100%;"> JSmol Here</div>');
   // launching JSmol/Jmol applet
    Jmol.setDocument(false); // manually insert Jmol.getAppletHtml
    jQuery('#' + applet_name+'_wrapper').html( Jmol.getAppletHtml(applet_name, info));

    // Finished
    this._count += 1;
};

// Callback for Action -> Delete all Output
SageJmolManager.prototype.delete_all_callback = function() {
    // console.log('jmol: delete_all');
    this.delete_callback();
};

// Callback for deleting single cell (may not contain jmol)
SageJmolManager.prototype.delete_callback = function() {
    // console.log('jmol: delete_check');
    var applet_names = Object.keys(this._applets);
    for (i = 0; i < applet_names.length; i++) {
        var name = applet_names[i];
        if (jQuery('#' + name).length === 0)
            delete this._applets[name];
    }
};

SageJmolManager.prototype.activator = function () {
    if (document.getElementById("loadJmol")) {
        var parentdiv = jQuery("#loadJmol").parent();
        // This div contains the ID number
        var cell_num = parentdiv.children("#loadJmol").html();
        parentdiv.children("#loadJmol").remove();
        var size = parentdiv.children("#sage_jmol_size_"+cell_num).html();
        var img = parentdiv.children("#sage_jmol_img_"+cell_num).html();
        var script = parentdiv.children("#sage_jmol_script_"+cell_num).html();
        var server_url = parentdiv.children("#sage_jmol_server_url_"+cell_num).html();
        sage_jmol.add_applet(size, img, script, server_url, cell_num);
        parentdiv.children("#sage_jmol_status_"+cell_num).html("Activated");
    }
};


sage_jmol = new SageJmolManager();
