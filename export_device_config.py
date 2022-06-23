from webbrowser import get
import requests, json, urllib3, time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# Prints JSON in a readable way
def pretty_print(dict):
    return print(json.dumps(dict, indent=4))

# Generates DNAC token based on DNAC credentials
def get_auth_token(username, password):
    auth_url = base_url + "/dna/system/api/v1/auth/token"

    headers = {"Content-Type": "application/json"}

    response = requests.post(auth_url, headers=headers, auth=(username,password), verify=False)

    token = json.loads(response.text)['Token']

    return token

# Creates a list of all devices
def get_device_list(token):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-Auth-token": token 
    }
    url = base_url + '/dna/intent/api/v1/network-device'
    
    device_list = requests.get(url=url, headers=headers).json()['response']

    return device_list

# Takes a list of devices and filters for UUID -> returns a list of UUIDs
def get_device_uuids(token):
    device_list = get_device_list(token)
    device_IDs = []

    print("GENERATING DEVICE LIST...\n")
    for index, device in enumerate(device_list):
        device_IDs.append(device['id'])
        print(f"{index+1}: {device['type']}\n\tMGMT_IP: {device['managementIpAddress']}")
        print(f"\tUUID: {device['id']}")
    
    return device_IDs

# Runs Configuration Archive Export -- process is asynchronous therefore returns a taskId
def export_config(uuids, password, token):
    url = base_url + '/dna/intent/api/v1/network-device-archive/cleartext'

    payload = {
        "deviceId": uuids, 
        "password": password
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-Auth-token": token 
    }
    
    response = requests.post(url, headers=headers, json=payload)
    #pretty_print(response.json())
    taskId = response.json()['response']['taskId']

    return taskId

# Waits for Task to complete and returns the "additionalStatusURL" field
# This field contains the API endpoint to query for config archive 
def wait_for_task(token, taskId):
    url = base_url +"/dna/intent/api/v1/task/" + taskId
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-auth-token": token 
    }

    attempts = 3
    waitTime = 5

    for i in range(attempts):
        time.sleep(waitTime)

        response = requests.get(url, headers=headers, verify=False)

        data = response.json()['response']
        #pretty_print(data)
        # If "endTime" field is in data then the processing is complete --> HTTP 200
        if "endTime" in data:
            fileURL = data['additionalStatusURL']
            return fileURL

    print("Request timed out")

# Takes a fileId and downloads it into local File Structure
def download_file(fileURL, filename):
    url = base_url + fileURL
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-auth-token": token 
    }

    try:
        response = requests.get(url, headers=headers, verify=False)
        with open(f'{filename}.zip', 'wb') as file:
            file.write(response.content)
        
        print(f"\nSuccessfully Created {filename}.zip")
    except Exception as e:
        print("Error while downloading file\nError Message: ", e)

# MAIN FUNC
def main():
    uuids = get_device_uuids(token)
    task_id = export_config(uuids, password, token)
    fileURL = wait_for_task(token, task_id)
    download_file(fileURL, filename)


if __name__=='__main__':
    # Base URL for DNAC API access
    base_url = "https://sandboxdnac2.cisco.com"

    # Update to your DNAC Credentials
    password = "Cisco123!"
    username= "devnetuser"

    # Name of Archive Zip File 
    filename = "Configuration_Archive"

    token = get_auth_token(username,password)

    # If you plan on harcoding the Device UUIDs, then enter into below field --  consequently comment out line 107!
    #uuids = ['']
    
    main()

