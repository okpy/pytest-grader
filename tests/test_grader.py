from pytest_grader import points


@points(5)
def test_points_decorator():
    """Test that the points decorator correctly adds a points attribute to this function."""
    assert hasattr(test_points_decorator, 'points')
    assert test_points_decorator.points == 5