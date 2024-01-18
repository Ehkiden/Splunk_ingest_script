'''
Purpose: To gather MS defender incidents from the previous day and forward them to Splunk for logging, metrics, and correlation
Author: Jared Rigdon <jared.rigdon@rubicon.com>
Date: 1/31/2023
'''

import json
import requests
from datetime import datetime, timedelta
import os

# forward the resulting json to the splunk event collector to be stored
def forward_onto_splunk(incident_list):
    if len(incident_list) > 5:
        print(incident_list[:5])
    else:
        print(incident_list)
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
        print("MS Defender incidents sent to Splunk successfully.")
        print(splunk_resp)
    else:
        print("An error occured during the Splunk POST attempt.")
        print(splunk_resp)
    x=42    # debug variable

# formats then groups all incidents found into an array of jsons 
def dont_make_an_incident(incident_json):
    incident_list = []
    if len(incident_json['value'])>0:
        for i in incident_json['value']:
            incident_list.append({
                "event": i,
                "sourcetype": "ms365:defender:incident"
            })
    # hehe
    print("Incident List:\n")
    print(incident_list)
    forward_onto_splunk(incident_list)

def make_request(url, headers):
    """
    Makes a GET request.
    :param url: Url of the request.
    :returns: json response.
    :raises HTTPError: raises an exception
    """

    try:
        resp_data = json.loads(requests.get(url, headers=headers).content)
    except requests.exceptions.HTTPError as e:
        raise e

    return resp_data


def lambda_handler(event, context):
    # set the necessary values to obtain the token to access the api
    appId = os.environ['appId']
    appSecret = os.environ['appSecret']
    tenantId = os.environ['tenantId']

    # Azure Active Directory token endpoint.
    url = "https://login.microsoftonline.com/%s/oauth2/v2.0/token" % (tenantId)
    body = {
        'client_id' : appId,
        'client_secret' : appSecret,
        'grant_type' : 'client_credentials',
        'scope': 'https://graph.microsoft.com/.default'
    }

    # authenticate and obtain AAD Token for future calls
    try:
        resp = json.loads(requests.post(url, data=body).content)
    except requests.exceptions.HTTPError as e:
        raise e

    # Grab the token from the response then store it in the headers dict.
    aadToken = resp["access_token"]
    headers = { 
        'Content-Type' : 'application/json',
        'Accept' : 'application/json',
        'Authorization' : "Bearer " + aadToken
    }
    
    print("Token response:\n")
    print(resp)
    
    # get yesterday's date
    # graph_filter = "lastUpdateDateTime gt " + (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    # get last hour's incidents
    graph_filter = "lastUpdateDateTime gt " + (datetime.now() - timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S%z') + "Z"
    
    incidents_url = f"https://graph.microsoft.com/v1.0/security/incidents?$filter={graph_filter}"

    incident_resp = make_request(incidents_url, headers)
    print("Incident Response:\n")
    print(incident_resp)
    if len(incident_resp) > 0:
        dont_make_an_incident(incident_resp)
    
        return {
            'statusCode': 200,
            'body': json.dumps('Defender to Splunk script exited successfully.')
        }
    else:
        return {
            'statusCode': 200,
            'body': json.dumps('Defender to Splunk script did not find any incidents.')
        }
