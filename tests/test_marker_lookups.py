"""
Tests for marker lookup optimization
"""
import pytest
import pytest_spiratest_integration as plugin
from unittest.mock import Mock, MagicMock


class TestMarkerLookups:
    """Test marker lookup functionality and optimization"""
    
    def test_get_test_case_id_with_spira_id_marker(self, spira_config_file, reset_plugin_state):
        """Test getting test case ID from spira_id marker"""
        config = plugin.getConfig()
        
        # Mock item with spira_id marker
        mock_item = Mock()
        mock_marker = Mock()
        mock_marker.args = [999]
        mock_item.get_closest_marker = Mock(side_effect=lambda name: mock_marker if name == "spira_id" else None)
        mock_item.cls = None
        
        test_case_id, mapping_source = plugin.get_test_case_id_and_source(mock_item, "test_example", config)
        
        assert test_case_id == 999
        assert mapping_source['type'] == 'spira_id'
        # Should only call get_closest_marker once for spira_id
        assert mock_item.get_closest_marker.call_count == 1
    
    def test_get_test_case_id_with_marker_mapping(self, spira_config_file, reset_plugin_state):
        """Test getting test case ID from marker mapping"""
        config = plugin.getConfig()
        
        # Mock item with smoke marker
        mock_item = Mock()
        mock_smoke_marker = Mock()
        mock_item.get_closest_marker = Mock(side_effect=lambda name: mock_smoke_marker if name == "smoke" else None)
        mock_item.cls = None
        
        test_case_id, mapping_source = plugin.get_test_case_id_and_source(mock_item, "test_example", config)
        
        assert test_case_id == "200"  # smoke marker maps to 200
        assert mapping_source['type'] == 'marker'
        assert mapping_source['marker_name'] == 'smoke'
    
    def test_get_test_case_id_from_function_name(self, spira_config_file, reset_plugin_state):
        """Test getting test case ID from function name mapping"""
        config = plugin.getConfig()
        
        # Mock item without markers
        mock_item = Mock()
        mock_item.get_closest_marker = Mock(return_value=None)
        mock_item.cls = None
        
        test_case_id, mapping_source = plugin.get_test_case_id_and_source(mock_item, "test_example", config)
        
        assert test_case_id == "101"  # test_example maps to 101
        assert mapping_source['type'] == 'function'
    
    def test_get_test_case_id_from_class_name(self, spira_config_file, reset_plugin_state):
        """Test getting test case ID from class name mapping"""
        config = plugin.getConfig()
        
        # Mock item with class but no function mapping
        mock_item = Mock()
        mock_item.get_closest_marker = Mock(return_value=None)
        mock_item.cls = Mock()
        mock_item.cls.__name__ = "TestClass"
        
        test_case_id, mapping_source = plugin.get_test_case_id_and_source(mock_item, "test_unknown", config)
        
        assert test_case_id == "102"  # testclass maps to 102
        assert mapping_source['type'] == 'class'
    
    def test_get_test_case_id_default(self, spira_config_file, reset_plugin_state):
        """Test getting default test case ID"""
        config = plugin.getConfig()
        
        # Mock item with no markers, no class, no function mapping
        mock_item = Mock()
        mock_item.get_closest_marker = Mock(return_value=None)
        mock_item.cls = None
        
        test_case_id, mapping_source = plugin.get_test_case_id_and_source(mock_item, "test_unknown", config)
        
        assert test_case_id == "100"  # default
        assert mapping_source['type'] == 'default'
    
    def test_marker_lookup_optimization(self, spira_config_file, reset_plugin_state):
        """Test that marker lookups are optimized (not called multiple times)"""
        config = plugin.getConfig()
        
        # Mock item
        mock_item = Mock()
        call_count = 0
        
        def mock_get_marker(name):
            nonlocal call_count
            call_count += 1
            return None
        
        mock_item.get_closest_marker = Mock(side_effect=mock_get_marker)
        mock_item.cls = None
        
        # Call the combined function
        test_case_id, mapping_source = plugin.get_test_case_id_and_source(mock_item, "test_unknown", config)
        
        # Should call get_closest_marker for:
        # 1. spira_id
        # 2. smoke (first marker mapping)
        # 3. regression (second marker mapping)
        # Total: 3 calls (not 6+ like before optimization)
        assert call_count == 3
    
    def test_empty_marker_mappings(self, temp_config_dir, reset_plugin_state):
        """Test behavior with no marker mappings configured"""
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
        
        # Mock item
        mock_item = Mock()
        mock_item.get_closest_marker = Mock(return_value=None)
        mock_item.cls = None
        
        test_case_id, mapping_source = plugin.get_test_case_id_and_source(mock_item, "test_unknown", config)
        
        # Should only check spira_id marker (not iterate through empty marker_mappings)
        assert mock_item.get_closest_marker.call_count == 1
        assert test_case_id == "100"
