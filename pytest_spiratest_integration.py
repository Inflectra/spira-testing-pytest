import requests
import json
import time

def pytest_runtest_makereport(item, call, __multicall__):
    report = __multicall__.execute()
    if report.when == "call":
        print(str(report))
        status_id = -1
        start_time = time.time() - report.duration
        test_name = report.location
        stack_trace = report.longreprtext
        message = ""

        if report.outcome == "passed":
            # 2 is passed
            status_id = 2
            message = "Test Succeeded"
        elif report.outcome == "skipped":
            # 3 is not run
            status_id = 3
            message = "Test Skipped"
        elif report.outcome == "failed":
            #1 is failed
            status_id = 1
            message = ""
        print("status: " + str(status_id))
        print("name: " + str(test_name))
        print("trace: " + str(stack_trace))
        print("Keywords: " + str(report.keywords))
        print("user props: " + str(report.user_properties))
        print("sections: " + str(report.sections))


    return report

# The URL snippet used after the Spira URL
REST_SERVICE_URL = "/Services/v5_0/RestService.svc/"
# The URL spippet used to post an automated test run. Needs the project ID to work
POST_TEST_RUN = "projects/%s/test-runs/record"

# Returns an Inflectra formatted date based on the seconds passed in (obtained by time.time())
def format_date(seconds):
    millis = int(round(seconds * 1000))
    offset = time.timezone / 3600
    return '/Date(' + str(millis) + '-0' + str(offset) + '00)/'    

# Name of this extension
RUNNER_NAME = "PyTest"

"""
A TestRun object model for Spira
"""
class SpiraTestRun:
    project_id = -1
    test_case_id = -1
    test_name = ""
    stack_trace = ""
    status_id = -1
    start_time = -1
    message = ""
    release_id = -1
    test_set_id = -1
    
    def __init__(self, project_id, test_case_id, test_name, stack_trace, status_id, start_time, message = '', release_id = -1, test_set_id = -1):
        self.project_id = project_id
        self.test_case_id = test_case_id
        self.test_name = test_name
        self.stack_trace = stack_trace
        self.status_id = status_id
        self.start_time = start_time
        self.message = message
        self.release_id = release_id
        self.test_set_id = test_set_id
    
    def post(self, spira_url, spira_username, spira_token):
        """
        Post the test run to Spira with the given credentials
        """
        url = spira_url + REST_SERVICE_URL + (POST_TEST_RUN % self.project_id)
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
            'StartDate': format_date(self.start_time),
            'RunnerName': RUNNER_NAME,
            'RunnerTestName': self.test_name,
            'RunnerMessage': self.message,
            'RunnerStackTrace': self.stack_trace,
            'TestCaseId': self.test_case_id,
            # Passes (2) if the stack trace length is 0
            'ExecutionStatusId': self.status_id
        }

        # Releases and Test Sets are optional
        if(self.release_id != -1) :
            json.release_id = self.release_id
        if(self.test_set_id != -1):
            json.test_set_id = self.test_set_id
            
        request = requests.post(url, data = json.dumps(body), params = params, headers = headers)
