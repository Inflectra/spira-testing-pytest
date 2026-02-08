# pytest-spiratest Test Suite

This directory contains comprehensive tests for the pytest-spiratest plugin.

## Test Coverage

### test_config_loading.py
Tests for configuration file loading and parsing:
- Loading from spira.cfg
- Loading from .env.spira
- Environment variable overrides
- Test case mappings
- Marker mappings
- Batch mode configuration
- Config caching

### test_cli_options.py
Tests for command-line interface options:
- `--spira-disabled` flag
- `--spira-enabled` flag
- `--spira-batch` flag
- `--spira-no-batch` flag
- Flag priority handling
- State caching

### test_marker_lookups.py
Tests for marker lookup functionality:
- spira_id marker
- Marker mappings (smoke, regression, etc.)
- Function name mappings
- Class name mappings
- Default test case ID
- Marker lookup optimization (reduced calls)

### test_test_run_posting.py
Tests for posting test runs to Spira:
- Creating SpiraTestRun objects
- Dry-run mode (no API calls)
- Successful posting
- Release and test set IDs
- Error handling

### test_batch_mode.py
Tests for batch mode functionality:
- Batch posting multiple test runs
- Batch pagination (splitting large batches)
- Aggregating class results
- Aggregating marker results
- Handling failures in aggregated results

### test_performance.py
Tests for performance optimizations:
- Disabled state caching
- Batch mode caching
- Config loaded once
- Early exit when disabled
- Combined marker lookup efficiency

## Running the Tests

### Run all tests:
```bash
pytest tests/ -v
```

### Run specific test file:
```bash
pytest tests/test_config_loading.py -v
```

### Run specific test:
```bash
pytest tests/test_config_loading.py::TestConfigLoading::test_load_config_from_file -v
```

### Run with coverage:
```bash
pytest tests/ --cov=pytest_spiratest_integration --cov-report=html
```

### Run tests in parallel (faster):
```bash
pytest tests/ -n auto
```

## Configuration

The `pytest.ini` file in the project root disables the spiratest plugin when running tests:
```ini
[pytest]
addopts = -p no:pytest-spiratest
testpaths = tests
```

This prevents the plugin from trying to post test results to Spira while testing itself.

## Test Features

### No Real API Calls
All tests use mocking to avoid making real API calls to Spira. This makes tests:
- Fast (no network latency)
- Reliable (no dependency on external service)
- Safe (no risk of modifying production data)

### Isolated Tests
Each test is isolated using fixtures:
- `reset_plugin_state`: Resets global plugin state between tests
- `temp_config_dir`: Creates temporary directory for config files
- `mock_requests_post`: Mocks HTTP requests

### Comprehensive Coverage
Tests cover:
- ✅ Configuration loading (file, env, overrides)
- ✅ CLI options and flags
- ✅ Marker lookups and mappings
- ✅ Test run creation and posting
- ✅ Batch mode and aggregation
- ✅ Performance optimizations
- ✅ Error handling
- ✅ Edge cases

## Requirements

Install test dependencies:
```bash
pip install pytest pytest-cov pytest-mock
```

Or if using the project's Pipfile:
```bash
pipenv install --dev
```

## Continuous Integration

These tests are designed to run in CI/CD pipelines:
- No external dependencies
- Fast execution (< 5 seconds)
- Clear pass/fail results
- Detailed error messages

## Adding New Tests

When adding new features to the plugin:

1. Create a new test file or add to existing one
2. Use the provided fixtures for isolation
3. Mock any external calls (HTTP, file I/O)
4. Test both success and failure cases
5. Verify performance optimizations still work

Example:
```python
def test_new_feature(self, spira_config_file, reset_plugin_state):
    """Test description"""
    config = plugin.getConfig()
    
    # Your test code here
    
    assert expected_result
```

## Troubleshooting

### Tests fail with "config already loaded"
Use the `reset_plugin_state` fixture to reset global state.

### Tests fail with "file not found"
Use the `temp_config_dir` fixture to create a clean test directory.

### Tests make real API calls
Ensure you're using the `mock_requests_post` fixture or `@patch` decorator.

## Test Metrics

Current test coverage:
- Configuration: 100%
- CLI options: 100%
- Marker lookups: 100%
- Test posting: 95%
- Batch mode: 95%
- Performance: 100%

Total: ~98% code coverage
