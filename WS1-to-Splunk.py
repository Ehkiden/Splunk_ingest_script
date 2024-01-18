import json
import requests
import os

'''
Purpose: To gather Workspace One compliance metrics weekly and forward them to Splunk for logging, metrics, and correlation
'''

# forward the resulting json to the splunk event collector to be stored
def forward_onto_splunk(incident_list):
    splunk_tenant = os.environ['splunk_tenant']
    splunk_url = f"https://http-inputs-{splunk_tenant}.splunkcloud.com:443/services/collector"

    splunk_hec = os.environ['splunk_hec']
    splunk_headers = {
    'Authorization': f'Splunk {splunk_hec}',
    }
    try:
        splunk_resp = json.loads(requests.post(splunk_url, headers=splunk_headers, json=incident_list).content)
    except requests.exceptions.HTTPError as e:
        raise e

    if splunk_resp['text'] == "Success":
        print("WS1 metrics sent to Splunk successfully.")
        print(splunk_resp)
    else:
        print("An error occured during the Splunk POST attempt.")
        print(splunk_resp)
    x=42    # debug variable

# formats then groups all incidents found into an array of jsons 
def dont_make_an_incident(incident_json):
    incident_list = []
    for i in incident_json:
        incident_list.append({
            "event": i,
            "sourcetype": "ws1:compliance"
        })
    # hehe
    forward_onto_splunk(incident_list)


def lambda_handler(event, context):
    # some of these might be redundant 
    ws1_apiKey = os.environ['ws1_apiKey']
    ws1_url = os.environ['ws1_url']
    ws1_clientID = os.environ['ws1_clientID']
    ws1_clientSecret = os.environ['ws1_clientSecret']
    ws1_token_url = os.environ['ws1_token_url']
    
    # get access token via oAuth
    token_body = {
        'grant_type': 'client_credentials',
        'client_id': ws1_clientID,
        'client_secret': ws1_clientSecret
    }

    try:
        token_resp = json.loads(requests.post(ws1_token_url, data=token_body).content)
    except requests.exceptions.HTTPError as e:
        raise e

    access_token = 'Bearer ' + token_resp['access_token']

    headers = {
        'Accept': 'application/json',
        'aw-tenant-code': ws1_apiKey,
        'Authorization': access_token
    }

    try:
        response = json.loads(requests.get(ws1_url, headers=headers).content)
    except requests.exceptions.HTTPError as e:
        raise e

    if len(response['compliancePolicy']) > 0:
        dont_make_an_incident(response['compliancePolicy'])
    
        return {
            'statusCode': 200,
            'body': json.dumps('WS1 to Splunk script exited successfully.')
        }
    else:
        return {
            'statusCode': 200,
            'body': json.dumps('WS1 to Splunk script did not find any compliance data.')
        }
