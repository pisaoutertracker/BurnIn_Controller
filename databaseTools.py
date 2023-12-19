from pprint import pprint
import requests

verbose=100
ip="192.168.0.45"
port=5005

#upload session to DB
def uploadSessionToDB(sessionDescription = {}):
    sessionName=sessionDescription["sessionName"]
    if verbose>0: print("Calling uploadSessionToDB()", sessionName)
    if verbose>2: pprint(sessionDescription)
   
    # URL of the API endpoint
    api_url = "http://%s:%d/sessionss"%(ip, port)
    
    # Send a PUT request
    response = requests.post(api_url, json=sessionDescription)
    
    # Check the response
    if response.status_code == 201:
        if verbose>1: print("Session %s created successfully"%sessionName)
    else:
        print("Failed to update the session. Status code:", response.status_code)

### read the test result from DB

def getSessionFromDB(sessionName):
    if verbose>0: print("Calling getTestFromDB()", sessionName)
    api_url = "http://%s:%d/sessions/%s"%(ip, port, sessionName)
    response = requests.get(api_url)
    if response.status_code == 200:
        if verbose>1: print("Session successfully pulled.")
    else:
        print("Failed to pull the session. Status code:", response.status_code)
    return eval(response.content.decode())

if __name__ == '__main__':
    sessionName="session1"
    from pprint import pprint
    pprint(getSessionFromDB(sessionName))
