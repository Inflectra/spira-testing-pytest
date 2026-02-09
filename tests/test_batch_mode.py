"""
Tests for batch mode functionality
"""
import pytest
import pytest_spiratest_integration as plugin
from unittest.mock import Mock, patch
import datetime


class TestBatchMode:
    """Test batch mode posting functionality"""
    
    @patch('pytest_spiratest_integration.requests.post')
    def test_batch_posting(self, mock_post, spira_config_file, reset_plugin_state):
        """Test posting multiple test runs in batch"""
        config = plugin.getConfig()
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '[{"TestRunId": 1}, {"TestRunId": 2}]'
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        # Create test runs
        start_time = datetime.datetime(2024, 1, 1, 10, 0, 0)
        end_time = datetime.datetime(2024, 1, 1, 10, 0, 5)
        
        test_runs = [
            plugin.SpiraTestRun(1, 100, "test_1", "", 2, start_time, end_time),
            plugin.SpiraTestRun(1, 101, "test_2", "", 2, start_time, end_time),
        ]
        
        plugin.post_batch_results(test_runs, config)
        
        # Verify batch API was called
        assert mock_post.called
        call_args = mock_post.call_args
        
        # Check URL contains batch endpoint
        assert "test-runs/record-multiple" in call_args[0][0]
        
        # Check body contains multiple test runs
        import json
        body = json.loads(call_args[1]['data'])
        assert len(body) == 2
    
    @patch('pytest_spiratest_integration.requests.post')
    def test_batch_pagination(self, mock_post, spira_config_file, reset_plugin_state):
        """Test that large batches are split into multiple API calls"""
        config = plugin.getConfig()
        config["batch_size"] = 10  # Small batch size for testing
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '[]'
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        # Create 25 test runs (should be split into 3 batches: 10, 10, 5)
        start_time = datetime.datetime(2024, 1, 1, 10, 0, 0)
        end_time = datetime.datetime(2024, 1, 1, 10, 0, 5)
        
        test_runs = [
            plugin.SpiraTestRun(1, 100 + i, f"test_{i}", "", 2, start_time, end_time)
            for i in range(25)
        ]
        
        plugin.post_batch_results(test_runs, config)
        
        # Should have made 3 API calls
        assert mock_post.call_count == 3
        
        # Verify batch sizes
        import json
        call_1_body = json.loads(mock_post.call_args_list[0][1]['data'])
        call_2_body = json.loads(mock_post.call_args_list[1][1]['data'])
        call_3_body = json.loads(mock_post.call_args_list[2][1]['data'])
        
        assert len(call_1_body) == 10
        assert len(call_2_body) == 10
        assert len(call_3_body) == 5
    
    def test_aggregate_class_results(self, spira_config_file, reset_plugin_state):
        """Test aggregating multiple test results from a class"""
        config = plugin.getConfig()
        
        start_time = datetime.datetime(2024, 1, 1, 10, 0, 0)
        end_time = datetime.datetime(2024, 1, 1, 10, 0, 5)
        
        class_data = {
            'class_name': 'TestExample',
            'test_case_id': 100,
            'results': [
                {
                    'test_name': 'test_1',
                    'status_id': 2,  # Passed
                    'stack_trace': '',
                    'message': 'Test Succeeded',
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': 5.0
                },
                {
                    'test_name': 'test_2',
                    'status_id': 2,  # Passed
                    'stack_trace': '',
                    'message': 'Test Succeeded',
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': 3.0
                },
            ],
            'project_id': 1,
            'release_id': 5,
            'test_set_id': 10
        }
        
        aggregated = plugin.aggregate_class_results(class_data, config)
        
        assert aggregated is not None
        assert aggregated.test_case_id == 100
        assert aggregated.status_id == 2  # All passed
        assert "TestExample" in aggregated.test_name
        assert "2 tests" in aggregated.message
        assert "Passed: 2" in aggregated.message
    
    def test_aggregate_class_results_with_failure(self, spira_config_file, reset_plugin_state):
        """Test aggregating class results with failures"""
        config = plugin.getConfig()
        
        start_time = datetime.datetime(2024, 1, 1, 10, 0, 0)
        end_time = datetime.datetime(2024, 1, 1, 10, 0, 5)
        
        class_data = {
            'class_name': 'TestExample',
            'test_case_id': 100,
            'results': [
                {
                    'test_name': 'test_1',
                    'status_id': 2,  # Passed
                    'stack_trace': '',
                    'message': 'Test Succeeded',
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': 5.0
                },
                {
                    'test_name': 'test_2',
                    'status_id': 1,  # Failed
                    'stack_trace': 'AssertionError: test failed',
                    'message': '',
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': 3.0
                },
            ],
            'project_id': 1,
            'release_id': 5,
            'test_set_id': 10
        }
        
        aggregated = plugin.aggregate_class_results(class_data, config)
        
        assert aggregated.status_id == 1  # Failed (because one test failed)
        assert "Passed: 1" in aggregated.message
        assert "Failed: 1" in aggregated.message
        assert "AssertionError" in aggregated.stack_trace
    
    def test_aggregate_marker_results(self, spira_config_file, reset_plugin_state):
        """Test aggregating results by marker"""
        config = plugin.getConfig()
        
        start_time = datetime.datetime(2024, 1, 1, 10, 0, 0)
        end_time = datetime.datetime(2024, 1, 1, 10, 0, 5)
        
        marker_data = {
            'marker_name': 'smoke',
            'test_case_id': 200,
            'results': [
                {
                    'test_name': 'test_1',
                    'status_id': 2,
                    'stack_trace': '',
                    'message': 'Test Succeeded',
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': 5.0
                },
                {
                    'test_name': 'test_2',
                    'status_id': 2,
                    'stack_trace': '',
                    'message': 'Test Succeeded',
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': 3.0
                },
            ],
            'project_id': 1,
            'release_id': 5,
            'test_set_id': 10
        }
        
        aggregated = plugin.aggregate_marker_results(marker_data, config)
        
        assert aggregated is not None
        assert aggregated.test_case_id == 200
        assert "@smoke" in aggregated.test_name
        assert "2 tests" in aggregated.message
