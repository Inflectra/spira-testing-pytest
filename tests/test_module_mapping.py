"""
Tests for module-level mapping functionality
"""
import pytest
import pytest_spiratest_integration as plugin
from unittest.mock import Mock, MagicMock


class TestModuleMapping:
    """Test module-level mapping functionality"""
    
    def test_get_test_case_id_from_module_name(self, temp_config_dir, reset_plugin_state):
        """Test getting test case ID from module name mapping"""
        config_content = """[credentials]
url = http://test.spira.com
username = test_user
token = test_token
project_id = 1

[test_cases]
default = 100

[modules]
test_example_module = 300
tests.integration.test_api = 301
"""
        config_file = temp_config_dir / "spira.cfg"
        config_file.write_text(config_content)
        
        config = plugin.getConfig()
        
        # Mock item with module but no other mappings
        mock_item = Mock()
        mock_item.get_closest_marker = Mock(return_value=None)
        mock_item.cls = None
        mock_item.module = Mock()
        mock_item.module.__name__ = "test_example_module"
        
        test_case_id, mapping_source = plugin.get_test_case_id_and_source(mock_item, "test_unknown", config)
        
        assert test_case_id == "300"
        assert mapping_source['type'] == 'module'
        assert mapping_source['module_name'] == 'test_example_module'
    
    def test_get_test_case_id_from_dotted_module_path(self, temp_config_dir, reset_plugin_state):
        """Test getting test case ID from dotted module path"""
        config_content = """[credentials]
url = http://test.spira.com
username = test_user
token = test_token
project_id = 1

[test_cases]
default = 100

[modules]
tests.integration.test_api = 301
"""
        config_file = temp_config_dir / "spira.cfg"
        config_file.write_text(config_content)
        
        config = plugin.getConfig()
        
        # Mock item with dotted module path
        mock_item = Mock()
        mock_item.get_closest_marker = Mock(return_value=None)
        mock_item.cls = None
        mock_item.module = Mock()
        mock_item.module.__name__ = "tests.integration.test_api"
        
        test_case_id, mapping_source = plugin.get_test_case_id_and_source(mock_item, "test_unknown", config)
        
        assert test_case_id == "301"
        assert mapping_source['type'] == 'module'
        assert mapping_source['module_name'] == 'tests.integration.test_api'
    
    def test_module_mapping_case_insensitive(self, temp_config_dir, reset_plugin_state):
        """Test that module mapping is case-insensitive"""
        config_content = """[credentials]
url = http://test.spira.com
username = test_user
token = test_token
project_id = 1

[test_cases]
default = 100

[modules]
TestExampleModule = 300
"""
        config_file = temp_config_dir / "spira.cfg"
        config_file.write_text(config_content)
        
        config = plugin.getConfig()
        
        # Mock item with different case
        mock_item = Mock()
        mock_item.get_closest_marker = Mock(return_value=None)
        mock_item.cls = None
        mock_item.module = Mock()
        mock_item.module.__name__ = "testexamplemodule"
        
        test_case_id, mapping_source = plugin.get_test_case_id_and_source(mock_item, "test_unknown", config)
        
        assert test_case_id == "300"
        assert mapping_source['type'] == 'module'
    
    def test_module_mapping_priority_lower_than_function(self, temp_config_dir, reset_plugin_state):
        """Test that function-level mapping has higher priority than module mapping"""
        config_content = """[credentials]
url = http://test.spira.com
username = test_user
token = test_token
project_id = 1

[test_cases]
default = 100
test_example = 200

[modules]
test_example_module = 300
"""
        config_file = temp_config_dir / "spira.cfg"
        config_file.write_text(config_content)
        
        config = plugin.getConfig()
        
        # Mock item with both function and module mapping
        mock_item = Mock()
        mock_item.get_closest_marker = Mock(return_value=None)
        mock_item.cls = None
        mock_item.module = Mock()
        mock_item.module.__name__ = "test_example_module"
        
        test_case_id, mapping_source = plugin.get_test_case_id_and_source(mock_item, "test_example", config)
        
        # Function mapping should win
        assert test_case_id == "200"
        assert mapping_source['type'] == 'function'
    
    def test_module_mapping_priority_lower_than_class(self, temp_config_dir, reset_plugin_state):
        """Test that class-level mapping has higher priority than module mapping"""
        config_content = """[credentials]
url = http://test.spira.com
username = test_user
token = test_token
project_id = 1

[test_cases]
default = 100
TestClass = 200

[modules]
test_example_module = 300
"""
        config_file = temp_config_dir / "spira.cfg"
        config_file.write_text(config_content)
        
        config = plugin.getConfig()
        
        # Mock item with both class and module mapping
        mock_item = Mock()
        mock_item.get_closest_marker = Mock(return_value=None)
        mock_item.cls = Mock()
        mock_item.cls.__name__ = "TestClass"
        mock_item.module = Mock()
        mock_item.module.__name__ = "test_example_module"
        
        test_case_id, mapping_source = plugin.get_test_case_id_and_source(mock_item, "test_unknown", config)
        
        # Class mapping should win
        assert test_case_id == "200"
        assert mapping_source['type'] == 'class'
    
    def test_module_mapping_priority_lower_than_marker(self, temp_config_dir, reset_plugin_state):
        """Test that marker mapping has higher priority than module mapping"""
        config_content = """[credentials]
url = http://test.spira.com
username = test_user
token = test_token
project_id = 1

[test_cases]
default = 100

[markers]
smoke = 200

[modules]
test_example_module = 300
"""
        config_file = temp_config_dir / "spira.cfg"
        config_file.write_text(config_content)
        
        config = plugin.getConfig()
        
        # Mock item with both marker and module mapping
        mock_item = Mock()
        mock_smoke_marker = Mock()
        mock_item.get_closest_marker = Mock(side_effect=lambda name: mock_smoke_marker if name == "smoke" else None)
        mock_item.cls = None
        mock_item.module = Mock()
        mock_item.module.__name__ = "test_example_module"
        
        test_case_id, mapping_source = plugin.get_test_case_id_and_source(mock_item, "test_unknown", config)
        
        # Marker mapping should win
        assert test_case_id == "200"
        assert mapping_source['type'] == 'marker'
    
    def test_module_mapping_priority_higher_than_default(self, temp_config_dir, reset_plugin_state):
        """Test that module mapping has higher priority than default"""
        config_content = """[credentials]
url = http://test.spira.com
username = test_user
token = test_token
project_id = 1

[test_cases]
default = 100

[modules]
test_example_module = 300
"""
        config_file = temp_config_dir / "spira.cfg"
        config_file.write_text(config_content)
        
        config = plugin.getConfig()
        
        # Mock item with only module mapping
        mock_item = Mock()
        mock_item.get_closest_marker = Mock(return_value=None)
        mock_item.cls = None
        mock_item.module = Mock()
        mock_item.module.__name__ = "test_example_module"
        
        test_case_id, mapping_source = plugin.get_test_case_id_and_source(mock_item, "test_unknown", config)
        
        # Module mapping should win over default
        assert test_case_id == "300"
        assert mapping_source['type'] == 'module'
    
    def test_no_module_mapping_falls_to_default(self, temp_config_dir, reset_plugin_state):
        """Test that unmapped module falls through to default"""
        config_content = """[credentials]
url = http://test.spira.com
username = test_user
token = test_token
project_id = 1

[test_cases]
default = 100

[modules]
test_other_module = 300
"""
        config_file = temp_config_dir / "spira.cfg"
        config_file.write_text(config_content)
        
        config = plugin.getConfig()
        
        # Mock item with unmapped module
        mock_item = Mock()
        mock_item.get_closest_marker = Mock(return_value=None)
        mock_item.cls = None
        mock_item.module = Mock()
        mock_item.module.__name__ = "test_unmapped_module"
        
        test_case_id, mapping_source = plugin.get_test_case_id_and_source(mock_item, "test_unknown", config)
        
        # Should fall through to default
        assert test_case_id == "100"
        assert mapping_source['type'] == 'default'
    
    def test_empty_module_mappings(self, temp_config_dir, reset_plugin_state):
        """Test behavior with no module mappings configured"""
        config_content = """[credentials]
url = http://test.spira.com
username = test_user
token = test_token
project_id = 1

[test_cases]
default = 100
"""
        config_file = temp_config_dir / "spira.cfg"
        config_file.write_text(config_content)
        
        config = plugin.getConfig()
        
        # Mock item with module
        mock_item = Mock()
        mock_item.get_closest_marker = Mock(return_value=None)
        mock_item.cls = None
        mock_item.module = Mock()
        mock_item.module.__name__ = "test_example_module"
        
        test_case_id, mapping_source = plugin.get_test_case_id_and_source(mock_item, "test_unknown", config)
        
        # Should use default when no module mappings exist
        assert test_case_id == "100"
        assert mapping_source['type'] == 'default'
    
    def test_module_aggregation_data_structure(self, temp_config_dir, reset_plugin_state):
        """Test that module aggregation creates correct data structure"""
        config_content = """[credentials]
url = http://test.spira.com
username = test_user
token = test_token
project_id = 1
release_id = 5
test_set_id = 10

[test_cases]
default = 100

[modules]
test_example_module = 300
"""
        config_file = temp_config_dir / "spira.cfg"
        config_file.write_text(config_content)
        
        config = plugin.getConfig()
        
        # Create module aggregation data
        module_data = {
            'module_name': 'test_example_module',
            'test_case_id': '300',
            'results': [
                {
                    'test_name': 'test_one',
                    'status_id': 2,
                    'stack_trace': '',
                    'message': 'Test Succeeded',
                    'start_time': plugin.datetime.datetime(2024, 1, 1, 10, 0, 0),
                    'end_time': plugin.datetime.datetime(2024, 1, 1, 10, 0, 1),
                    'duration': 1.0
                },
                {
                    'test_name': 'test_two',
                    'status_id': 2,
                    'stack_trace': '',
                    'message': 'Test Succeeded',
                    'start_time': plugin.datetime.datetime(2024, 1, 1, 10, 0, 1),
                    'end_time': plugin.datetime.datetime(2024, 1, 1, 10, 0, 2),
                    'duration': 1.0
                }
            ],
            'project_id': 1,
            'release_id': 5,
            'test_set_id': 10
        }
        
        # Aggregate the results
        aggregated_run = plugin.aggregate_module_results(module_data, config)
        
        assert aggregated_run is not None
        assert aggregated_run.test_case_id == '300'
        assert aggregated_run.test_name == 'test_example_module'
        assert aggregated_run.status_id == 2  # Passed
        assert aggregated_run.project_id == 1
        assert aggregated_run.release_id == 5
        assert aggregated_run.test_set_id == 10
        assert 'Module: test_example_module' in aggregated_run.message
        assert 'Total: 2 tests' in aggregated_run.message
        assert 'Passed: 2' in aggregated_run.message
    
    def test_module_aggregation_with_failures(self, temp_config_dir, reset_plugin_state):
        """Test that module aggregation correctly handles failures"""
        config_content = """[credentials]
url = http://test.spira.com
username = test_user
token = test_token
project_id = 1

[test_cases]
default = 100

[modules]
test_example_module = 300
"""
        config_file = temp_config_dir / "spira.cfg"
        config_file.write_text(config_content)
        
        config = plugin.getConfig()
        
        # Create module aggregation data with failures
        module_data = {
            'module_name': 'test_example_module',
            'test_case_id': '300',
            'results': [
                {
                    'test_name': 'test_pass',
                    'status_id': 2,
                    'stack_trace': '',
                    'message': 'Test Succeeded',
                    'start_time': plugin.datetime.datetime(2024, 1, 1, 10, 0, 0),
                    'end_time': plugin.datetime.datetime(2024, 1, 1, 10, 0, 1),
                    'duration': 1.0
                },
                {
                    'test_name': 'test_fail',
                    'status_id': 1,
                    'stack_trace': 'AssertionError: test failed',
                    'message': '',
                    'start_time': plugin.datetime.datetime(2024, 1, 1, 10, 0, 1),
                    'end_time': plugin.datetime.datetime(2024, 1, 1, 10, 0, 2),
                    'duration': 1.0
                }
            ],
            'project_id': 1,
            'release_id': -1,
            'test_set_id': -1
        }
        
        # Aggregate the results
        aggregated_run = plugin.aggregate_module_results(module_data, config)
        
        assert aggregated_run is not None
        assert aggregated_run.status_id == 1  # Failed (because one test failed)
        assert 'Passed: 1' in aggregated_run.message
        assert 'Failed: 1' in aggregated_run.message
        assert '[PASSED] test_pass' in aggregated_run.message
        assert '[FAILED] test_fail' in aggregated_run.message
        assert 'AssertionError: test failed' in aggregated_run.stack_trace
    
    def test_no_default_returns_none(self, temp_config_dir, reset_plugin_state):
        """Test that unmapped test returns None when no default is configured"""
        config_content = """[credentials]
url = http://test.spira.com
username = test_user
token = test_token
project_id = 1

[test_cases]
test_mapped = 100
"""
        config_file = temp_config_dir / "spira.cfg"
        config_file.write_text(config_content)
        
        config = plugin.getConfig()
        
        # Mock item with no mapping
        mock_item = Mock()
        mock_item.get_closest_marker = Mock(return_value=None)
        mock_item.cls = None
        mock_item.module = Mock()
        mock_item.module.__name__ = "test_unmapped_module"
        
        test_case_id, mapping_source = plugin.get_test_case_id_and_source(mock_item, "test_unmapped", config)
        
        # Should return None when no default
        assert test_case_id is None
        assert mapping_source['type'] == 'unmapped'
    
    def test_with_default_returns_default(self, temp_config_dir, reset_plugin_state):
        """Test that unmapped test returns default when default is configured"""
        config_content = """[credentials]
url = http://test.spira.com
username = test_user
token = test_token
project_id = 1

[test_cases]
default = 100
test_mapped = 200
"""
        config_file = temp_config_dir / "spira.cfg"
        config_file.write_text(config_content)
        
        config = plugin.getConfig()
        
        # Mock item with no mapping
        mock_item = Mock()
        mock_item.get_closest_marker = Mock(return_value=None)
        mock_item.cls = None
        mock_item.module = Mock()
        mock_item.module.__name__ = "test_unmapped_module"
        
        test_case_id, mapping_source = plugin.get_test_case_id_and_source(mock_item, "test_unmapped", config)
        
        # Should return default
        assert test_case_id == "100"
        assert mapping_source['type'] == 'default'
