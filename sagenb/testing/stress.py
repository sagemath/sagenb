import re
import urllib2


from sage.misc.sage_timeit import sage_timeit
from sage.misc.misc import alarm, cancel_alarm

from sagenb.misc.misc import walltime, cputime


TIMEOUT = 'timeout'

class PubStressTest:
    """
    Stress test viewing things that a non-authenticated viewer can
    look at, namely the login screen, list of published worksheets,
    and each individual published worksheet.
    """
    def __init__(self, url, verbose=True,
                 timeit_number=1, timeit_repeat=1,
                 url_timeout=10):
        """
        INPUT:

            - ``url`` -- url of the Sage notebook server

            - ``verbose`` -- bool; whether to print info about what is
              being tested as it is tested

            - ``timeit_number`` -- integer (default: 1)

            - ``timeit_repeat`` -- integer (default: 1)
            
            
        """
        self._url = url
        self._verbose = verbose
        self._timeit_number = timeit_number
        self._timeit_repeat = timeit_repeat
        self._url_timeout = url_timeout

    def url_login_screen(self):
        """
        Return the url of the login screen for the notebook server.
        """
        return self._url

    def url_pub(self):
        """
        Return the url of the list list of published worksheets.
        """
        return self._url + '/pub'

    def _timeit(self, code):
        """
        Time evaluation of the given code, timing out after
        self._url_timeout seconds, and using the default number and
        repeat values as options to timeit.
        """
        try:
            alarm(self._url_timeout)
            T = sage_timeit(code, globals(), number=self._timeit_number,
                               repeat=self._timeit_repeat)
        except KeyboardInterrupt:
            return TIMEOUT
        finally:
            cancel_alarm()
        return T

    def _geturlcode(self, url):
        """
        Return code that when evaluated returns the data at the given
        url as a string.
        """
        return "urllib2.urlopen('%s').read()"%(url)

    def _geturl(self, url, use_alarm=True):
        """
        Download the given url.  If use_alarm is True (the default)
        timeout and return the TIMEOUT object if the default download
        timeout is exceeded.
        """
        if not use_alarm:
            return urllib2.urlopen(url).read()
        try:
            alarm(self._url_timeout)
            return urllib2.urlopen(url).read()
        except KeyboardInterrupt:
            return TIMEOUT
        finally:
            cancel_alarm()
        
    def test_login_screen(self):
        """
        Download the main login screen for the Sage notebook server.
        """
        if self._verbose: print "testing login screen..."
        return self._timeit(self._geturlcode(self.url_login_screen()))

    def test_pub(self):
        """
        Download the list of published worksheets.
        """
        if self._verbose: print "testing list of published worksheets..."
        return self._timeit(self._geturlcode(self.url_pub()))

    def get_urls_of_published_worksheets(self):
        """
        Get a list of the urls of all published worksheets.
        """
        pub = self._geturl(self.url_pub())
        if pub == TIMEOUT:
            print TIMEOUT
            return []
        return [self._url + X.strip('"').strip("'") for X in
                re.findall('"/home/pub/[0-9]*"', pub)]

    def test_allpub(self):
        """
        View every single one of the published worksheets on the
        Sage notebook server.
        """
        if self._verbose: print "testing download of all published worksheets..."
        tm = walltime()
        pub = self.get_urls_of_published_worksheets()
        try:
            alarm(self._url_timeout)
            for i, X in enumerate(pub):
                t0 = walltime()
                self._geturl(X, use_alarm=False)
                if self._verbose:
                    print "Got %s [%s/%s] %.2f seconds"%(X,i,len(X), walltime(t0))
            return walltime(tm)
        except KeyboardInterrupt:
            return TIMEOUT
        finally:
            cancel_alarm()

    def test(self):
        """
        Run all tests and return the rest as a dictionary of pairs
        {'test_name':output}.
        """
        v = {}
        for method in dir(self):
            if method.startswith('test_'):
                v[method] = getattr(self, method)()
        return v

