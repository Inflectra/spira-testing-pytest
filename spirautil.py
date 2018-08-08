# Utilities for use within the Spira extension

import requests
import json
import time

# The URL snippet used after the Spira URL
REST_SERVICE_URL = "/Services/v5_0/RestService.svc/"
# The URL spippet used to post an automated test run. Needs the project ID to work
POST_TEST_RUN = "projects/%s/test-runs/record"

# Name of this extension
RUNNER_NAME = "PyTest"
 
# Returns an Inflectra formatted date based on the current time
def format_date():
    millis = int(round(time.time() * 1000))
    offset = time.timezone / 3600
    return '/Date(' + str(millis) + '-0' + str(offset) + '00)/'

def post_test_run(spira_url, spira_username, spira_token, project_id, test_case_id, test_name, stack_trace, message = '', release_id = -1, test_set_id = -1) :
    url = spira_url + REST_SERVICE_URL + (POST_TEST_RUN % project_id)
    # The credentials we need
    params = {
        'username': spira_username,
        'api-key': spira_token
    }

    # The headers we are sending to the server
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
        'User-Agent': RUNNER_NAME
    }

    # The body we are sending
    body = {
        # Constant for plain text
        'TestRunFormatId': 1,
        'StartDate': format_date(),
        'RunnerName': RUNNER_NAME,
        'RunnerTestName': test_name,
        'RunnerMessage': message,
        'RunnerStackTrace': stack_trace,
        'TestCaseId': test_case_id,
        # Passes (2) if the stack trace length is 0
        'ExecutionStatusId': 2 if len(stack_trace) == 0 else 1
    }

    # Releases and Test Sets are optional
    if(release_id != -1) :
        json.release_id = release_id
    if(test_set_id != -1):
        json.test_set_id =test_set_id
        
    request = requests.post(url, data = json.dumps(body), params = params, headers = headers)
    url = request.url
    status = request.status_code
    j = request.text
        
        

url = "https://demo.spiraservice.net/peter-inflectra"
username = "administrator"
key = "{90250D72-4526-4889-B670-0290BF63BC24}"
post_test_run(url, username, key, 1, 20, "test_test()", "")        
