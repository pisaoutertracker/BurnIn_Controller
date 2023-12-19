from pprint import pprint
import requests

verbose=3
ip="192.168.0.45"
port=5005


#upload session to DB
def uploadSessionToDB(sessionDescription = {}):
    seshKey=sessionDescription["sessionKey"]
    if verbose>0: print("Calling uploadSessionToDB()", seshKey)
    if verbose>2: pprint(testResult)
   
    # URL of the API endpoint
    api_url = "http://%s:%d/sessionss"%(ip, port)
    
    # Send a PUT request
    response = requests.post(api_url, json=sessionDescription)
    
    # Check the response
    if response.status_code == 201:
        if verbose>1: print("Session %s created successfully"%sesh)
    else:
        print("Failed to update the module. Status code:", response.status_code)

### read the test result from DB

def getSessionFromDB(seshKey="658078708c02ab6a2ede8051"):
    if verbose>0: print("Calling getTestFromDB()", seshKey)
    api_url = "http://%s:%d/tests/%s"%(ip, port, seshKey)
    response = requests.get(api_url)
    if response.status_code == 200:
        if verbose>1: print("Module %supdated successfully")
    else:
        print("Failed to update the module. Status code:", response.status_code)
    return eval(response.content.decode())
