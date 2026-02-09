"""
Tests for CLI options and flags
"""
import pytest
import pytest_spiratest_integration as plugin
from unittest.mock import Mock


class TestCLIOptions:
    """Test command-line interface options"""
    
    def test_spira_disabled_flag(self, spira_config_file, reset_plugin_state):
        """Test --spira-disabled CLI flag"""
        mock_config = Mock()
        mock_config._spira_cli_disabled = True
        mock_config._spira_cli_enabled = False
        
        config = plugin.getConfig()
        result = plugin.is_spira_enabled(mock_config, config)
        
        assert result is False
    
    def test_spira_enabled_flag(self, disabled_config_file, reset_plugin_state):
        """Test --spira-enabled CLI flag overrides config"""
        mock_config = Mock()
        mock_config._spira_cli_disabled = False
        mock_config._spira_cli_enabled = True
        
        config = plugin.getConfig()
        result = plugin.is_spira_enabled(mock_config, config)
        
        # Should be enabled despite config saying disabled
        assert result is True
    
    def test_disabled_flag_priority(self, spira_config_file, reset_plugin_state):
        """Test that --spira-disabled has priority over --spira-enabled"""
        mock_config = Mock()
        mock_config._spira_cli_disabled = True
        mock_config._spira_cli_enabled = True
        
        config = plugin.getConfig()
        result = plugin.is_spira_enabled(mock_config, config)
        
        # Disabled should win
        assert result is False
    
    def test_batch_mode_cli_flag(self, spira_config_file, reset_plugin_state):
        """Test --spira-batch CLI flag"""
        mock_config = Mock()
        mock_config._spira_cli_batch = True
        mock_config._spira_cli_no_batch = False
        
        config = plugin.getConfig()
        result = plugin.is_batch_mode_enabled(mock_config, config)
        
        assert result is True
    
    def test_no_batch_mode_cli_flag(self, temp_config_dir, reset_plugin_state):
        """Test --spira-no-batch CLI flag"""
        # Create config with batch_mode = true
        config_content = """[credentials]
url = http://test.spira.com
username = test_user
token = test_token
project_id = 1

[test_cases]
default = 100

[settings]
batch_mode = true
"""
        config_file = temp_config_dir / "spira.cfg"
        config_file.write_text(config_content)
        
        mock_config = Mock()
        mock_config._spira_cli_batch = False
        mock_config._spira_cli_no_batch = True
        
        config = plugin.getConfig()
        result = plugin.is_batch_mode_enabled(mock_config, config)
        
        # Should be disabled despite config
        assert result is False
    
    def test_enabled_state_caching(self, spira_config_file, reset_plugin_state):
        """Test that enabled state is cached"""
        mock_config = Mock()
        mock_config._spira_cli_disabled = False
        mock_config._spira_cli_enabled = False
        
        config = plugin.getConfig()
        
        # First call
        result1 = plugin.is_spira_enabled(mock_config, config)
        # Second call should use cache
        result2 = plugin.is_spira_enabled(mock_config, config)
        
        assert result1 == result2
        assert plugin._spira_enabled_cache is not None
    
    def test_batch_mode_caching(self, spira_config_file, reset_plugin_state):
        """Test that batch mode state is cached"""
        mock_config = Mock()
        mock_config._spira_cli_batch = False
        mock_config._spira_cli_no_batch = False
        
        config = plugin.getConfig()
        
        # First call
        result1 = plugin.is_batch_mode_enabled(mock_config, config)
        # Second call should use cache
        result2 = plugin.is_batch_mode_enabled(mock_config, config)
        
        assert result1 == result2
        assert plugin._batch_mode_cache is not None
