"""
Tests for test run posting functionality
"""
import pytest
import pytest_spiratest_integration as plugin
from unittest.mock import Mock, patch
import datetime
from urllib.parse import urlparse

class TestTestRunPosting:
    """Test posting test runs to Spira"""
    
    def test_create_test_run(self, reset_plugin_state):
        """Test creating a SpiraTestRun object"""
        start_time = datetime.datetime(2024, 1, 1, 10, 0, 0)
        end_time = datetime.datetime(2024, 1, 1, 10, 0, 5)
        
        test_run = plugin.SpiraTestRun(
            project_id=1,
            test_case_id=100,
            test_name="test_example",
            stack_trace="",
            status_id=2,
            start_time=start_time,
            end_time=end_time,
            message="Test Succeeded",
            release_id=5,
            test_set_id=10
        )
        
        assert test_run.project_id == 1
        assert test_run.test_case_id == 100
        assert test_run.test_name == "test_example"
        assert test_run.status_id == 2
        assert test_run.message == "Test Succeeded"
    
    def test_post_test_run_dry_run(self, spira_config_file, reset_plugin_state, capsys):
        """Test posting in dry-run mode (no actual API call)"""
        config = plugin.getConfig()
        
        # Mock pytest config with dry-run enabled
        mock_pytest_config = Mock()
        mock_pytest_config._spira_dry_run = True
        
        start_time = datetime.datetime(2024, 1, 1, 10, 0, 0)
        end_time = datetime.datetime(2024, 1, 1, 10, 0, 5)
        
        test_run = plugin.SpiraTestRun(
            project_id=1,
            test_case_id=100,
            test_name="test_example",
            stack_trace="",
            status_id=2,
            start_time=start_time,
            end_time=end_time,
            message="Test Succeeded"
        )
        
        # Post should not make actual API call
        test_run.post(config["url"], config["username"], config["token"], config, mock_pytest_config)
        
        # Check that dry-run message was logged
        captured = capsys.readouterr()
        assert "[DRY RUN]" in captured.err
        assert "test_example" in captured.err
    
    @patch('pytest_spiratest_integration.requests.post')
    def test_post_test_run_success(self, mock_post, spira_config_file, reset_plugin_state):
        """Test successful test run posting"""
        config = plugin.getConfig()
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"TestRunId": 12345}'
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        # Mock pytest config
        mock_pytest_config = Mock()
        mock_pytest_config._spira_dry_run = False
        
        start_time = datetime.datetime(2024, 1, 1, 10, 0, 0)
        end_time = datetime.datetime(2024, 1, 1, 10, 0, 5)
        
        test_run = plugin.SpiraTestRun(
            project_id=1,
            test_case_id=100,
            test_name="test_example",
            stack_trace="",
            status_id=2,
            start_time=start_time,
            end_time=end_time,
            message="Test Succeeded"
        )
        
        test_run.post(config["url"], config["username"], config["token"], config, mock_pytest_config)
        
        # Verify API was called
        assert mock_post.called
        call_args = mock_post.call_args
        
        # Check URL
        url = call_args[0][0]
        parsed_url = urlparse(url)
        assert parsed_url.hostname == "test.spira.com"
        assert parsed_url.path.endswith("/projects/1/test-runs/record")
        
        # Check params
        assert call_args[1]['params']['username'] == 'test_user'
        assert call_args[1]['params']['api-key'] == 'test_token'
    
    @patch('pytest_spiratest_integration.requests.post')
    def test_post_test_run_with_release_and_test_set(self, mock_post, spira_config_file, reset_plugin_state):
        """Test posting with release and test set IDs"""
        config = plugin.getConfig()
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"TestRunId": 12345}'
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        mock_pytest_config = Mock()
        mock_pytest_config._spira_dry_run = False
        
        start_time = datetime.datetime(2024, 1, 1, 10, 0, 0)
        end_time = datetime.datetime(2024, 1, 1, 10, 0, 5)
        
        test_run = plugin.SpiraTestRun(
            project_id=1,
            test_case_id=100,
            test_name="test_example",
            stack_trace="",
            status_id=2,
            start_time=start_time,
            end_time=end_time,
            message="Test Succeeded",
            release_id=5,
            test_set_id=10
        )
        
        test_run.post(config["url"], config["username"], config["token"], config, mock_pytest_config)
        
        # Verify release and test set were included
        import json
        call_args = mock_post.call_args
        body = json.loads(call_args[1]['data'])
        
        assert body['ReleaseId'] == 5
        assert body['TestSetId'] == 10
    
    @patch('pytest_spiratest_integration.requests.post')
    def test_post_test_run_failure(self, mock_post, spira_config_file, reset_plugin_state, capsys):
        """Test handling of API failure"""
        config = plugin.getConfig()
        
        # Mock failed response
        from requests.exceptions import HTTPError
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        mock_response.raise_for_status = Mock(side_effect=HTTPError("HTTP 500"))
        mock_post.return_value = mock_response
        
        mock_pytest_config = Mock()
        mock_pytest_config._spira_dry_run = False
        
        start_time = datetime.datetime(2024, 1, 1, 10, 0, 0)
        end_time = datetime.datetime(2024, 1, 1, 10, 0, 5)
        
        test_run = plugin.SpiraTestRun(
            project_id=1,
            test_case_id=100,
            test_name="test_example",
            stack_trace="",
            status_id=2,
            start_time=start_time,
            end_time=end_time,
            message="Test Succeeded"
        )
        
        # Should not raise exception, just log error
        test_run.post(config["url"], config["username"], config["token"], config, mock_pytest_config)
        
        # Check error was logged
        captured = capsys.readouterr()
        assert "ERROR" in captured.err
