from pytest_grader import lock, points

def square(x):
    return x*x

@lock
@points(1)
def test_square():
    """
    >>> square(10)
    100
    >>> print(print(10, square(10))
    10 100
    None
    """