from net.grinder.script.Grinder import grinder
from net.grinder.script import Test
from net.grinder.plugin.http import HTTPRequest
from HTTPClient import NVPair
from java.util import Random

protectedResourceTest = Test(1, "Request home")
authenticationTest = Test(2, "POST to login")
newCellTest = Test(3, "Make a new Cell")
evaluationTest = Test(4, "Evaluate 2 + 2")
updateTest = Test(5, "Get 4")
deleteCellTest = Test(6, "Delete Cell")

class TestRunner:
    def __call__(self):
        worksheet = '1'
        request = protectedResourceTest.wrap(
            HTTPRequest(url="http://localhost:8000/"))

        result = request.GET()
        result = maybeAuthenticate(result)
        result = request.GET('/home/admin/%s/' % worksheet)
        #print 'test sheet seen: ', (result.text.find('test') != -1)
        #print result.text
        
        base_url = 'http://localhost:8000/home/admin/%s' % worksheet 
        request = newCellTest.wrap(HTTPRequest(url=base_url + "/new_cell_after"))
        result = request.POST((NVPair("id","0"),))
        new_cell = result.text.split()[0].rstrip('___S_A_G_E___')
        #print 'new cell number', new_cell 

        request = evaluationTest.wrap(HTTPRequest(url=base_url + "/eval"))
        random = Random()
        a, b = random.nextInt(10**1), random.nextInt(10**1) 
        # print 'random test',a,b,
        evalData = ( NVPair("id", new_cell),
                     NVPair("input", "%s * %s"% (a,b)),
                     NVPair("newcell", "0"),)
        result = request.POST(evalData)
        #print 'input', result.text

        count = 0 
        while (True): 
            #grinder.sleep(5000)
            request = updateTest.wrap(HTTPRequest(url=base_url + "/cell_update"))
            getData = ( NVPair("id", new_cell),)
            result = request.POST(getData)
            #print 'full result:', result.text
            count += 1            
            if result.text.find('pre') != -1: 
                #print 'full result:', result.text
                print 'wait',count,'test',a,'*',b,'=', strip_answer(result.text)
                break

        request = deleteCellTest.wrap(HTTPRequest(url=base_url + "/delete_cell"))
        getData = ( NVPair("id", new_cell),)
        result = request.POST(getData)

# Function that checks the passed HTTPResult to see whether
# authentication is necessary. If it is, perform the authentication
# and record performance information against Test 2.
def maybeAuthenticate(lastResult):
    if lastResult.statusCode == 401 \
    or lastResult.text.find("password") != -1:

        #print "Challenged, authenticating"

        authenticationFormData = ( NVPair("email", "admin"),
                                   NVPair("password", "test"),)

        request = authenticationTest.wrap(
            HTTPRequest(url="%s/login" % lastResult.originalURI))

        return request.POST(authenticationFormData)

def strip_answer(text):
#<pre class="shrunk">532962756677</pre>
    st = text.find('<pre')
    end = text.find('</pre>')
    return text[st + 20 : end] 
