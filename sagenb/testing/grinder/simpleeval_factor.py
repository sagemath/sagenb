from net.grinder.script.Grinder import grinder
from net.grinder.script import Test
from net.grinder.plugin.http import HTTPRequest
from HTTPClient import NVPair
from java.util import Random

newCellTest = Test(1, "Make a new Cell")
evaluationTest = Test(2, "Evaluate")
updateTest = Test(3, "Poll until evaluated")
deleteCellTest = Test(4, "Delete Cell")

class TestRunner:
    def __call__(self):
        sheets = 10
        random = Random()
        worksheet = str(40 + random.nextInt(sheets))

        base_url = 'http://localhost:8000/home/admin/%s' % worksheet 
        request = newCellTest.wrap(HTTPRequest(url=base_url + "/new_cell_after"))
        result = request.POST((NVPair("id","0"),))
        new_cell = result.text.split()[0].rstrip('___S_A_G_E___')

        request = evaluationTest.wrap(HTTPRequest(url=base_url + "/eval"))
        a = random.nextInt(2**30)
        b = random.nextInt(2**30)
        evalData = ( NVPair("id", new_cell),
                     NVPair("input", "factor(%s%s)"% (a,b)),
                     NVPair("newcell", "0"),)
        result = request.POST(evalData)

        count = 0 
        while (True): 
            request = updateTest.wrap(HTTPRequest(url=base_url + "/cell_update"))
            getData = ( NVPair("id", new_cell),)
            result = request.POST(getData)
            count += 1            
            if result.text.find('pre') != -1: 
                print 'wait %s test factor %s%s = %s' % (count, a, b, strip_answer(result.text))
                break

        request = deleteCellTest.wrap(HTTPRequest(url=base_url + "/delete_cell"))
        getData = ( NVPair("id", new_cell),)
        result = request.POST(getData)

def strip_answer(text):
#<pre class="shrunk">532962756677</pre>
    st = text.find('<pre')
    end = text.find('</pre>')
    return text[st + 20 : end] 
