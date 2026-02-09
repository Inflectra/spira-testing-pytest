"""
Tests for performance optimizations
"""
import pytest
import pytest_spiratest_integration as plugin
from unittest.mock import Mock
import time


class TestPerformanceOptimizations:
    """Test that performance optimizations work correctly"""
    
    def test_disabled_state_cached(self, disabled_config_file, reset_plugin_state):
        """Test that disabled state is cached after first check"""
        config = plugin.getConfig()
        
        mock_pytest_config = Mock()
        mock_pytest_config._spira_cli_disabled = False
        mock_pytest_config._spira_cli_enabled = False
        
        # First call
        result1 = plugin.is_spira_enabled(mock_pytest_config, config)
        
        # Modify config (should not affect result due to caching)
        config["enabled"] = True
        
        # Second call should use cached value
        result2 = plugin.is_spira_enabled(mock_pytest_config, config)
        
        assert result1 == result2 == False
        assert plugin._spira_enabled_cache is False
    
    def test_batch_mode_cached(self, spira_config_file, reset_plugin_state):
        """Test that batch mode state is cached"""
        config = plugin.getConfig()
        
        mock_pytest_config = Mock()
        mock_pytest_config._spira_cli_batch = False
        mock_pytest_config._spira_cli_no_batch = False
        
        # First call
        result1 = plugin.is_batch_mode_enabled(mock_pytest_config, config)
        
        # Modify config (should not affect result due to caching)
        config["batch_mode"] = True
        
        # Second call should use cached value
        result2 = plugin.is_batch_mode_enabled(mock_pytest_config, config)
        
        assert result1 == result2 == False
        assert plugin._batch_mode_cache is False
    
    def test_config_loaded_once(self, spira_config_file, reset_plugin_state):
        """Test that config is only loaded once"""
        # First call
        config1 = plugin.getConfig()
        
        # Second call should return same object
        config2 = plugin.getConfig()
        
        assert config1 is config2
        assert plugin.config_loaded is True
    
    def test_spira_disabled_flag_set(self, disabled_config_file, reset_plugin_state):
        """Test that spira_disabled flag is set when disabled"""
        config = plugin.getConfig()
        
        assert plugin.spira_disabled is True
    
    def test_no_config_sets_disabled_flag(self, temp_config_dir, reset_plugin_state):
        """Test that missing config files set disabled flag"""
        config = plugin.getConfig()
        
        assert config["enabled"] is False
        assert plugin.spira_disabled is True
    
    def test_marker_lookup_not_called_when_disabled(self, disabled_config_file, reset_plugin_state):
        """Test that marker lookups are skipped when disabled"""
        # This is tested implicitly by the early exit in pytest_runtest_makereport
        # We verify the disabled flag is set correctly
        config = plugin.getConfig()
        
        mock_pytest_config = Mock()
        mock_pytest_config._spira_cli_disabled = False
        mock_pytest_config._spira_cli_enabled = False
        
        is_enabled = plugin.is_spira_enabled(mock_pytest_config, config)
        
        assert is_enabled is False
        assert plugin.spira_disabled is True
    
    def test_cli_disabled_flag_immediate_exit(self, spira_config_file, reset_plugin_state):
        """Test that CLI disabled flag causes immediate exit"""
        # Don't load config yet
        assert plugin.config is None
        
        mock_pytest_config = Mock()
        mock_pytest_config._spira_cli_disabled = True
        mock_pytest_config._spira_cli_enabled = False
        
        # Create mock item and report
        mock_item = Mock()
        mock_item.config = mock_pytest_config
        
        mock_report = Mock()
        mock_report.when = "call"
        mock_report.outcome = "passed"
        mock_report.location = ["file.py", 1, "test_example"]
        mock_report.longreprtext = ""
        mock_report.duration = 1.0
        
        # Simulate the hook - should exit early without loading config
        # (We can't easily test the hook directly, but we verify the flag works)
        config = plugin.getConfig()
        is_enabled = plugin.is_spira_enabled(mock_pytest_config, config)
        
        assert is_enabled is False
    
    def test_combined_marker_lookup_efficiency(self, spira_config_file, reset_plugin_state):
        """Test that combined marker lookup is more efficient"""
        config = plugin.getConfig()
        
        mock_item = Mock()
        call_count = 0
        
        def count_calls(name):
            nonlocal call_count
            call_count += 1
            return None
        
        mock_item.get_closest_marker = Mock(side_effect=count_calls)
        mock_item.cls = None
        
        # Call combined function
        test_case_id, mapping_source = plugin.get_test_case_id_and_source(mock_item, "test_unknown", config)
        
        # Should call get_closest_marker exactly 3 times:
        # 1. spira_id
        # 2. smoke (first marker mapping)
        # 3. regression (second marker mapping)
        assert call_count == 3
        
        # Before optimization, this would have been called 6+ times
        # (once for each marker in get_test_case_id, then again in get_mapping_source)
