"""
Tests for configuration loading and parsing
"""
import pytest
import os
import pytest_spiratest_integration as plugin


class TestConfigLoading:
    """Test configuration file loading and parsing"""
    
    def test_load_config_from_file(self, spira_config_file, reset_plugin_state):
        """Test loading configuration from spira.cfg"""
        config = plugin.getConfig()
        
        assert config["url"] == "http://test.spira.com"
        assert config["username"] == "test_user"
        assert config["token"] == "test_token"
        assert config["project_id"] == "1"
        assert config["enabled"] is True
        assert config["verbose"] is False
    
    def test_config_cached_after_first_load(self, spira_config_file, reset_plugin_state):
        """Test that config is cached after first load"""
        config1 = plugin.getConfig()
        config2 = plugin.getConfig()
        
        # Should be the same object (cached)
        assert config1 is config2
    
    def test_disabled_config(self, disabled_config_file, reset_plugin_state):
        """Test loading disabled configuration"""
        config = plugin.getConfig()
        
        assert config["enabled"] is False
        assert plugin.spira_disabled is True
    
    def test_no_config_file(self, temp_config_dir, reset_plugin_state):
        """Test behavior when no config file exists"""
        config = plugin.getConfig()
        
        assert config["enabled"] is False
        assert plugin.spira_disabled is True
        assert config["url"] == ""
    
    def test_env_file_loading(self, temp_config_dir, reset_plugin_state):
        """Test loading configuration from .env.spira file"""
        env_content = """SPIRA_URL=http://env.spira.com
SPIRA_USERNAME=env_user
SPIRA_TOKEN=env_token
SPIRA_PROJECT_ID=99
SPIRA_ENABLED=true
"""
        env_file = temp_config_dir / ".env.spira"
        env_file.write_text(env_content)
        
        config = plugin.getConfig()
        
        assert config["url"] == "http://env.spira.com"
        assert config["username"] == "env_user"
        assert config["token"] == "env_token"
        assert config["project_id"] == 99
        assert config["enabled"] is True
    
    def test_env_overrides_config(self, spira_config_file, temp_config_dir, reset_plugin_state):
        """Test that .env.spira overrides spira.cfg"""
        env_content = """SPIRA_URL=http://override.spira.com
SPIRA_USERNAME=override_user
"""
        env_file = temp_config_dir / ".env.spira"
        env_file.write_text(env_content)
        
        config = plugin.getConfig()
        
        # Env should override config file
        assert config["url"] == "http://override.spira.com"
        assert config["username"] == "override_user"
        # But token should still come from config file
        assert config["token"] == "test_token"
    
    def test_test_case_mappings(self, spira_config_file, reset_plugin_state):
        """Test that test case mappings are loaded correctly"""
        config = plugin.getConfig()
        
        assert config["test_case_ids"]["default"] == "100"
        assert config["test_case_ids"]["test_example"] == "101"
        assert config["test_case_ids"]["testclass"] == "102"
    
    def test_marker_mappings(self, spira_config_file, reset_plugin_state):
        """Test that marker mappings are loaded correctly"""
        config = plugin.getConfig()
        
        assert config["marker_mappings"]["smoke"] == "200"
        assert config["marker_mappings"]["regression"] == "201"
    
    def test_batch_mode_config(self, temp_config_dir, reset_plugin_state):
        """Test batch mode configuration"""
        config_content = """[credentials]
url = http://test.spira.com
username = test_user
token = test_token
project_id = 1

[test_cases]
default = 100

[settings]
batch_mode = true
batch_size = 250
"""
        config_file = temp_config_dir / "spira.cfg"
        config_file.write_text(config_content)
        
        config = plugin.getConfig()
        
        assert config["batch_mode"] is True
        assert config["batch_size"] == 250
