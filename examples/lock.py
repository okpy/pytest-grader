from pytest_grader import lock, points

def square(x):
    return x*x

@lock
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