# The Grinder 3.6
# HTTP script recorded by TCPProxy at Nov 8, 2011 8:34:41 AM

from net.grinder.script import Test
from net.grinder.script.Grinder import grinder
from net.grinder.plugin.http import HTTPPluginControl, HTTPRequest
from HTTPClient import NVPair
connectionDefaults = HTTPPluginControl.getConnectionDefaults()
httpUtilities = HTTPPluginControl.getHTTPUtilities()

# To use a proxy server, uncomment the next line and set the host and port.
# connectionDefaults.setProxyServer("localhost", 8001)

# These definitions at the top level of the file are evaluated once,
# when the worker process is started.

connectionDefaults.defaultHeaders = \
  [ NVPair('Accept-Language', 'en-us,en;q=0.5'),
    NVPair('Accept-Charset', 'ISO-8859-1,utf-8;q=0.7,*;q=0.7'),
    NVPair('Accept-Encoding', 'gzip, deflate'),
    NVPair('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:7.0.1) Gecko/20100101 Firefox/7.0.1'), ]

headers0= \
  [ NVPair('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'), ]

headers1= \
  [ NVPair('Accept', 'text/css,*/*;q=0.1'),
    NVPair('Referer', 'http://test.sagenb.org/pub/'), ]

headers2= \
  [ NVPair('Accept', '*/*'),
    NVPair('Referer', 'http://test.sagenb.org/pub/'), ]

headers3= \
  [ NVPair('Accept', 'image/png,image/*;q=0.8,*/*;q=0.5'),
    NVPair('Referer', 'http://test.sagenb.org/pub/'), ]

url0 = 'http://test.sagenb.org:80'
url1 = 'http://www.google-analytics.com:80'

# Create an HTTPRequest for each request, then replace the
# reference to the HTTPRequest with an instrumented version.
# You can access the unadorned instance using request101.__target__.
request101 = HTTPRequest(url=url0, headers=headers0)
request101 = Test(101, 'GET /').wrap(request101)

request102 = HTTPRequest(url=url0, headers=headers1)
request102 = Test(102, 'GET main.css').wrap(request102)

request103 = HTTPRequest(url=url0, headers=headers2)
request103 = Test(103, 'GET localization.js').wrap(request103)

request201 = HTTPRequest(url=url1, headers=headers3)
request201 = Test(201, 'GET __utm.gif').wrap(request201)


class TestRunner:
  """A TestRunner instance is created for each worker thread."""

  # A method for each recorded page.
  def page1(self):
    """GET / (requests 101-103)."""
    result = request101.GET('/pub/')
    # 3 different values for token_sort found in response, using the first one.
    self.token_sort = \
      httpUtilities.valueFromBodyURI('sort') # 'rating'
    # 2 different values for token_typ found in response, using the first one.
    self.token_typ = \
      httpUtilities.valueFromBodyURI('typ') # 'active'
    self.token_reverse = \
      httpUtilities.valueFromBodyURI('reverse') # 'True'

    grinder.sleep(218)
    request102.GET('/css/main.css')

    request103.GET('/javascript/dynamic/localization.js')

    return result

  def page2(self):
    """GET __utm.gif (request 201)."""
    self.token_utmwv = \
      '5.2.0'
    self.token_utms = \
      '4'
    self.token_utmn = \
      '1624681580'
    self.token_utmhn = \
      'test.sagenb.org'
    self.token_utmcs = \
      'UTF-8'
    self.token_utmsr = \
      '1680x1050'
    self.token_utmsc = \
      '24-bit'
    self.token_utmul = \
      'en-us'
    self.token_utmje = \
      '1'
    self.token_utmfl = \
      '10.2 r153'
    self.token_utmdt = \
      'Published Worksheets -- Sage'
    self.token_utmhid = \
      '25603674'
    self.token_utmr = \
      '-'
    self.token_utmp = \
      '/pub/'
    self.token_utmac = \
      'UA-24214040-1'
    self.token_utmcc = \
      '__utma=199536369.2072460302.1309502470.1320725328.1320762863.9;+__utmz=199536369.1309502470.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none);'
    self.token_utmu = \
      'qB~'
    result = request201.GET('/__utm.gif' +
      '?utmwv=' +
      self.token_utmwv +
      '&utms=' +
      self.token_utms +
      '&utmn=' +
      self.token_utmn +
      '&utmhn=' +
      self.token_utmhn +
      '&utmcs=' +
      self.token_utmcs +
      '&utmsr=' +
      self.token_utmsr +
      '&utmsc=' +
      self.token_utmsc +
      '&utmul=' +
      self.token_utmul +
      '&utmje=' +
      self.token_utmje +
      '&utmfl=' +
      self.token_utmfl +
      '&utmdt=' +
      self.token_utmdt +
      '&utmhid=' +
      self.token_utmhid +
      '&utmr=' +
      self.token_utmr +
      '&utmp=' +
      self.token_utmp +
      '&utmac=' +
      self.token_utmac +
      '&utmcc=' +
      self.token_utmcc +
      '&utmu=' +
      self.token_utmu)

    return result

  def __call__(self):
    """This method is called for every run performed by the worker thread."""
    self.page1()      # GET / (requests 101-103)

    grinder.sleep(1230)
    self.page2()      # GET __utm.gif (request 201)


def instrumentMethod(test, method_name, c=TestRunner):
  """Instrument a method with the given Test."""
  unadorned = getattr(c, method_name)
  import new
  method = new.instancemethod(test.wrap(unadorned), None, c)
  setattr(c, method_name, method)

# Replace each method with an instrumented version.
# You can call the unadorned method using self.page1.__target__().
instrumentMethod(Test(100, 'Page 1'), 'page1')
instrumentMethod(Test(200, 'Page 2'), 'page2')


