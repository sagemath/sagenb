from net.grinder.script.Grinder import grinder
from net.grinder.script import Test
from net.grinder.plugin.http import HTTPRequest
from HTTPClient import NVPair

# We declare a default URL for the HTTPRequest.
request = HTTPRequest(url = "http://localhost:8000")

def page1():
    request.GET('/')
    #request.GET('/console/login/LoginForm.jsp')
    #request.GET('/console/login/bea_logo.gif')

page1Test = Test(1, "First page").wrap(page1)

class TestRunner:
    def __call__(self):
        page1Test()
