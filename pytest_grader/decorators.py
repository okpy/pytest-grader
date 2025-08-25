def points(n):
    """Decorator to add a points attribute to a test function."""
    def wrapper(f):
        f.points = n
        return f
    return wrapper