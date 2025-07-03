import doctest


def points(n):
    """Decorator to add a points attribute to a test function."""
    def wrapper(f):
        f.points = n
        return f
    return wrapper


def lock(f):
    """Decorator to add a lock attribute to a function with doctests."""

    if not hasattr(f, '__doc__') or f.__doc__ is None:
        raise ValueError(f"Function {f.__name__} must have a docstring with at least one doctest")

    finder = doctest.DocTestFinder()
    doctests = finder.find(f)

    if not doctests or len(doctests) == 0:
        raise ValueError(f"Function {f.__name__} must have at least one doctest in its docstring")

    f.lock = True
    return f