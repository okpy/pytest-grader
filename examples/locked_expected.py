from pytest_grader import lock, points

def square(x):
    return x*x

@points(1)
def square_doctest():
    """
    >>> x = 10
    >>> square(x)
    LOCKED: ba895e2e4d0fdf52
    >>> print(print(10),
    ...       square(10))
    LOCKED: e099e49dc98e82c6
    LOCKED: b8bfeb74e5267ab5
    """