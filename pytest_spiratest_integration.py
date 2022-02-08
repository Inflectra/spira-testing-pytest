import requests
import json
import datetime
import time
import configparser
import pytest

'''
The config is only retrieved once
'''
config = None

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == "call":
        config = getConfig()
        # Only do stuff if config is specified
        if config["url"] != "":
            status_id = -1
            current_time = datetime.datetime.utcnow()
            # The function name
            test_name = report.location[2].lower()
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

            # Get the test case id if specified, otherwise use the default
            if test_name in config["test_case_ids"]:
                test_case_id = config["test_case_ids"][test_name.lower()]
            else:
                test_case_id = config["test_case_ids"]["default"]

            # Create the test run
            test_run = SpiraTestRun(
                config["project_id"], 
                test_case_id, 
                test_name, 
                stack_trace, 
                status_id, 
                current_time - datetime.timedelta(seconds=report.duration), 
                current_time,
                message=message, 
                release_id=config["release_id"], 
                test_set_id=config["test_set_id"]
            )
            # Post the test run!
            test_run.post(config["url"], config["username"], config["token"])

    return report


def getConfig():
    global config
    # Only retrieve config once
    if config is None:
        # Model of config object:
        config = {
            "url": "",
            "username": "",
            "token": "",
            "project_id": -1,
            "release_id": -1,
            "test_set_id": -1,
            "test_case_ids": {
                "default": -1
            }
        }
        # Parse the config file
        parser = configparser.ConfigParser()
        parser.read("spira.cfg")

        sections = parser.sections()

        # Process Configs
        for section in sections:
            # Handle credentials and test case mappings differently
            if section == "credentials":
                for (key, value) in parser.items(section):
                    config[key] = value
            elif section == "test_cases":
                for (key, value) in parser.items(section):
                    config["test_case_ids"][key.lower()] = value
    return config


# Name of this extension
RUNNER_NAME = "PyTest"


class SpiraTestRun:
    # The URL snippet used after the Spira URL
    REST_SERVICE_URL = "/Services/v6_0/RestService.svc/"
    # The URL spippet used to post an automated test run. Needs the project ID to work
    POST_TEST_RUN = "projects/%s/test-runs/record"
    '''
    A TestRun object model for Spira
    '''
    project_id = -1
    test_case_id = -1
    test_name = ""
    stack_trace = ""
    status_id = -1
    start_time = -1
    end_time = -1
    message = ""
    release_id = -1
    test_set_id = -1

    def __init__(self, project_id, test_case_id, test_name, stack_trace, status_id, start_time, end_time, message='', release_id=-1, test_set_id=-1):
        self.project_id = project_id
        self.test_case_id = test_case_id
        self.test_name = test_name
        self.stack_trace = stack_trace
        self.status_id = status_id
        self.start_time = start_time
        self.end_time = end_time
        self.message = message
        self.release_id = release_id
        self.test_set_id = test_set_id

    def post(self, spira_url, spira_username, spira_token):
        """
        Post the test run to Spira with the given credentials
        """
        url = spira_url + self.REST_SERVICE_URL + \
            (self.POST_TEST_RUN % self.project_id)
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
            'StartDate': self.start_time.isoformat(),
            'EndDate': self.end_time.isoformat(),
            'RunnerName': RUNNER_NAME,
            'RunnerTestName': self.test_name,
            'RunnerMessage': self.message,
            'RunnerStackTrace': self.stack_trace,
            'TestCaseId': self.test_case_id,
            # Passes (2) if the stack trace length is 0
            'ExecutionStatusId': self.status_id
        }

        # Releases and Test Sets are optional
        if(self.release_id != -1):
            body["ReleaseId"] = int(self.release_id)
        if(self.test_set_id != -1):
            body["TestSetId"] = int(self.test_set_id)

        dumps = json.dumps(body)

        request = requests.post(url, data=json.dumps(
            body), params=params, headers=headers)
