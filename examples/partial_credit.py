from pytest_grader import points

def square(x):
    return int(x * x)  # Intentionally wrong

def twice(f, x):
    return f(f(x))

@points(3)
def test_square_int():
    assert square(3) == 9
    assert square(-4) == 16
    assert square(0) == 0

@points(2)
def test_square_float():
    assert square(0.5) == 0.25

@points(4)
def test_twice_function():
    assert twice(lambda x: x * 2, 3) == 12
    assert twice(square, 2) == 16