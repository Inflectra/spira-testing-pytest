import pytest

def add(num1, num2):
    return num1 + num2

# Example 1: Using existing pytest markers mapped in spira.cfg
@pytest.mark.smoke
def test_critical_login():
    """This test uses @pytest.mark.smoke which maps to test case 100 in spira.cfg"""
    assert add(1, 1) == 2

@pytest.mark.regression
def test_user_profile():
    """This test uses @pytest.mark.regression which maps to test case 101"""
    assert add(2, 2) == 4

@pytest.mark.integration
def test_payment_flow():
    """This test uses @pytest.mark.integration which maps to test case 102"""
    assert add(3, 3) == 6

# Example 2: Multiple markers - first one found wins
@pytest.mark.slow
@pytest.mark.integration
def test_with_multiple_markers():
    """Has both slow and integration markers - will use first match from config"""
    assert add(4, 4) == 8

# Example 3: spira_id marker overrides other markers
@pytest.mark.spira_id(999)
@pytest.mark.smoke
def test_spira_id_wins():
    """spira_id marker (999) takes priority over smoke marker (100)"""
    assert add(5, 5) == 10

# Example 4: Class with marker
@pytest.mark.critical
class TestCriticalFeatures:
    """All tests in this class use critical marker mapping (103)"""
    
    def test_feature_a(self):
        assert add(1, 2) == 3
    
    def test_feature_b(self):
        assert add(2, 3) == 5
    
    # Override with spira_id
    @pytest.mark.spira_id(500)
    def test_feature_special(self):
        """This specific test overrides the class marker"""
        assert add(3, 4) == 7

# Example 5: Unmapped marker falls through to default
@pytest.mark.custom_marker
def test_with_unmapped_marker():
    """custom_marker is not in spira.cfg, so uses default (22)"""
    assert add(6, 6) == 12

# Example 6: No marker at all
def test_no_marker():
    """No marker, uses default (22)"""
    assert add(7, 7) == 14
