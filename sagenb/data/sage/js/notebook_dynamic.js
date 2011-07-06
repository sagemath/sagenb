///////////////////////////////////////////////////////////////////
//
// "External" Javascript
//
///////////////////////////////////////////////////////////////////


// Key codes (auto-generated in js.py from config.py and user's sage
// config).
 {{ KEY_CODES }}
 
// Other libraries.
{% include "js/async_lib.js" %}
{% include "js/canvas3d_lib.js" %}
{% include "js/jmol_lib.js" %}

{%- if debug_mode %}
{% include "js/debug.js" %}
{% endif %}

function interrupt_callback(status, response) {
    /*
    Callback called after we send the interrupt signal to the server.
    If the interrupt succeeds, we change the CSS/DOM to indicate that
    no cells are currently computing.  If it fails, we display/update
    a alert and repeat after a timeout.  If the signal doesn't make
    it, we just reset any alerts.
    */
    var is = interrupt_state, message;
    {% set timeout = 5 %}
    var timeout = {{ timeout }};

    if (response === 'failed') {
        if (!is.count) {
            is.count = 1;
            message = translations['Unable to interrupt calculation.'] + " " + translations[timeout > 1 ? 2 : 1]['Trying again in %(num)d second...'](timeout) + ' ' + translations['Close this box to stop trying.'];

            is.alert = $.achtung({
                className: 'interrupt-fail-notification',
                message: message,
                timeout: timeout,
                hideEffects: false,
                showEffects: false,
                onCloseButton: function () {
                    reset_interrupts();
                },
                onTimeout: function () {
                    interrupt();
                }
            });
            return;
        }

        is.count += 1;
        message = translations['Interrupt attempt'] + " " + is.count;
        if (is.count > 5) {
            message += ". " + translations["<a href='javascript:restart_sage();'>Restart</a>, instead?"];
        }
        is.alert.achtung('update', {
            message: message,
            timeout: timeout
        });
    } else if (status === 'success') {
        halt_queued_cells();
    } else {
        reset_interrupts();
    }
}
