"""
Pytest configuration and fixtures for testing pytest-spiratest plugin
"""
import pytest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary directory for config files"""
    config_dir = tmp_path / "test_config"
    config_dir.mkdir()
    original_dir = os.getcwd()
    os.chdir(config_dir)
    yield config_dir
    os.chdir(original_dir)


@pytest.fixture
def mock_spira_config():
    """Create a mock Spira configuration"""
    return {
        "url": "http://test.spira.com",
        "username": "test_user",
        "token": "test_token",
        "project_id": 1,
        "release_id": 5,
        "test_set_id": 10,
        "test_case_ids": {
            "default": 100,
            "test_example": 101,
            "testclass": 102
        },
        "marker_mappings": {
            "smoke": 200,
            "regression": 201
        },
        "verbose": False,
        "enabled": True,
        "batch_mode": False,
        "batch_size": 500
    }


@pytest.fixture
def spira_config_file(temp_config_dir):
    """Create a test spira.cfg file"""
    config_content = """[credentials]
url = http://test.spira.com
username = test_user
token = test_token
project_id = 1
release_id = 5
test_set_id = 10

[test_cases]
default = 100
test_example = 101
testclass = 102

[markers]
smoke = 200
regression = 201

[settings]
enabled = true
verbose = false
batch_mode = false
"""
    config_file = temp_config_dir / "spira.cfg"
    config_file.write_text(config_content)
    return config_file


@pytest.fixture
def disabled_config_file(temp_config_dir):
    """Create a disabled spira.cfg file"""
    config_content = """[credentials]
url = http://test.spira.com
username = test_user
token = test_token
project_id = 1

[test_cases]
default = 100

[settings]
enabled = false
"""
    config_file = temp_config_dir / "spira.cfg"
    config_file.write_text(config_content)
    return config_file


@pytest.fixture
def mock_requests_post():
    """Mock requests.post to avoid real API calls"""
    with patch('pytest_spiratest_integration.requests.post') as mock_post:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"TestRunId": 12345}'
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        yield mock_post


@pytest.fixture
def reset_plugin_state():
    """Reset global plugin state between tests"""
    import pytest_spiratest_integration as plugin
    
    # Store original values
    original_config = plugin.config
    original_disabled = plugin.spira_disabled
    original_batch_cache = plugin._batch_mode_cache
    original_enabled_cache = plugin._spira_enabled_cache
    original_results_queue = plugin.test_results_queue.copy()
    original_class_results = plugin.class_test_results.copy()
    original_marker_results = plugin.marker_test_results.copy()
    
    yield
    
    # Reset to original values
    plugin.config = None
    plugin.config_loaded = False
    plugin.spira_disabled = False
    plugin._batch_mode_cache = None
    plugin._spira_enabled_cache = None
    plugin.test_results_queue.clear()
    plugin.class_test_results.clear()
    plugin.marker_test_results.clear()


@pytest.fixture(autouse=True)
def cleanup_after_test(reset_plugin_state):
    """Automatically cleanup after each test"""
    yield
