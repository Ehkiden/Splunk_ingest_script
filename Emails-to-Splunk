import json
import requests
from datetime import datetime, timedelta
import os

# forward the resulting json to the splunk event collector to be stored
def forward_onto_splunk(incident_list):
    splunk_tenant = os.environ['splunk_tenant']
    splunk_url = f"https://http-inputs-{splunk_tenant}.splunkcloud.com:443/services/collector"
    splunk_hec = os.environ['splunk_hec']
    splunk_headers = {
    'Authorization': f'Splunk {splunk_hec}'
    }
    try:
        splunk_resp = json.loads(requests.post(splunk_url, headers=splunk_headers, json=incident_list).content)
    except requests.exceptions.HTTPError as e:
        raise e
        
    if splunk_resp['text'] == "Success":
        print("Outlook incidents sent to Splunk successfully.")
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
                "sourcetype": "incidents:emails"
            })
    # hehe
    forward_onto_splunk(incident_list)

def token_gains():
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
    return resp["access_token"]

def graph_query(url, aadToken):
    # Grab the token from the response then store it in the headers dict.
    headers = { 
        'Content-Type' : 'application/json',
        'Accept' : 'application/json',
        'Authorization' : "Bearer " + aadToken
    }

    try:
        resp_data = json.loads(requests.get(url, headers=headers).content)
    except requests.exceptions.HTTPError as e:
        raise e
    
    # send the current results to splunk to avoid size limit
    dont_make_an_incident(resp_data)

    try:
        if resp_data['@odata.nextLink']:
            # call the recursive(?) function on itself to go through the next set
            graph_query(resp_data['@odata.nextLink'], aadToken)
    except:
        # once @odata.nextLink is null then we are done
        return 


def lambda_handler(event, context):
    # set last weeks date
    graph_url_base = f'https://graph.microsoft.com/v1.0/users/Jared.Rigdon@rubicon.com/messages?$filter=((from/emailAddress/address) eq \'{email}\' or (from/emailAddress/address) eq \'no-reply@sns.amazonaws.com\')'
    graph_filter = ' and receivedDateTime ge '+ (datetime.today() - timedelta(weeks=1)).strftime("%Y-%m-%d")

    # get auth key
    aadToken = token_gains()

    # get emails from the past last week
    temp_url = graph_url_base+graph_filter
    graph_query(temp_url, aadToken)
    return {
        'statusCode': 200,
        'body': json.dumps('Script exited Successfully!')
    }
