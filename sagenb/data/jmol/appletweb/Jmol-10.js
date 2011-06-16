/* $RCSfile$
 * $Author: hansonr $
 * $Date: 2006-09-14 19:13:51 +0200 (jeu., 14 sept. 2006) $
 * $Revision: 5543 $
 *
 * Copyright (C) 2004-2005  Miguel, Jmol Development, www.jmol.org
 *
 * Contact: miguel@jmol.org
 *
 *  This library is free software; you can redistribute it and/or
 *  modify it under the terms of the GNU Lesser General Public
 *  License as published by the Free Software Foundation; either
 *  version 2.1 of the License, or (at your option) any later version.
 *
 *  This library is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 *  Lesser General Public License for more details.
 *
 *  You should have received a copy of the GNU Lesser General Public
 *  License along with this library; if not, write to the Free Software
 *  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
 *  02111-1307  USA.
 */

// for documentation see www.jmol.org/jslibrary

var undefined; // for IE 5 ... wherein undefined is undefined

////////////////////////////////////////////////////////////////
// Basic Scripting infrastruture
////////////////////////////////////////////////////////////////

function jmolInitialize(codebaseDirectory, useSignedApplet) {
  if (_jmol.initialized) {
    alert("jmolInitialize() should only be called *ONCE* within a page");
    return;
  }
  if (! codebaseDirectory) {
    alert("codebaseDirectory is a required parameter to jmolInitialize");
    codebaseDirectory = ".";
  }
  if (codebaseDirectory.indexOf("http://") == 0 ||
      codebaseDirectory.indexOf("https://") == 0)
    alert("An absolute URL is not recommended for codebaseDirectory.\n" +
	  "A directory or docroot relative reference is recommended.\n\n" +
	  "If you are experienced enough to go 'off piste' then you\n" +
	  "can override this warning by inserting a space before\n" +
	  "http in your URL.");
  _jmolSetCodebase(codebaseDirectory);
  _jmolUseSignedApplet(useSignedApplet);
  _jmolOnloadResetForms();
  _jmol.initialized = true;
}

function jmolSetDocument(doc) {
  _jmol.currentDocument = doc;
}

function jmolSetAppletColor(boxbgcolor, boxfgcolor, progresscolor) {
  _jmolInitCheck();
  _jmol.boxbgcolor = boxbgcolor;
  if (boxfgcolor)
    _jmol.boxfgcolor = boxfgcolor
  else if (boxbgcolor == "white" || boxbgcolor == "#FFFFFF")
    _jmol.boxfgcolor = "black";
  else
    _jmol.boxfgcolor = "white";
  if (progresscolor)
    _jmol.progresscolor = progresscolor;
  if (_jmol.debugAlert)
    alert(" boxbgcolor=" + _jmol.boxbgcolor +
          " boxfgcolor=" + _jmol.boxfgcolor +
          " progresscolor=" + _jmol.progresscolor);
}

function jmolApplet(size, script, nameSuffix) {
  _jmolInitCheck();
  return _jmolApplet(size, null, script, nameSuffix);
}

////////////////////////////////////////////////////////////////
// Basic controls
////////////////////////////////////////////////////////////////

function jmolButton(script, label, id) {
  _jmolInitCheck();
  if (id == undefined || id == null)
    id = "jmolButton" + _jmol.buttonCount;
  if (label == undefined || label == null)
    label = script.substring(0, 32);
  ++_jmol.buttonCount;
  var scriptIndex = _jmolAddScript(script);
  var t = "<input type='button' name='" + id + "' id='" + id +
          "' value='" + label +
          "' onClick='_jmolClick(" + scriptIndex + _jmol.targetText +
          ")' onMouseover='_jmolMouseOver(" + scriptIndex +
          ");return true' onMouseout='_jmolMouseOut()' " +
          _jmol.buttonCssText + "/>";
  if (_jmol.debugAlert)
    alert(t);
  return _jmolDocumentWrite(t);
}

function jmolCheckbox(scriptWhenChecked, scriptWhenUnchecked,
                      labelHtml, isChecked, id) {
  _jmolInitCheck();
  if (id == undefined || id == null)
    id = "jmolCheckbox" + _jmol.checkboxCount;
  ++_jmol.checkboxCount;
  if (scriptWhenChecked == undefined || scriptWhenChecked == null ||
      scriptWhenUnchecked == undefined || scriptWhenUnchecked == null) {
    alert("jmolCheckbox requires two scripts");
    return;
  }
  if (labelHtml == undefined || labelHtml == null) {
    alert("jmolCheckbox requires a label");
    return;
  }
  var indexChecked = _jmolAddScript(scriptWhenChecked);
  var indexUnchecked = _jmolAddScript(scriptWhenUnchecked);
  var t = "<input type='checkbox' name='" + id + "' id='" + id +
          "' onClick='_jmolCbClick(this," +
          indexChecked + "," + indexUnchecked + _jmol.targetText +
          ")' onMouseover='_jmolCbOver(this," + indexChecked + "," +
          indexUnchecked +
          ");return true' onMouseout='_jmolMouseOut()' " +
	  (isChecked ? "checked " : "") + _jmol.checkboxCssText + "/>" +
          labelHtml;
  if (_jmol.debugAlert)
    alert(t);
  return _jmolDocumentWrite(t);
}

function jmolRadioGroup(arrayOfRadioButtons, separatorHtml, groupName) {
  _jmolInitCheck();
  var type = typeof arrayOfRadioButtons;
  if (type != "object" || type == null || ! arrayOfRadioButtons.length) {
    alert("invalid arrayOfRadioButtons");
    return;
  }
  if (separatorHtml == undefined || separatorHtml == null)
    separatorHtml = "&nbsp; ";
  var length = arrayOfRadioButtons.length;
  var t = "";
  jmolStartNewRadioGroup();
  for (var i = 0; i < length; ++i) {
    var radio = arrayOfRadioButtons[i];
    type = typeof radio;
    if (type == "object") {
      t += _jmolRadio(radio[0], radio[1], radio[2], separatorHtml, groupName);
    } else {
      t += _jmolRadio(radio, null, null, separatorHtml, groupName);
    }
  }
  if (_jmol.debugAlert)
    alert(t);
  return _jmolDocumentWrite(t);
}

function jmolLink(script, label, id) {
  _jmolInitCheck();
  if (id == undefined || id == null)
    id = "jmolLink" + _jmol.linkCount;
  if (label == undefined || label == null)
    label = script.substring(0, 32);
  ++_jmol.linkCount;
  var scriptIndex = _jmolAddScript(script);
  var t = "<a name='" + id + "' id='" + id + 
          "' href='javascript:_jmolClick(" + scriptIndex +
          _jmol.targetText +
          ");' onMouseover='_jmolMouseOver(" + scriptIndex +
          ");return true;' onMouseout='_jmolMouseOut()' " +
          _jmol.linkCssText + ">" + label + "</a>";
  if (_jmol.debugAlert)
    alert(t);
  return _jmolDocumentWrite(t);
}

function jmolMenu(arrayOfMenuItems, size, id) {
  _jmolInitCheck();
  if (id == undefined || id == null)
    id = "jmolMenu" + _jmol.menuCount;
  ++_jmol.menuCount;
  var type = typeof arrayOfMenuItems;
  if (type != null && type == "object" && arrayOfMenuItems.length) {
    var length = arrayOfMenuItems.length;
    if (typeof size != "number" || size == 1)
      size = null;
    else if (size < 0)
      size = length;
    var sizeText = size ? " size='" + size + "' " : "";
    var t = "<select name='" + id + "' id='" + id +
            "' onChange='_jmolMenuSelected(this" +
            _jmol.targetText + ")'" +
            sizeText + _jmol.menuCssText + ">";
    for (var i = 0; i < length; ++i) {
      var menuItem = arrayOfMenuItems[i];
      type = typeof menuItem;
      var script, text;
      var isSelected = undefined;
      if (type == "object" && menuItem != null) {
        script = menuItem[0];
        text = menuItem[1];
        isSelected = menuItem[2];
      } else {
        script = text = menuItem;
      }
      if (text == undefined || text == null)
        text = script;
      var scriptIndex = _jmolAddScript(script);
      var selectedText = isSelected ? "' selected>" : "'>";
      t += "<option value='" + scriptIndex + selectedText + text + "</option>";
    }
    t += "</select>";
    if (_jmol.debugAlert)
      alert(t);
    return _jmolDocumentWrite(t);
  }
}

function jmolHtml(html) {
  return _jmolDocumentWrite(html);
}

function jmolBr() {
  return _jmolDocumentWrite("<br />");
}

////////////////////////////////////////////////////////////////
// advanced scripting functions
////////////////////////////////////////////////////////////////

function jmolDebugAlert(enableAlerts) {
  _jmol.debugAlert = (enableAlerts == undefined || enableAlerts)
}

function jmolAppletInline(size, inlineModel, script, nameSuffix) {
  return _jmolApplet(size, _jmolSterilizeInline(inlineModel),
                     script, nameSuffix);
}

function jmolSetTarget(targetSuffix) {
  _jmol.targetSuffix = targetSuffix;
  _jmol.targetText = targetSuffix ? ",\"" + targetSuffix + "\"" : "";
}

function jmolScript(script, targetSuffix) {
  if (script) {
    _jmolCheckBrowser();
    if (targetSuffix == "all") {
      with (_jmol) {
	for (var i = 0; i < appletSuffixes.length; ++i) {
	  var target = "jmolApplet" + appletSuffixes[i];
          var applet = _jmolFindApplet(target);
          if (applet)
            applet.script(script);
          else
            alert("could not find applet " + target);
        }
      }
    } else {
      var target = "jmolApplet" + (targetSuffix ? targetSuffix : "0");
      var applet = _jmolFindApplet(target);
      if (applet)
        return applet.script(script);
      else
        alert("could not find applet " + target);
    }
  }
}

function jmolLoadInline(model, targetSuffix) {
  if (model) {
    var target = "jmolApplet" + (targetSuffix ? targetSuffix : "0");
//    while (! _jmol.ready[target])
//      alert("The Jmol applet " + target + " is not loaded yet");
//    if (! _jmol.ready[target])
//      alert("The Jmol applet " + target + " is not loaded yet");
//    if (document.applets[target] && ! document.applets[target].isActive())
//       alert("The Jmol applet " + target + " is not yet active");
//    else {
      var applet = _jmolFindApplet(target);
      if (applet)
        return applet.loadInline(model);
      else
        alert("could not find applet " + target);
//    }
  }
}

function jmolStartNewRadioGroup() {
  ++_jmol.radioGroupCount;
}

function jmolRadio(script, labelHtml, isChecked, separatorHtml, groupName) {
  _jmolInitCheck();
  if (_jmol.radioGroupCount == 0)
    ++_jmol.radioGroupCount;
  var t = _jmolRadio(script, labelHtml, isChecked, separatorHtml, groupName);
  if (_jmol.debugAlert)
    alert(t);
  return _jmolDocumentWrite(t);
}

function jmolCheckBrowser(action, urlOrMessage, nowOrLater) {
  if (typeof action == "string") {
    action = action.toLowerCase();
    if (action != "alert" && action != "redirect" && action != "popup")
      action = null;
  }
  if (typeof action != "string")
    alert("jmolCheckBrowser(action, urlOrMessage, nowOrLater)\n\n" +
          "action must be 'alert', 'redirect', or 'popup'");
  else {
    if (typeof urlOrMessage != "string")
      alert("jmolCheckBrowser(action, urlOrMessage, nowOrLater)\n\n" +
            "urlOrMessage must be a string");
    else {
      _jmol.checkBrowserAction = action;
      _jmol.checkBrowserUrlOrMessage = urlOrMessage;
    }
  }
  if (typeof nowOrLater == "string" && nowOrLater.toLowerCase() == "now")
    _jmolCheckBrowser();
}

function _jmolDocumentWrite(text) {
  if (_jmol.currentDocument)
    _jmol.currentDocument.write(text);
  return text;
}

////////////////////////////////////////////////////////////////
// Cascading Style Sheet Class support
////////////////////////////////////////////////////////////////

function jmolSetAppletCssClass(appletCssClass) {
  if (_jmol.hasGetElementById) {
    _jmol.appletCssClass = appletCssClass;
    _jmol.appletCssText = appletCssClass ? "class='" + appletCssClass + "' " : "";
  }
}

function jmolSetButtonCssClass(buttonCssClass) {
  if (_jmol.hasGetElementById) {
    _jmol.buttonCssClass = buttonCssClass;
    _jmol.buttonCssText = buttonCssClass ? "class='" + buttonCssClass + "' " : "";
  }
}

function jmolSetCheckboxCssClass(checkboxCssClass) {
  if (_jmol.hasGetElementById) {
    _jmol.checkboxCssClass = checkboxCssClass;
    _jmol.checkboxCssText = checkboxCssClass ? "class='" + checkboxCssClass + "' " : "";
  }
}

function jmolSetRadioCssClass(radioCssClass) {
  if (_jmol.hasGetElementById) {
    _jmol.radioCssClass = radioCssClass;
    _jmol.radioCssText = radioCssClass ? "class='" + radioCssClass + "' " : "";
  }
}

function jmolSetLinkCssClass(linkCssClass) {
  if (_jmol.hasGetElementById) {
    _jmol.linkCssClass = linkCssClass;
    _jmol.linkCssText = linkCssClass ? "class='" + linkCssClass + "' " : "";
  }
}

function jmolSetMenuCssClass(menuCssClass) {
  if (_jmol.hasGetElementById) {
    _jmol.menuCssClass = menuCssClass;
    _jmol.menuCssText = menuCssClass ? "class='" + menuCssClass + "' " : "";
  }
}

////////////////////////////////////////////////////////////////
// functions for INTERNAL USE ONLY which are subject to change
// use at your own risk ... you have been WARNED!
////////////////////////////////////////////////////////////////

var _jmol = {
  currentDocument: document,

  debugAlert: false,
  bgcolor: "black",
  progresscolor: "blue",
  boxbgcolor: "black",
  boxfgcolor: "white",
  boxmessage: "Downloading JmolApplet ...",
  
  codebase: ".",
  modelbase: ".",
  
  appletCount: 0,
  appletSuffixes: [],
  
  buttonCount: 0,
  checkboxCount: 0,
  linkCount: 0,
  menuCount: 0,
  radioCount: 0,
  radioGroupCount: 0,
  
  appletCssClass: null,
  appletCssText: "",
  buttonCssClass: null,
  buttonCssText: "",
  checkboxCssClass: null,
  checkboxCssText: "",
  radioCssClass: null,
  radioCssText: "",
  linkCssClass: null,
  linkCssText: "",
  menuCssClass: null,
  menuCssText: "",
  
  targetSuffix: 0,
  targetText: "",
  scripts: [""],
  
  ua: navigator.userAgent.toLowerCase(),
  uaVersion: parseFloat(navigator.appVersion),
  
  os: "unknown",
  browser: "unknown",
  browserVersion: 0,
  hasGetElementById: !!document.getElementById,
  isJavaEnabled: navigator.javaEnabled(),
  isNetscape47Win: false,
  isIEWin: false,
  useIEObject: false,
  useHtml4Object: false,
  
  windowsClassId: "clsid:8AD9C840-044E-11D1-B3E9-00805F499D93",
  windowsCabUrl:
   "http://java.sun.com/update/1.5.0/jinstall-1_5_0_07-windows-i586.cab",

  isBrowserCompliant: false,
  isJavaCompliant: false,
  isFullyCompliant: false,

  initialized: false,
  initChecked: false,
  
  browserChecked: false,
  checkBrowserAction: "alert",
  checkBrowserUrlOrMessage: null,

  archivePath: null, // JmolApplet0.jar OR JmolAppletSigned0.jar

  previousOnloadHandler: null,
  ready: {}
}

with (_jmol) {

  function _jmolTestUA(candidate) {
    var ua = _jmol.ua;
    var index = ua.indexOf(candidate);
    if (index < 0)
      return false;
    _jmol.browser = candidate;
    _jmol.browserVersion = parseFloat(ua.substring(index+candidate.length+1));
    return true;
  }
  
  function _jmolTestOS(candidate) {
    if (_jmol.ua.indexOf(candidate) < 0)
      return false;
    _jmol.os = candidate;
    return true;
  }
  
  _jmolTestUA("konqueror") ||
  _jmolTestUA("safari") ||
  _jmolTestUA("omniweb") ||
  _jmolTestUA("opera") ||
  _jmolTestUA("webtv") ||
  _jmolTestUA("icab") ||
  _jmolTestUA("msie") ||
  (_jmol.ua.indexOf("compatible") < 0 && _jmolTestUA("mozilla"));
  
  _jmolTestOS("linux") ||
  _jmolTestOS("unix") ||
  _jmolTestOS("mac") ||
  _jmolTestOS("win");

  isNetscape47Win = (os == "win" && browser == "mozilla" &&
                     browserVersion >= 4.78 && browserVersion <= 4.8);

  if (os == "win") {
    isBrowserCompliant = hasGetElementById;
  } else if (os == "mac") { // mac is the problem child :-(
    if (browser == "mozilla" && browserVersion >= 5) {
      // miguel 2004 11 17
      // checking the plugins array does not work because
      // Netscape 7.2 OS X still has Java 1.3.1 listed even though
      // javaplugin.sf.net is installed to upgrade to 1.4.2
      eval("try {var v = java.lang.System.getProperty('java.version');" +
           " _jmol.isBrowserCompliant = v >= '1.4.2';" +
           " } catch (e) { }");
    } else if (browser == "opera" && browserVersion <= 7.54) {
      isBrowserCompliant = false;
    } else {
      isBrowserCompliant = hasGetElementById &&
        !((browser == "msie") ||
          (browser == "safari" && browserVersion < 125.12));
    }
  } else if (os == "linux" || os == "unix") {
    if (browser == "konqueror" && browserVersion <= 3.3)
      isBrowserCompliant = false;
    else
      isBrowserCompliant = hasGetElementById;
  } else { // other OS
    isBrowserCompliant = hasGetElementById;
  }

  // possibly more checks in the future for this
  isJavaCompliant = isJavaEnabled;

  isFullyCompliant = isBrowserCompliant && isJavaCompliant;

  // IE5.5 works just fine ... but let's push them to Sun Java
  isIEWin = (os == "win" && browser == "msie" && browserVersion >= 5.5);
  useIEObject = isIEWin;
  useHtml4Object =
   (os != "mac" && browser == "mozilla" && browserVersion >= 5) ||
   (os == "win" && browser == "opera" && browserVersion >= 8) ||
   (os == "mac" && browser == "safari" && browserVersion >= 412.2);
}

function _jmolUseSignedApplet(useSignedApplet) {
  _jmol.archivePath =
    (useSignedApplet ? "JmolAppletSigned" : "JmolApplet") + "0.jar";
}

function _jmolApplet(size, inlineModel, script, nameSuffix) {
  with (_jmol) {
    if (! nameSuffix)
      nameSuffix = appletCount;
    appletSuffixes.push(nameSuffix);
    ++appletCount;
    if (! script)
      script = "select *";
    var sz = _jmolGetAppletSize(size);
    var widthAndHeight = " width='" + sz[0] + "' height='" + sz[1] + "' ";

    var tHeader, tFooter;

    if (useIEObject) { // use MSFT IE6 object tag with .cab file reference
      var winCodebase = "";
      if (windowsCabUrl)
         winCodebase = " codebase='" + windowsCabUrl + "'\n";
      tHeader = 
        "<object name='jmolApplet" + nameSuffix +
        "' id='jmolApplet" + nameSuffix + "' " + appletCssText + "\n" +
	" classid='" + windowsClassId + "'\n" +
        winCodebase + widthAndHeight + ">\n" +
        "  <param name='code' value='JmolApplet' />\n" +
        "  <param name='archive' value='" + archivePath + "' />\n" +
        "  <param name='mayscript' value='true' />\n" +
        "  <param name='codebase' value='" + codebase + "' />\n";
      tFooter = "</object>";
    } else if (useHtml4Object) { // use HTML4 object tag
      tHeader = 
        "<object name='jmolApplet" + nameSuffix +
        "' id='jmolApplet" + nameSuffix + "' " + appletCssText + "\n" +
	" classid='java:JmolApplet'\n" +
        " type='application/x-java-applet'\n" +
        widthAndHeight + ">\n" +
        "  <param name='archive' value='" + archivePath + "' />\n" +
        "  <param name='mayscript' value='true' />\n" +
        "  <param name='codebase' value='" + codebase + "' />\n";
      tFooter = "</object>";
    } else { // use applet tag
      tHeader = 
        "<applet name='jmolApplet" + nameSuffix +
        "' id='jmolApplet" + nameSuffix +
        "' " + appletCssText +
        " code='JmolApplet'" +
        " archive='" + archivePath + "' codebase='" + codebase + "'\n" +
        " width='" + sz[0] + "' height='" + sz[1] +
        "' mayscript='true'>\n";
      tFooter = "</applet>";
    }
    var tParams =
      "  <param name='progressbar' value='true' />\n" +
      "  <param name='progresscolor' value='" +
      progresscolor + "' />\n" +
      "  <param name='boxmessage' value='" +
      boxmessage + "' />\n" +
      "  <param name='boxbgcolor' value='" +
      boxbgcolor + "' />\n" +
      "  <param name='boxfgcolor' value='" +
      boxfgcolor + "' />\n" +
      "  <param name='ReadyCallback' value='_jmolReadyCallback' />\n";
    
    if (inlineModel)
      tParams += "  <param name='loadInline' value='" + inlineModel + "' />\n";
    if (script)
      tParams += "  <param name='script' value='" +
                 _jmolSterilizeScript(script) + "' />\n";
    var visitJava;
    if (isIEWin || useHtml4Object) {
      visitJava =
        "<p style='background-color:yellow;" +
        "width:" + sz[0] + ";height:" + sz[1] + ";" + 
        // why doesn't this vertical-align work?
	"text-align:center;vertical-align:middle;'>\n" +
        "You do not have Java applets<br />\n" +
        "enabled in your web browser.<br />\n" +
        "Install the Java Runtime Environment<br />\n" +
        "from <a href='http://www.java.com'>www.java.com</a><br />" +
        "and/or enable Java applets in<br />\n" +
        "your web browser preferences." +
        "</p>";
    } else {
      visitJava =
        "<table bgcolor='yellow' width='" + sz[0] + "'><tr>" +
        "<td align='center' valign='middle' height='" + sz[1] + "'>\n" +
        "You do not have the<br />\n" +
        "Java Runtime Environment<br />\n" +
        "installed for applet support.<br />\n" +
        "Visit <a href='http://www.java.com'>www.java.com</a>" +
        "</td></tr></table>";
    }

    var t = tHeader + tParams + visitJava + tFooter;
    jmolSetTarget(nameSuffix);
    ready["jmolApplet" + nameSuffix] = false;
    if (_jmol.debugAlert)
      alert(t);
    return _jmolDocumentWrite(t);
  }
}

function _jmolInitCheck() {
  if (_jmol.initChecked)
    return;
  _jmol.initChecked = true;
  if (_jmol.initialized)
    return;
  alert("jmolInitialize({codebase}, {useSignedApplet})\n" +
        "  must be called before any other Jmol.js functions");
}

function _jmolCheckBrowser() {
  with (_jmol) {
    if (browserChecked)
      return;
    browserChecked = true;
  
    if (isFullyCompliant)
      return true;

    if (checkBrowserAction == "redirect")
      location.href = checkBrowserUrlOrMessage;
    else if (checkBrowserAction == "popup")
      _jmolPopup(checkBrowserUrlOrMessage);
    else {
      var msg = checkBrowserUrlOrMessage;
      if (msg == null)
        msg = "Your web browser is not fully compatible with Jmol\n\n" +
              "browser: " + browser +
              "   version: " + browserVersion +
              "   os: " + os +
              "\n\n" + ua;
      alert(msg);
    }
  }
  return false;
}

function _jmolPopup(url) {
  var popup = window.open(url, "JmolPopup",
                          "left=150,top=150,height=400,width=600," +
                          "directories=yes,location=yes,menubar=yes," +
                          "toolbar=yes," +
                          "resizable=yes,scrollbars=yes,status=yes");
  if (popup.focus)
    poup.focus();
}

function _jmolReadyCallback(name) {
  if (_jmol.debugAlert)
    alert(name + " is ready");
  _jmol.ready["" + name] = true;
}

function _jmolSterilizeScript(script) {
  var inlineScript = script.replace(/'/g, "&#39;");
  if (_jmol.debugAlert)
    alert("script:\n" + inlineScript);
  return inlineScript;
}

function _jmolSterilizeInline(model) {
  var inlineModel =
    model.replace(/\r|\n|\r\n/g, "|").replace(/'/g, "&#39;");
  if (_jmol.debugAlert)
    alert("inline model:\n" + inlineModel);
  return inlineModel;
}

function _jmolGetAppletSize(size) {
  var width, height;
  var type = typeof size;
  if (type == "number")
    width = height = size;
  else if (type == "object" && size != null) {
    width = size[0]; height = size[1];
  }
  if (! (width >= 25 && width <= 2000))
    width = 300;
  if (! (height >= 25 && height <= 2000))
    height = 300;
  return [width, height];
}

function _jmolRadio(script, labelHtml, isChecked, separatorHtml, groupName) {
  ++_jmol.radioCount;
  if (groupName == undefined || groupName == null)
    groupName = "jmolRadioGroup" + (_jmol.radioGroupCount - 1);
  if (!script)
    return "";
  if (labelHtml == undefined || labelHtml == null)
    labelHtml = script.substring(0, 32);
  if (! separatorHtml)
    separatorHtml = "";
  var scriptIndex = _jmolAddScript(script);
  return "<input name='" + groupName +
         "' type='radio' onClick='_jmolClick(" +
         scriptIndex + _jmol.targetText +
         ");return true;' onMouseover='_jmolMouseOver(" +
         scriptIndex +
         ");return true;' onMouseout='_jmolMouseOut()' " +
	 (isChecked ? "checked " : "") + _jmol.radioCssText + "/>" +
         labelHtml + separatorHtml;
}

function _jmolFindApplet(target) {
  // first look for the target in the current window
  var applet = _jmolSearchFrames(window, target);
  if (applet == undefined)
    applet = _jmolSearchFrames(top, target); // look starting in top frame
  return applet;
}

function _jmolSearchFrames(win, target) {
  var applet;
  var frames = win.frames;
  if (frames && frames.length) { // look in all the frames below this window
    for (var i = 0; i < frames.length; ++i) {
      applet = _jmolSearchFrames(frames[i], target);
      if (applet)
        break;
    }
  } else { // look for the applet in this window
    var doc = win.document;
// getElementById fails on MacOSX Safari & Mozilla	
    if (_jmol.useHtml4Object || _jmol.useIEObject)
      applet = doc.getElementById(target);
    else if (doc.applets)
      applet = doc.applets[target];
    else
      applet = doc[target];
  }
  return applet;
}

function _jmolAddScript(script) {
  if (! script)
    return 0;
  var index = _jmol.scripts.length;
  _jmol.scripts[index] = script;
  return index;
}

function _jmolClick(scriptIndex, targetSuffix) {
  jmolScript(_jmol.scripts[scriptIndex], targetSuffix);
}

function _jmolMenuSelected(menuObject, targetSuffix) {
  var scriptIndex = menuObject.value;
  if (scriptIndex != undefined) {
    jmolScript(_jmol.scripts[scriptIndex], targetSuffix);
    return;
  }
  var length = menuObject.length;
  if (typeof length == "number") {
    for (var i = 0; i < length; ++i) {
      if (menuObject[i].selected) {
        _jmolClick(menuObject[i].value, targetSuffix);
	return;
      }
    }
  }
  alert("?Que? menu selected bug #8734");
}

function _jmolCbClick(ckbox, whenChecked, whenUnchecked, targetSuffix) {
  _jmolClick(ckbox.checked ? whenChecked : whenUnchecked, targetSuffix);
}

function _jmolCbOver(ckbox, whenChecked, whenUnchecked) {
  window.status = _jmol.scripts[ckbox.checked ? whenUnchecked : whenChecked];
}

function _jmolMouseOver(scriptIndex) {
  window.status = _jmol.scripts[scriptIndex];
}

function _jmolMouseOut() {
  window.status = " ";
  return true;
}

function _jmolSetCodebase(codebase) {
  _jmol.codebase = codebase ? codebase : ".";
  if (_jmol.debugAlert)
    alert("jmolCodebase=" + _jmol.codebase);
}

function _jmolOnloadResetForms() {
  _jmol.previousOnloadHandler = window.onload;
  window.onload =
  function() {
    with (_jmol) {
      if (buttonCount+checkboxCount+menuCount+radioCount+radioGroupCount > 0) {
        var forms = document.forms;
        for (var i = forms.length; --i >= 0; )
          forms[i].reset();
      }
      if (previousOnloadHandler)
        previousOnloadHandler();
    }
  }
}

