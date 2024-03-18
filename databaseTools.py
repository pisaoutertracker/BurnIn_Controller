from pprint import pprint
import requests

verbose=100
ip="192.168.0.45"
port=5000

#upload session to DB
def uploadSessionToDB(sessionDescription = {}):

    if verbose>0: print("Calling uploadSessionToDB()")
    if verbose>2: pprint(sessionDescription)
   
    # URL of the API endpoint
    api_url = "http://%s:%d/sessions"%(ip, port)
    
    # Send a PUT request
    try:
        response = requests.post(api_url, json=sessionDescription,timeout=5)
    except requests.exceptions.Timeout:
        return "timeout"
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)

    # Check the response
    if response.status_code == 201:
        if 1<verbose<=2: print("Session \"%s\" created successfully"%response.json()["sessionName"])
        if verbose>2: pprint(response.json)
    else:
        print("Failed to update the session. Status code:", response.status_code)
    return response.json()["sessionName"]

### read the test result from DB

def getSessionFromDB(sessionName):
    if verbose>0: print("Calling getSessionFromDB()", sessionName)
    api_url = "http://%s:%d/sessions/%s"%(ip, port, sessionName)
    response = requests.get(api_url)
    if response.status_code == 200:
        if verbose>1: print("Session successfully pulled.")
    else:
        print("Failed to pull the session. Status code:", response.status_code)
    return eval(response.content.decode())
	

def updateSessionFromDB(sessionName,sessionDescription = {}):
    if verbose>0: print("Calling updateSessionFromDB()", sessionName)
    api_url = "http://%s:%d/sessions/%s"%(ip, port, sessionName)
    response = requests.put(api_url,json=sessionDescription)
    if response.status_code == 200:
        if verbose>1: print("Session successfully updated.")
    else:
        print("Failed to update the session. Status code:", response.status_code)
    return eval(response.content.decode())

if __name__ == '__main__':
    sessionName="session5"
    from pprint import pprint
    pprint(getSessionFromDB(sessionName))
