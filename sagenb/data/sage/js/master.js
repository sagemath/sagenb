/*global $, window */
/*jslint white: true, onevar: true, undef: true, nomen: true, eqeqeq: true, plusplus: true, bitwise: true, regexp: true, strict: true, newcap: true, immed: true */
//"use strict";

var replicate_str = function(x, n) {
    var str = '';
    for (var i = 0; i < n; ++i) {
        str += x;
    }
};

$(function () {
    var body = $('body'), body_id = body.attr('id');

    var hash_pwd_field = function($pwd, $msg, $hmac_pwd, $crypt_pwd) {
        if ($msg && $msg.length > 0) {
            // HMAC-SHA256 Authentication
            $hmac_pwd.val(hmac_sha256(sha256(sha256($pwd.val())), $msg.val()));
        } else {
            $hmac_pwd.val(sha256($pwd.val()));
        }
        if ($crypt_pwd && $crypt_pwd.length > 0) {
            $crypt_pwd.val(unixCryptTD($pwd.val(), 'aa'))
        }
        $pwd.val(replicate_str('*', $pwd.val().length));
    };

    if (body_id === 'worksheet-listing-page') {
        checkForGearsInstalled();
    } else if (body_id === 'login-page') {
        $('#openid').openid({
            img_path: '/javascript/openid-realselector/img/openid/',
            txt: {
                label: '{username} for <b>{provider}</b>',
                username: 'username',
                title: 'Select an OpenID provider',
                sign: 'Send'
            }
        });
        var $form = $('#sign-in-form');
        $form.bind('submit', function() {
            hash_pwd_field($form.find('input[name="password"]'),
                           $form.find('input[name="message"]'),
                           $form.find('input[name="hmac_password"]'),
                           $form.find('input[name="crypt_password"]'));
        });
    } else if (body_id === 'account-settings-page') {
        var $form = $('#account-settings-form');
        $form.bind('submit', function() {
            hash_pwd_field($form.find('input[name="old-pass"]'),
                           $form.find('input[name="message"]'),
                           $form.find('input[name="hmac-old-pass"]'),
                           $form.find('input[name="crypt-old-pass"]'));
            hash_pwd_field($form.find('input[name="new-pass"]'),
                           null,
                           $form.find('input[name="hmac-new-pass"]'));
            hash_pwd_field($form.find('input[name="retype-pass"]'),
                           null,
                           $form.find('input[name="hmac-retype-pass"]'));
        });
    } else if (body_id === 'registration-page') {
        var $form = $('#registration-form');
        $form.bind('submit', function() {
            hash_pwd_field($form.find('input[name="password"]'),
                           null,
                           $form.find('input[name="hmac_password"]'));
            hash_pwd_field($form.find('input[name="retype_password"]'),
                           null,
                           $form.find('input[name="hmac_retype_password"]'));
        });
    }

    if (body.hasClass('worksheet-online')) {
        initialize_the_notebook();
        $('.introspection .docstring .click-message', '#worksheet_cell_list')
            .live('click', function (e) {
                var ds_elem = $(this).parent(), id, name, style;

                id = toint(ds_elem.parent().attr('id').slice(15));
                name = introspect[id].before_replacing_word;

                if (name.slice(-2) === '??') {
                    // Source code.
                    name = name.slice(0, -2);
                    style = 'color: #007020';
                } else if (name.slice(-1) === '?' || name.slice(-1) === '(') {
                    // Docstring.
                    name = name.slice(0, -1);
                    style = 'color: #0000aa';
                }

                halt_introspection(id);

                ds_elem.dialog({
                    height: 600,
                    width: '90%',
                    title: '<span style="' + style + '">' + name + '<span>',
                    dialogClass: 'docstring-introspection-dialog',
                    'close': function (event, ui) {
                        ds_elem.dialog('destroy').remove();
                    }
                });
                ds_elem.find('.click-message').remove();
            });
    }
});
