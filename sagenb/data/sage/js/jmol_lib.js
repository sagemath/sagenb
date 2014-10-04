/*This is a very vanilla script to get Jmol/JSmol working in Sage again.  I
  have removed all the controls and the automatic sleeping that avoided
  memory overload of web browsers.
  Jonathan Gutow <gutow@uwosh.edu> February 2014 
*/

// Turn off the JSmolCore.js: synchronous binary file transfer is
// requested but not available" warning
Jmol._alertNoBinary = false

jmol_isReady = function(jmolApplet) {
    console.log('Jmol is ready');
    Jmol.script(jmolApplet, "set platformSpeed 6;");
    //alert("Applet: "+jmolApplet+" has launched.");
}

var jmolInfo = { //default values
    width: "100%",
    height: "100%",
    // debug=true will pop up alert boxes
    debug: false,
    color: "white",
    addSelectionOptions: false,
    use: "HTML5 WebGL Java",
    // Tooltip when the mouse is over the static image
    coverTitle: 'Click on 3-D image to make it live.  Right-click on live image for a control menu.',
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
    readyFunction: jmol_isReady,
    script: "",
    z: 5,
    zIndexBase: 5,
    menuFile: "/jsmol/appletweb/SageMenu.mnu", //special sagemenu
    platformSpeed: 6,
}

var jmol_count = 0;

jmolStatus = {//most of these not used in the lightweight version, kept to make widgets easy to add back.
    maxLiveAllowed: 4,
    numLive: 0,
    loadSigned: false, //when set to true will load signed applets.
    signed: new Array(), //false for unsigned applets, true for signed applets.
    jmolArray: new Array(),//-2 loading failed, -1 deleted, 0 awake, 1 sleeping, 2 loading, 3 waiting to load.
    urls: new Array(),
    defaultdirectory: new Array(),
    widths: new Array(),
    heights: new Array(),
    controlStrs: new Array(),
    captionStrs: new Array(),
    pictureStrs: new Array(),
    stateScripts: new Array(),
    cntrls: new Array(),
    attempts: new Array(),
    jmolInfo: new Object(),
}

//Some default constants
//applet sizes
var miniature = 100;
var small = 250;
var medium = 500;
var large = 800;

//Check whether to load 3-D live
//live_3D_state = $('#3D_check').prop('checked');
//start the watch function
jmolWatcher = setInterval('jmolActivator();',500);

// makes a new applet and puts it into the dom
function make_jmol_applet(size, image, script, server_url, cell_num, functionnames) {
    var appletID = jmol_count;
    jmol_count = jmol_count + 1;
    jmolStatus.jmolArray[appletID] = 3; //queued to load.
    if (size == 500)
        size = medium; // set to medium size otherwise we will keep other sizes.
    Jmol.setDocument(false); // manually insert Jmol.getAppletHtml later
    jmolStatus.jmolInfo[appletID] = jQuery.extend({}, jmolInfo); // shallow copy default values
    jmolStatus.jmolInfo[appletID].coverImage = image; //this should be the image url
    jmolStatus.jmolInfo[appletID].script = "script "+script; //this should be the script name
    jmolStatus.jmolInfo[appletID].serverURL = server_url;
    // jmolStatus.jmolInfo[appletID].deferApplet = jQuery('#3D_check').prop('checked');
    jmolDivStr = "jmol"+appletID;
    jmolStatus.widths[appletID] = size;
    jmolStatus.heights[appletID]= size;
    // appending to cell_ID
    var cell_ID = 'sage_jmol_' + cell_num;
    // $('#'+cell_ID).append('<span></span>');
    $('#'+cell_ID).append('<div id="'+jmolDivStr+'" style="height:'+size+'px; width:'+size+'px;" >JSmol here</div>');
    // launching JSmol/Jmol applet
    var applet_html = Jmol.getAppletHtml("jmolApplet"+appletID, jmolStatus.jmolInfo[appletID]);
    $('#'+jmolDivStr).html(applet_html);
    // we will still set all the data for this applet so that other asynchronously created applets do not grab its ID.
    jmolStatus.signed[appletID] = jmolStatus.loadSigned;
    return jmolDivStr;//for historical compatibility
}

function jmolActivator(){
    if (document.getElementById("loadJmol")){
        var parentdiv = jQuery("#loadJmol").parent();
        // This div contains the ID number
        var cell_num = parentdiv.children("#loadJmol").html();
        parentdiv.children("#loadJmol").remove();
        var size = parentdiv.children("#sage_jmol_size_"+cell_num).html();
        var img = parentdiv.children("#sage_jmol_img_"+cell_num).html();
        var script = parentdiv.children("#sage_jmol_script_"+cell_num).html();
        var server_url = parentdiv.children("#sage_jmol_server_url_"+cell_num).html();
        make_jmol_applet(size, img, script, server_url, cell_num);
        parentdiv.children("#sage_jmol_status_"+cell_num).html("Activated");
    }
}

function live_3D_check(s) {
    /*
    Send a message back to the server either turn live_3D on of off.
    INPUT:
        s -- boolean; whether the live 3D box is checked.
    */
    var live_3D_state = s;
    //alert ('live_3D_state:'+live_3D_state);
    async_request(worksheet_command('live_3D/' + s));
}

//The following two delete functions do not do anything in this truncated jmol_lib.
//They are for compatibility with the notebook_lib.js
function jmol_delete_all_output() {
    //called by the delete_all_output function of the notebook to get jmol parameters cleaned up.
    jmol_count=0;
    jmolStatus.numLive=0;
    jmolStatus.jmolArray=new Array();
}

function jmol_delete_check() {
    //called when cells are evaluated to see if any jmols have been deleted.  If so update their status.
    liveCount = jmolStatus.jmolArray.length;
    for ( k = 0; k< liveCount; k++) {
        testId= 'Jmol_Table_Jmol'+k; //looking for the whole table Jmol is in, since if the table is there it is sleeping.
        if (!get_element(testId)) { //we need to set this as deleted and maybe free up the ID?
            jmolStatus.jmolArray[k] = -1;
            //for the time being old IDs will not be reused.  Shouldn't be real big problem as completely resets
            //each time a page is opened.
        }
    }
    //jmol_numLiveUpdate();
}
