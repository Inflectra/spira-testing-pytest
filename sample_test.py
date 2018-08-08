# Function we are testing
def add(num1, num2):
    print("Testing...")
    return num1 + num2

# Successful test
def test_add_1():
    assert add(1, 1) == 2

# Failed test
def test_add_2():
    assert add(2, 1) == 2

# Failed test
def test_add_3():
    assert add(4, 1) == 6