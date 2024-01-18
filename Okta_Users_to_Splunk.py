import requests
import json
import os

'''
Purpose: Gather all non-deactivated users from Okta and send to specific Splunk sourcetype with the goal of creating an up-to-date Okta user list via scheduled search.
    This is due to some users not appearing in sourcetype="OktaIM2:user". 
'''

# forward the resulting json to the splunk event collector to be stored
def forward_onto_splunk(log_list):
    splunk_tenant = os.environ['splunk_tenant']
    splunk_url = f"https://http-inputs-{splunk_tenant}.splunkcloud.com:443/services/collector"
    
    splunk_hec = os.environ['splunk_hec']
    splunk_headers = {
    'Authorization': f'Splunk {splunk_hec}',
    }
    try:
        splunk_resp = json.loads(requests.post(splunk_url, headers=splunk_headers, json=log_list).content)
    except requests.exceptions.HTTPError as e:
        raise e
    if splunk_resp['text'] == "Success":
        print("Okta users list sent to Splunk successfully.")
        print(splunk_resp)
    else:
        print("An error occured during the Splunk POST attempt.")
        print(splunk_resp)

def splunk_format(user_array):
    splunk_logs = []
    for i in user_array:
        # remove unneeded fields/data
        del i['_links']
        del i['credentials']

        splunk_logs.append({
            "event": i,
            "sourcetype": "okta:users:script"
            })

    forward_onto_splunk(splunk_logs)

# recursively gather all the users from the query
def nextpage(url, headers, user_array):
    try:
        resp = requests.get(url, headers=headers)
        resp_data = json.loads(resp.content)
    except requests.exceptions.HTTPError as e:
        print(e)
        pass

    user_array += resp_data

    # check if the next page token exists
    if 'next' in resp.links:
        url = resp.links['next']['url']
        nextpage(url, headers, user_array)

    return user_array

def lambda_handler(event, context):
    okta_tenant = os.environ['okta_tenant']
    okta_domain = f"{okta_tenant}.okta.com"
    search = "search=status lt \"DEPROVISIONED\" or status gt \"DEPROVISIONED\""
    url = "https://" + okta_domain + "/api/v1/users?" + search

    okta_api_key = os.environ['okta_api_key']
    # ref https://developer.okta.com/docs/reference/core-okta-api/#api-token-authentication
    headers = {"Authorization": f"SSWS {okta_api_key}"}

    user_array = []
    user_array_complete = nextpage(url, headers, user_array)
    splunk_format(user_array_complete)

    return {
        'statusCode': 200,
        'body': json.dumps('Script exited Successfully!')
    }
