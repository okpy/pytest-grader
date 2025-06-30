from pytest_grader import lock, points

def square(x):
    return x*x

@points(1)
def square_doctest():
    """
    >>> square(10)
    LOCKED: e409c22ab33a6834
    >>> print(print(10),
    ...       square(10))
    LOCKED: b9a895416606bf4d
    LOCKED: 7aa05a7945fb8e4c
    """