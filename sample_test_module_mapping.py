"""
Example test file demonstrating module-level mapping

This entire module would map to a single Spira test case (e.g., TC-200)
All tests in this file would be aggregated into one test run result.

Configuration in spira.cfg:
[modules]
sample_test_module_mapping = 200
"""
import pytest


def test_user_login():
    """Test user can log in"""
    assert True


def test_user_logout():
    """Test user can log out"""
    assert True


def test_password_reset():
    """Test password reset flow"""
    assert True


def test_session_timeout():
    """Test session expires after timeout"""
    assert True


class TestUserProfile:
    """Tests for user profile management"""
    
    def test_update_profile(self):
        """Test updating user profile"""
        assert True
    
    def test_upload_avatar(self):
        """Test uploading profile picture"""
        assert True


class TestUserSettings:
    """Tests for user settings"""
    
    def test_change_email(self):
        """Test changing email address"""
        assert True
    
    def test_enable_2fa(self):
        """Test enabling two-factor authentication"""
        assert True


# All 8 tests above would be aggregated into a single Spira test run:
# 
# Module: sample_test_module_mapping
# Total: 8 tests - Passed: 8, Failed: 0, Skipped: 0
#
# [PASSED] test_user_login
# [PASSED] test_user_logout
# [PASSED] test_password_reset
# [PASSED] test_session_timeout
# [PASSED] TestUserProfile.test_update_profile
# [PASSED] TestUserProfile.test_upload_avatar
# [PASSED] TestUserSettings.test_change_email
# [PASSED] TestUserSettings.test_enable_2fa


# You can still override module mapping with more specific mappings:

@pytest.mark.spira_id(999)
def test_critical_security_check():
    """This test overrides module mapping and posts individually to TC-999"""
    assert True


@pytest.mark.smoke
def test_quick_smoke_check():
    """This test uses marker mapping instead of module mapping"""
    assert True
