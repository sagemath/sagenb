r"""
Notebook Registration Challenges

This module includes support for challenge-response tests posed to
users registering for new Sage notebook accounts.  These \ **C**\
ompletely \ **A**\ utomated \ **P**\ ublic \ **T**\ uring tests to
tell \ **C**\ omputers and \ **H**\ umans \ **A**\ part, or CAPTCHAs,
may be simple math questions, requests for special registration codes,
or reCAPTCHAs_.

.. _reCAPTCHAs: http://recaptcha.net/

AUTHORS:

- reCAPTCHA_ is written by Ben Maurer and maintained by Josh
  Bronson. It is licensed under a MIT/X11 license.  The reCAPTCHA
  challenge implemented in :class:`reCAPTCHAChallenge` is adapted from
  `this Python API`_, which is also available here_.

.. _reCAPTCHA: http://recaptcha.net/
.. _this Python API: http://pypi.python.org/pypi/recaptcha-client
.. _here: http://code.google.com/p/recaptcha

"""

import os, random, re, urllib2, urllib

from sagenb.notebook.template import template


class ChallengeResponse(object):
    """
    A simple challenge response class that indicates whether a
    response is empty, correct, or incorrect, and, if it's incorrect,
    includes an optional error code.
    """
    def __init__(self, is_valid, error_code = None):
        """
        Instantiates a challenge response.

        INPUT:

        - ``is_valid`` - a boolean or None; whether there response is
          valid

        - ``error_code`` - a string (default: None); an optional error
          code if ``is_valid`` is False

        TESTS::

            sage: from sagenb.notebook.challenge import ChallengeResponse
            sage: resp = ChallengeResponse(False, 'Wrong! Please try again.')
            sage: resp.is_valid
            False
            sage: resp.error_code
            'Wrong! Please try again.'

        """
        self.is_valid = is_valid
        self.error_code = error_code


class AbstractChallenge(object):
    """
    An abstract class with a suggested common interface for specific
    challenge-response schemes.
    """
    def __init__(self, conf, **kwargs):
        """
        Instantiates an abstract challenge.

        INPUT:

        - ``conf`` - a :class:`ServerConfiguration`; a notebook server
          configuration instance

        - ``kwargs`` - a dictionary of keyword arguments

        TESTS::

            sage: from sagenb.notebook.challenge import AbstractChallenge
            sage: tmp = tmp_dir()
            sage: import sagenb.notebook.notebook as n
            sage: nb = n.Notebook(tmp)
            sage: chal = AbstractChallenge(nb.conf())

        """
        pass

    def html(self, **kwargs):
        """
        Returns HTML for the challenge, e.g., to insert into a new
        account registration page.

        INPUT:

        - ``kwargs`` - a dictionary of keywords arguments

        OUTPUT:

        - a string; HTML form representation of the challenge,
          including a field for the response, supporting hidden
          fields, JavaScript code, etc.

        TESTS::

            sage: from sagenb.notebook.challenge import AbstractChallenge
            sage: tmp = tmp_dir()
            sage: import sagenb.notebook.notebook as n
            sage: nb = n.Notebook(tmp)
            sage: chal = AbstractChallenge(nb.conf())
            sage: chal.html()
            Traceback (most recent call last):
            ...
            NotImplementedError:

        """
        raise NotImplementedError

    def is_valid_response(self, **kwargs):
        """
        Returns the status of a challenge response.

        INPUT:

        - ``kwargs`` - a dictionary of keyword arguments

        OUTPUT:

        - a :class:`ChallengeResponse` instance

        TESTS::

            sage: from sagenb.notebook.challenge import AbstractChallenge
            sage: tmp = tmp_dir()
            sage: import sagenb.notebook.notebook as n
            sage: nb = n.Notebook(tmp)
            sage: chal = AbstractChallenge(nb.conf())
            sage: chal.is_valid_response()
            Traceback (most recent call last):
            ...
            NotImplementedError:

        """
        raise NotImplementedError


class NotConfiguredChallenge(AbstractChallenge):
    """
    A fallback challenge used when an administrator has not configured
    a specific method.
    """
    def html(self, **kwargs):
        """
        Returns a suggestion to inform the Notebook server's
        administrator about the misconfigured challenge.

        INPUT:

        - ``conf`` - a :class:`ServerConfiguration`; an instance of the
          server's configuration

        - ``kwargs`` - a dictionary of keyword arguments

        OUTPUT:

        - a string

        TESTS::

            sage: from sagenb.notebook.challenge import NotConfiguredChallenge
            sage: tmp = tmp_dir()
            sage: import sagenb.notebook.notebook as n
            sage: nb = n.Notebook(tmp)
            sage: chal = NotConfiguredChallenge(nb.conf())
            sage: chal.html()
            'Please ask the server administrator to configure a challenge!'

        """
        return "Please ask the server administrator to configure a challenge!"

    def is_valid_response(self, **kwargs):
        """
        Always reports a failed response, for the sake of security.

        INPUT:

        - ``kwargs`` - a dictionary of keyword arguments

        OUTPUT:

        - a :class:`ChallengeResponse` instance
 
       TESTS::

            sage: from sagenb.notebook.challenge import NotConfiguredChallenge
            sage: tmp = tmp_dir()
            sage: import sagenb.notebook.notebook as n
            sage: nb = n.Notebook(tmp)
            sage: chal = NotConfiguredChallenge(nb.conf())
            sage: chal.is_valid_response().is_valid
            False
            sage: chal.is_valid_response().error_code
            ''

        """
        return ChallengeResponse(False, '')


# HTML template for :class:`SimpleChallenge`.
SIMPLE_TEMPLATE = """<p>%(question)s</p>
<input type="text" id="simple_response_field" name="simple_response_field" class="entry" tabindex="5" />
<input type="hidden" value="%(question)s" id="simple_challenge_field" name="simple_challenge_field" class="entry" />
"""

# A set of sample questions for :class:`SimpleChallenge`.
QUESTIONS = {
    'Is e^pi > pi^e?' : r'y|yes',
    'What is 8 times nine?' : r'72|seventy-two',
    'How many bits are in one byte?' : r'8|eight',
    'What is the smallest perfect number?' : r'6|six',
#    'What is our class registration code?' : r'XYZ123',
    'What is the largest prime factor of 1001?' : r'13|thirteen',
    'What is the multiplicative inverse of seventeen modulo nineteen?' : r'9|nine',
    'What is the smallest integer expressible as the sum of two positive cubes in two distinct ways?' : r'1729',
    'How many permutations of ABCD agree with it in no position? For example, BDCA matches ABCD only in position 3.' : r'9|nine',
}


def agree(response, answer):
    """
    Returns whether a challenge response agrees with the answer.

    INPUT:

    - ``response`` - a string; the user's response to a posed challenge

    - ``answer`` - a string; the challenge's right answer as a regular
      expression

    OUTPUT:

    - a boolean; whether the response agrees with the answer

    TESTS::

        sage: from sagenb.notebook.challenge import agree
        sage: agree('0', r'0|zero')
        True
        sage: agree('eighty', r'8|eight')
        False

    """
    response = re.sub(r'\s+', ' ', response.strip())
    m = re.search(r'^(' + answer + r')$', response, re.IGNORECASE)
    if m:
        return True
    else:
        return False


class SimpleChallenge(AbstractChallenge):
    """
    A simple question and answer challenge.
    """
    def html(self, **kwargs):
        """
        Returns a HTML form posing a randomly chosen question.

        INPUT:

        - ``kwargs`` - a dictionary of keyword arguments

        OUTPUT:

        - a string; the HTML form

        TESTS::

            sage: from sagenb.notebook.challenge import SimpleChallenge
            sage: tmp = tmp_dir()
            sage: import sagenb.notebook.notebook as n
            sage: nb = n.Notebook(tmp)
            sage: chal = SimpleChallenge(nb.conf())
            sage: chal.html() # random
            '...What is the largest prime factor of 1001?...'
            
        """
        question = random.choice([q for q in QUESTIONS])
        return SIMPLE_TEMPLATE % { 'question' : question }

    def is_valid_response(self, req_args = {}, **kwargs):
        """
        Returns the status of a user's answer to the challenge
        question.

        INPUT:

        - ``req_args`` - a string:list dictionary; the arguments of
          the remote client's HTTP POST request

        - ``kwargs`` - a dictionary of extra keyword arguments

        OUTPUT:

        - a :class:`ChallengeResponse` instance

        TESTS::

            sage: from sagenb.notebook.challenge import SimpleChallenge
            sage: tmp = tmp_dir()
            sage: import sagenb.notebook.notebook as n
            sage: nb = n.Notebook(tmp)
            sage: chal = SimpleChallenge(nb.conf())
            sage: req = {}
            sage: chal.is_valid_response(req).is_valid
            sage: chal.is_valid_response(req).error_code
            ''
            sage: from sagenb.notebook.challenge import QUESTIONS
            sage: import random
            sage: ques = random.choice([q for q in QUESTIONS])
            sage: ans = QUESTIONS[ques]
            sage: req['simple_response_field'] = [ans]
            sage: chal.is_valid_response(req).is_valid
            False
            sage: chal.is_valid_response(req).error_code
            ''
            sage: req['simple_challenge_field'] = [ques]
            sage: chal.is_valid_response(req).is_valid
            True
            sage: chal.is_valid_response(req).error_code
            ''

        """
        response_field = req_args.get('simple_response_field', [None])[0]
        if not (response_field and len(response_field)):
            return ChallengeResponse(None, '')

        challenge_field = req_args.get('simple_challenge_field', [None])[0]
        if not (challenge_field and len(challenge_field)):
            return ChallengeResponse(False, '')

        if agree(response_field, QUESTIONS[challenge_field]):
            return ChallengeResponse(True, '')
        else:
            return ChallengeResponse(False, '')


RECAPTCHA_SERVER = "http://api.recaptcha.net"
RECAPTCHA_SSL_SERVER = "https://api-secure.recaptcha.net"
RECAPTCHA_VERIFY_SERVER = "api-verify.recaptcha.net"

class reCAPTCHAChallenge(AbstractChallenge):
    """
    A reCAPTCHA_ challenge adapted from `this Python API`_, also
    hosted here_, written by Ben Maurer and maintained by Josh
    Bronson.

    .. _reCAPTCHA: http://recaptcha.net/
    .. _this Python API: http://pypi.python.org/pypi/recaptcha-client
    .. _here: http://code.google.com/p/recaptcha
    """
    def __init__(self, conf, remote_ip = '', is_secure = False, lang = 'en',
                 **kwargs):
        """
        Instantiates a reCAPTCHA challenge.

        INPUT:

        - ``conf`` - a :class:`ServerConfiguration`; an instance of the
          notebook server's configuration

        - ``remote_ip`` - a string (default: ''); the user's IP
          address, **required** by reCAPTCHA

        - ``is_secure`` - a boolean (default: False); whether the
          user's connection is secure, e.g., over SSL

        - ``lang`` - a string (default 'en'); the language used for
          the reCAPTCHA interface.  As of October 2009, the
          pre-defined choices are 'en', 'nl', 'fr', 'de', 'pt', 'ru',
          'es', and 'tr'

        - ``kwargs`` - a dictionary of extra keyword arguments

        ATTRIBUTES:

        - ``public_key`` - a string; a **site-specific** public
          key obtained at the `reCAPTCHA site`_.

        - ``private_key`` - a string; a **site-specific** private
          key obtained at the `reCAPTCHA site`_.

        .. _reCAPTCHA site: http://recaptcha.net/whyrecaptcha.html

        Currently, the keys are read from ``conf``'s
        ``recaptcha_public_key`` and ``recaptcha_private_key``
        settings.

        TESTS::

            sage: from sagenb.notebook.challenge import reCAPTCHAChallenge
            sage: tmp = tmp_dir()
            sage: import sagenb.notebook.notebook as n
            sage: nb = n.Notebook(tmp)
            sage: chal = reCAPTCHAChallenge(nb.conf(), remote_ip = 'localhost')

        """
        self.remote_ip = remote_ip
        if is_secure:
            self.api_server = RECAPTCHA_SSL_SERVER
        else:
            self.api_server = RECAPTCHA_SERVER

        self.lang = lang
        self.public_key = conf['recaptcha_public_key']
        self.private_key = conf['recaptcha_private_key']

    def html(self, error_code = None, **kwargs):
        """
        Returns HTML and JavaScript for a reCAPTCHA challenge and
        response field.

        INPUT:

        - ``error_code`` - a string (default: None); an optional error
          code to embed in the HTML, giving feedback about the user's
          *previous* response
        
        - ``kwargs`` - a dictionary of extra keyword arguments

        OUTPUT:
        
        - a string; HTML and JavaScript to render the reCAPTCHA
          challenge

        TESTS::

            sage: from sagenb.notebook.challenge import reCAPTCHAChallenge
            sage: tmp = tmp_dir()
            sage: import sagenb.notebook.notebook as n
            sage: nb = n.Notebook(tmp)
            sage: chal = reCAPTCHAChallenge(nb.conf(), remote_ip = 'localhost')
            sage: chal.html()
            '<script type="text/javascript">...</script>'
            sage: chal.html('incorrect-captcha-sol')
            '<script...incorrect-captcha-sol...</script>'

        """
        error_param = ''
        if error_code:
            error_param = '&error=%s' % error_code

        template_dict = { 'api_server' : self.api_server,
                          'public_key' : self.public_key,
                          'error_param' : error_param,
                          'lang' : self.lang }

        return template(os.path.join('html', 'recaptcha.html'),
                        **template_dict)

    def is_valid_response(self, req_args = {}, **kwargs):
        """
        Submits a reCAPTCHA request for verification and returns its
        status.
        
        INPUT:

        - ``req_args`` - a dictionary; the arguments of the responding
          user's HTTP POST request

        - ``kwargs`` - a dictionary of extra keyword arguments

        OUTPUT:

        - a :class:`ChallengeResponse` instance; whether the user's
          response is empty, accepted, or rejected, with an optional
          error string

        TESTS::

            sage: from sagenb.notebook.challenge import reCAPTCHAChallenge
            sage: tmp = tmp_dir()
            sage: import sagenb.notebook.notebook as n
            sage: nb = n.Notebook(tmp)
            sage: chal = reCAPTCHAChallenge(nb.conf(), remote_ip = 'localhost')
            sage: req = {}
            sage: chal.is_valid_response(req).is_valid
            sage: chal.is_valid_response(req).error_code
            ''
            sage: req['recaptcha_response_field'] = ['subplotTimes']
            sage: chal.is_valid_response(req).is_valid
            False
            sage: chal.is_valid_response(req).error_code
            'incorrect-captcha-sol'
            sage: req['simple_challenge_field'] = ['VBORw0KGgoANSUhEUgAAAB']
            sage: chal.is_valid_response(req).is_valid # random
            False
            sage: chal.is_valid_response(req).error_code # random
            'incorrect-captcha-sol'

        """
        response_field = req_args.get('recaptcha_response_field', [None])[0]
        if not (response_field and len(response_field)):
            return ChallengeResponse(None, '')

        challenge_field = req_args.get('recaptcha_challenge_field', [None])[0]
        if not (challenge_field and len(challenge_field)):
            return ChallengeResponse(False, 'incorrect-captcha-sol')

        def encode_if_necessary(s):
            if isinstance(s, unicode):
                return s.encode('utf-8')
            return s

        params = urllib.urlencode({
                'privatekey': encode_if_necessary(self.private_key),
                'remoteip' :  encode_if_necessary(self.remote_ip),
                'challenge':  encode_if_necessary(challenge_field),
                'response' :  encode_if_necessary(response_field)
                })

        request = urllib2.Request(
            url = "http://%s/verify" % RECAPTCHA_VERIFY_SERVER,
            data = params,
            headers = {
                "Content-type": "application/x-www-form-urlencoded",
                "User-agent": "reCAPTCHA Python"
                }
            )

        httpresp = urllib2.urlopen(request)
        return_values = httpresp.read().splitlines();
        httpresp.close();
        return_code = return_values[0]

        if (return_code == "true"):
            return ChallengeResponse(True)
        else:
            return ChallengeResponse(False, return_values[1])


class ChallengeDispatcher(object):
    """
    A simple dispatcher class that provides access to a specific
    challenge.
    """
    def __init__(self, conf, **kwargs):
        """
        Uses the server's configuration to select and set up a
        challenge.

        INPUT:

        - ``conf`` - a :class:`ServerConfiguration`; a server
          configuration instance

        - ``kwargs`` - a dictionary of keyword arguments

        ATTRIBUTES:

        - ``type`` - a string; the type of challenge to set up

        Currently, ``type`` is read from ``conf``'s ``challenge_type``
        setting.

        TESTS::

            sage: from sagenb.notebook.challenge import ChallengeDispatcher
            sage: tmp = tmp_dir()
            sage: import sagenb.notebook.notebook as n
            sage: nb = n.Notebook(tmp)
            sage: disp = ChallengeDispatcher(nb.conf())
            sage: disp.type # random
            'recaptcha'

        """
        self.type = conf['challenge_type']

        if self.type == 'recaptcha':
            # Very simple test for public and private reCAPTCHA keys.
            if conf['recaptcha_public_key'] and conf['recaptcha_private_key']:
                self.challenge = reCAPTCHAChallenge(conf, **kwargs)
            else:
                self.challenge = NotConfiguredChallenge(conf, **kwargs)

        elif self.type == 'simple':
            self.challenge = SimpleChallenge(conf, **kwargs)

        else:
            self.challenge = NotConfiguredChallenge(conf, **kwargs)

    def __call__(self):
        """
        Returns a previously set up challenge.

        OUTPUT:

        - an instantiated subclass of :class:`AbstractChallenge`.

        TESTS::

            sage: from sagenb.notebook.challenge import ChallengeDispatcher
            sage: tmp = tmp_dir()
            sage: import sagenb.notebook.notebook as n
            sage: nb = n.Notebook(tmp)
            sage: nb.conf()['challenge_type'] = 'simple'
            sage: disp = ChallengeDispatcher(nb.conf())
            sage: disp().html() # random
            '<p>...'
            sage: nb.conf()['challenge_type'] = 'mistake'
            sage: disp = ChallengeDispatcher(nb.conf())
            sage: disp().html()
            'Please ask the server administrator to configure a challenge!'

        """
        return self.challenge


def challenge(conf, **kwargs):
    """
    Wraps an instance of :class:`ChallengeDispatcher` and returns an
    instance of a specific challenge.

    INPUT:

    - ``conf`` - a :class:`ServerConfiguration`; a server configuration
      instance

    - ``kwargs`` - a dictionary of keyword arguments

    OUTPUT:

    - an instantiated subclass of :class:`AbstractChallenge`

    TESTS::

        sage: from sagenb.notebook.challenge import challenge
        sage: tmp = tmp_dir()
        sage: import sagenb.notebook.notebook as n
        sage: nb = n.Notebook(tmp)
        sage: nb.conf()['challenge_type'] = 'simple'
        sage: chal = challenge(nb.conf())
        sage: chal.html() # random
        '<p>...'

    """
    return ChallengeDispatcher(conf, **kwargs)()
