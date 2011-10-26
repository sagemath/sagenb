/*global $, tinymce, tinyMCE */
/*jslint white: true, onevar: true, undef: true, nomen: true, eqeqeq: true, plusplus: true, bitwise: true, regexp: true, strict: true, newcap: true, immed: true */
//"use strict";


var toggleEditor = function (id) {
    if (!tinyMCE.get(id)) {
        tinyMCE.execCommand('mceAddControl', false, id);
    } else {
        tinyMCE.execCommand('mceRemoveControl', false, id);
    }
};


$.fn.tinymce = function (options) {
    return this.each(function () {
        tinyMCE.execCommand("mceAddControl", true, this.id);
    });
};


tinyMCE.init({
    mode : "none",
    plugins: "advlist,inlinepopups,lists,media,paste,searchreplace,table,autolink,",

    theme : "advanced",
    theme_advanced_toolbar_location : "top",
    theme_advanced_toolbar_align : "left",
    theme_advanced_statusbar_location : "bottom",
    theme_advanced_buttons1 : "formatselect,fontselect,fontsizeselect,bold,italic,underline,strikethrough,forecolor,backcolor,|,bullist,numlist,|,undo,redo,search,pastetext,pasteword",
    theme_advanced_buttons2 : "justifyleft,justifycenter,justifyright,justifyfull,outdent,indent,|,charmap,|,table,tablecontrols,|,code,|,link,image,media,unlink",
    theme_advanced_buttons3 : "",
    theme_advanced_resizing : true,
    theme_advanced_show_current_color: true,
    theme_advanced_default_background_color : "#FFCC99",

    setup : function (ed) {
        // Make ctrl-shift-enter insert a line break.  In some
        // browsers and on some platforms, ctrl-enter may work
        // anyway.
        ed.onKeyDown.add(function (ed, e) {
            if (e.keyCode === 13 && e.shiftKey && e.ctrlKey) {
                var dom = ed.dom, s = ed.selection, r = s.getRng(), br, p, y, h, vp;

                if (tinymce.isIE) {
                    // Adapted from tiny_mce.js.
                    s.setContent('<br id="__"/>', {format : 'raw'});
                    br = ed.dom.get('__');
                    br.removeAttribute('id');
                    s.select(br);
                    s.collapse();
                } else {
                    // Adapted from the TinyMCE Safari plug-in.
                    r.deleteContents();
                    br = dom.create('br');
                    r.insertNode(br);
                    r.setStartAfter(br);
                    r.setEndAfter(br);
                    s.setRng(r);
                    if (s.getSel().focusNode === br.previousSibling) {
                        s.select(dom.insertAfter(dom.doc.createTextNode('\u00a0'), br));
                        s.collapse(1);
                    }
                }

                // Insert a temporary 'p' to get the position and height.
                // This doesn't always work for 'br' in WebKit browsers.
                p = dom.create('p');
                p.textContent = '\u00a0';
                dom.insertAfter(p, br);
                y = dom.getPos(p).y;
                h = dom.getSize(p).h;
                dom.remove(p);
                vp = dom.getViewPort(ed.getWin());

                // Bring the caret into view, if necessary.  Adapted
                // from tiny_mce.js.
                if (y < vp.y || y + h > vp.y + vp.h) {
                    ed.getWin().scrollTo(0, y < vp.y ? y : y + h - vp.h);
                }
                tinymce.dom.Event.cancel(e);
            }
        });  // ed.onKeyDown.add

        // Make shift-enter quit editing.
        ed.onKeyDown.add(function (ed, e) {
            if (key_enter_shift(key_event(e))) {
                $(ed.formElement).submit();
            }
        });  // ed.onKeyDown.add
    }  // setup
});  // tinyMCE.init


$.editable.addInputType('mce', {
    element : function (settings, original) {
        var textarea = $('<textarea id="' + $(original).attr("id") +
                         '_mce"/>');
        if (settings.rows) {
            textarea.attr('rows', settings.rows);
        } else {
            textarea.height(settings.height);
        }
        if (settings.cols) {
            textarea.attr('cols', settings.cols);
        } else {
            textarea.width(settings.width);
        }
        $(this).append(textarea);
        return textarea;
    },

    plugin : function (settings, original) {
        tinyMCE.execCommand("mceAddControl", true,
                            $(original).attr("id") + '_mce');
    },

    submit : function (settings, original) {
        tinyMCE.triggerSave();
        tinyMCE.execCommand("mceRemoveControl", true,
                            $(original).attr("id") + '_mce');
    },

    reset : function (settings, original) {
        tinyMCE.execCommand("mceRemoveControl", true,
                            $(original).attr("id") + '_mce');
        original.reset();
    }
});
