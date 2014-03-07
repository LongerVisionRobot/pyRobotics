'''
@author: arcra
'''

import time
from pyRobotics import BB
from pyRobotics.ParallelSenders import ParallelSender
from pyRobotics.Messages import Command, Response

def testFunction(c):
    print "testFunction called..."
    print 'Params: ' + c.params
    return Response.FromCommandObject(c, True, 'Command response')

fmap = {
        'tst_testfunction' : testFunction
        }



def main():
    BB.Initialize(2000, fmap)
    
    BB.Start()
    
    print 'Sending command say...'
    print BB.SendAndWait(Command('spg_say', 'This is a test.'), 5000, 3)
  
    print 'Sending Async command...'
    ps = ParallelSender(Command('othertst_slowfunction', 'This is another test.'), 5000, 3)
  
    while ps.sending:
        print 'sending...'
        time.sleep(0.3)
  
    'Response received...'
    print ps.response
    
    BB.Wait()

if __name__ == "__main__":
    
    main()
