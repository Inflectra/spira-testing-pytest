import pytest

def add(num1, num2):
    return num1 + num2

# Example 1: Function-level mapping (configured in spira.cfg)
def test_add_function():
    """This test is mapped via function name in spira.cfg"""
    assert add(1, 1) == 2

# Example 2: Marker-based mapping (highest priority)
@pytest.mark.spira_id(100)
def test_add_with_marker():
    """This test is mapped via @pytest.mark.spira_id marker"""
    assert add(2, 2) == 4

# Example 3: Class-level mapping
@pytest.mark.spira_id(200)
class TestCalculator:
    """All tests in this class map to test case 200 via marker"""
    
    def test_add_in_class_1(self):
        assert add(3, 3) == 6
    
    def test_add_in_class_2(self):
        assert add(4, 4) == 8

# Example 4: Class without marker (uses class name from spira.cfg)
class TestMathOperations:
    """Tests in this class map via class name 'testmathoperations' in spira.cfg"""
    
    def test_addition(self):
        assert add(5, 5) == 10
    
    def test_subtraction(self):
        assert 10 - 5 == 5

# Example 5: Individual test with marker overrides class
class TestAdvanced:
    """Class-level mapping can be overridden by function markers"""
    
    def test_default_mapping(self):
        """Uses class name mapping from spira.cfg"""
        assert add(1, 2) == 3
    
    @pytest.mark.spira_id(300)
    def test_override_mapping(self):
        """Marker overrides class mapping"""
        assert add(2, 3) == 5
