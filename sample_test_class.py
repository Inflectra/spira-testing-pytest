import pytest

def add(num1, num2):
    return num1 + num2

class TestGroup:


    def test_add_4(self):
        assert add(4, 1) == 6

    def test_add_5(self):
        assert add(4, 1) == 5
