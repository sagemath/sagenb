from net.grinder.script.Grinder import grinder
from net.grinder.script import Test
from net.grinder.plugin.http import HTTPRequest
from HTTPClient import NVPair
from java.util import Random

# We declare a default URL for the HTTPRequest.
request = HTTPRequest(url = "http://www.google.com")
#request = HTTPRequest(url = "http://aleph.sagemath.org")

def evalss():
    wait = 250
    random = Random()
    a, b  = (random.nextInt(), random.nextInt())
    #input = '%s*%s' % (a, b)
    input = 'from+sage.all+import+*;factor(ZZ.random_element(10**40))'
    result = request.GET('/execute?input=%s' % input)
    id = result.text
    count = 0
    while (True):
        grinder.sleep(wait) 
        result = request.GET('/get?id=%s' % id)
        count += 1
        if result.text.find('wait') == -1:
            break
    ans = eval(result.text)
    print 'test waited%s ans = %s' % (count, ans['output'])

evalssTest = Test(1, "Exec testpage").wrap(evalss)

def homess():
    request.GET('/')

homessTest = Test(2, "query homepage").wrap(homess)

class TestRunner:
    def __call__(self):
        #evalssTest()
        homessTest()
