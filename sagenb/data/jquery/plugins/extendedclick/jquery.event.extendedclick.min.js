;(function($){$.event.special.plainclick=$.event.special.ctrlclick=$.event.special.altclick=$.event.special.shiftclick=$.event.special.ctrlaltclick=$.event.special.ctrlshiftclick=$.event.special.altshiftclick=$.event.special.ctrlaltshiftclick={setup:function(){$.event.add(this,"click",extendedClickHandler,{});},teardown:function(){$.event.remove(this,"click",extendedClickHandler);}};function extendedClickHandler(event){if(event.type==="click"){if(event.ctrlKey)
{if(event.shiftKey)
{if(event.altKey||event.originalEvent.altKey)
{event.type="ctrlaltshiftclick";}
else
event.type="ctrlshiftclick";}
else if(event.altKey||event.originalEvent.altKey)
{event.type="ctrlaltclick";}
else
event.type="ctrlclick";}
else if(event.altKey||event.originalEvent.altKey)
{if(event.shiftKey)
{event.type="altshiftclick";}
else
event.type="altclick";}
else if(event.shiftKey)
{event.type="shiftclick";}
else
{event.type="plainclick";}
return $.event.handle.call(this,event);}}})(jQuery);