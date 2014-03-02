/*This is a very vanilla script to get Jmol/JSmol working in Sage again.  I
  have removed all the controls and the automatic sleeping that avoided
  memory overload of web browsers.
  Jonathan Gutow <gutow@uwosh.edu> February 2014 
*/

//This probably needs to be in header of pages that might use jmol
//Jmol.setDocument(document);  //will try in jmol_applet code.

var jmolApplet; //our generic viewer.

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

function jmol_applet(size, image, url, cell_num, functionnames) { //makes a new applet. 
    var appletID = jmol_count;
    jmol_count = jmol_count + 1;
    jmolStatus.jmolArray[appletID] = 3; //queued to load.
    if (size==500){
        size = medium; //set to medium size otherwise we will keep other sizes.
        }
    Jmol.setDocument(document);
    //Where am I?  Need to know in cases where I need to write directly to this cell.
    cell_ID = 'cell_output_html_'+cell_num;
    //however, I might be inside something else like an interact as well...so
    parent = get_element('jmol_static'+cell_num).parentNode;
    jmolStatus.jmolInfo[appletID] = jmolInfo; //set default values
    jmolStatus.jmolInfo[appletID].coverImage = image; //this should be the image url
    jmolStatus.jmolInfo[appletID].script = "script "+url; //this should be the script url
    parentStr = parent.innerHTML;
    //str = parentStr + newJmolTableStr(appletID, size, size, url, wakeMessage, sleepMessage, captionStr, controlStr);
    //str = parentStr + '<script>Jmol.getAppletHtml("jmolApplet'+appletID+'",jmolStatus.jmolInfo['+appletID+']))</script>';
    jmolDivStr = "jmol"+appletID;
    jmolStatus.widths[appletID] = size;
    jmolStatus.heights[appletID]= size;
   $(parent).append('<div id="'+jmolDivStr+'" style="height:'+size+'px; width:'+size+'px;" >JSmol here</div>');
    $('#'+jmolDivStr).html(Jmol.getAppletHtml("jmolApplet"+appletID,jmolStatus.jmolInfo[appletID])); 
    //add debugging div
    //str += '<div id="JmolDebug">Jmol Debugging goes here</div>';
    //now we can start the new one
    //cell_writer.write(str);
    parent.innerHTML = str;
    //jmolSetAppletColor("white");
    //if (appletID==0){
    //    jmol_checkbrowserOS();
     //   }
    //we will still set all the data for this applet so that other asynchronously created applets do not grab its ID.
    jmolStatus.signed[appletID]=jmolStatus.loadSigned;
    jmolStatus.urls[appletID]=url;
    //    jmolStatus.numLive = jmolStatus.numLive+1;
    jmolStatus.controlStrs[appletID] = controlStr;
    jmolStatus.captionStrs[appletID] = captionStr;
    jmolStatus.cntrls[appletID]=cntrlPanels;
//Now we wait for the server by calling a function that waits if the div is not yet written.
//    launchNewJmol(size,scriptStr,appletID);
    return str;
    }
