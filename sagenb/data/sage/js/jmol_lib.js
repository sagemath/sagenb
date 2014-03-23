/*This is a very vanilla script to get Jmol/JSmol working in Sage again.  I
  have removed all the controls and the automatic sleeping that avoided
  memory overload of web browsers.
  Jonathan Gutow <gutow@uwosh.edu> February 2014 
*/

//This probably needs to be in header of pages that might use jmol
//Jmol.setDocument(document);  //will try in jmol_applet code.

var jmolApplet; //our generic viewer.

var live_3D_state = false;

var jmolInfo = { //default values
    width: "100%",
    height: "100%",
    debug: false,
    color: "white",
    addSelectionOptions: false,
    serverURL: "http://chemapps.stolaf.edu/jmol/jsmol/php/jsmol.php", //you can change this to your own server.
    use: "HTML5",
    coverImage: "/jsmol/j2s/img/play_make_live.jpg", // initial image instead of applet
    coverScript: "",	// special script for click of cover image (otherwise equal to script)
    deferApplet: true,                  // wait to load applet until click
    deferUncover: true,                 // wait to uncover applet until script completed
    //The paths below assume your server is set up with standard JSmol directory.  If not
    //they will need modification for the page to work.
    jarPath: "/jsmol/java", //path to applet .jar files on server.
    j2sPath: "/jsmol/j2s",//path to javascript version.
    makeLiveImg:"/jsmol/j2s/img/play_make_live.jpg",//path to activate 3-D image.
    jarFile: "JmolAppletSigned0.jar",
    isSigned: true,
    //disableJ2SLoadMonitor: true,
    disableInitialConsole: true,
    readyFunction:'',//jmol_isReady,
    script: ""
}

jmol_isReady = function(jmolApplet) {
	//TODO will need to activate widgets
 }
var jmol_count = 0;

var jmolStatus = {//most of these not used in the lightweight version, kept to make widgets easy to add back.
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
    jmolInfo: new Array(),
    }

//Some default constants
//applet sizes
var miniature = 100;
var small = 250;
var medium = 400;
var large = 600;

//Check whether to load 3-D live
live_3D_state = $('#3D_check').prop('checked');
//start the watch function
jmolWatcher = setInterval('jmolActivator();',500);

function jmol_applet(size, image, url, cell_num, functionnames) { //makes a new applet. 
    var appletID = jmol_count;
    jmol_count = jmol_count + 1;
    jmolStatus.jmolArray[appletID] = 3; //queued to load.
    if (size==500){
        size = medium; //set to medium size otherwise we will keep other sizes.
        }
    Jmol.setDocument(document);
    //Where am I?  Need to know in cases where I need to write directly to this cell.
    cell_ID = 'sage_jmol'+cell_num;
    jmolStatus.jmolInfo[appletID] = jmolInfo; //set default values
    jmolStatus.jmolInfo[appletID].coverImage = image; //this should be the image url
    jmolStatus.jmolInfo[appletID].script = "script "+url; //this should be the script url
    //Check whether to load 3-D live
    live_3D_state = $('#3D_check').prop('checked');    
    if (live_3D_state){
       jmolStatus.jmolInfo[appletID].deferApplet=false;
       }
    jmolDivStr = "jmol"+appletID;
    jmolStatus.widths[appletID] = size;
    jmolStatus.heights[appletID]= size;
    //appending to cell_ID
    $('#'+cell_ID).append('<div id="'+jmolDivStr+'" style="height:'+size+'px; width:'+size+'px;" >JSmol here</div>');
    //launching JSmol/Jmol applet
    $('#'+jmolDivStr).html(Jmol.getAppletHtml("jmolApplet"+appletID,jmolStatus.jmolInfo[appletID])); 
    //we will still set all the data for this applet so that other asynchronously created applets do not grab its ID.
    jmolStatus.signed[appletID]=jmolStatus.loadSigned;
    jmolStatus.urls[appletID]=url;
    //    jmolStatus.numLive = jmolStatus.numLive+1;
    //jmolStatus.controlStrs[appletID] = controlStr;
    //jmolStatus.captionStrs[appletID] = captionStr;
    //jmolStatus.cntrls[appletID]=cntrlPanels;
//Now we wait for the server by calling a function that waits if the div is not yet written.
//    launchNewJmol(size,scriptStr,appletID);
    return jmolDivStr;//for historical compatibility
    }

function jmolActivator(){
    if (document.getElementById("loadJmol")){
        parentdiv = $("#loadJmol").parent();
        //parentid = $(parentdiv).attr("id");
        //alert("The parent id is:"+parentid);
        cell_num = $(parentdiv).children("#loadJmol").html();//this div must have the ID number
        //alert("Trying to launch JSmol #"+cell_num);
        $(parentdiv).children("#loadJmol").remove();
        size = $(parentdiv).children("#sage_jmol_size"+cell_num).html();
        img = $(parentdiv).children("#sage_jmol_img"+cell_num).html();
        script = $(parentdiv).children("#sage_jmol_script"+cell_num).html();
        tmpdiv = jmol_applet(size, img, script, cell_num);
        $(parentdiv).children("#sage_jmol_status"+cell_num).html() = "Activated";
    }
}

function live_3D_check(s) {
    /*
    Send a message back to the server either turn live_3D on of off.
    INPUT:
        s -- boolean; whether the pretty print box is checked.
    */
    live_3D_state =s;
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
