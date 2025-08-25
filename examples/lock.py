from pytest_grader import points

def square(x):
    return x*x

# LOCK
@points(1)
def times_doctest():
    """
    >>> x = 10
    >>> x * 2
    20
    """

# LOCK
@points(1)
def square_doctest():
    """
    >>> x = 10
    >>> square(x)
    100
    >>> print(print(10),
    ...       square(10))
    10
    None 100
    """
