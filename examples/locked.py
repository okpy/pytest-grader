from pytest_grader import lock, points

def square(x):
    return x*x

@lock
@points(1)
def test_square():
    """
    >>> square(10)
    '659786492e688880'
    >>> print(print(10, square(10))
    '1e38e5bf9e96acaf'
    'ce776779df1d65dc'
    """