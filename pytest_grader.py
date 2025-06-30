import doctest
import pytest


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


def has_points(item: pytest.Item):
    return isinstance(item, pytest.Function) and hasattr(item.function, 'points')


class ScorerPlugin:
    def __init__(self):
        self.test_items = {}
        self.test_results = []
        self.total_points_in_all_tests = 0

    def pytest_collection_modifyitems(self, session, config, items):
        self.total_points_in_all_tests = sum(f.function.points for f in items if has_points(f))

    def pytest_runtest_setup(self, item):
        self.test_items[item.nodeid] = item

    def pytest_runtest_logreport(self, report):
        if report.when == "call":
            self.test_results.append(report)

    def pytest_terminal_summary(self, terminalreporter, exitstatus, config):
        if config.getoption("--score"):
            self.print_score_report()

    def print_score_report(self):
        total_earned = 0
        total_points = 0

        print('═' * 40)
        for report in self.test_results:
            if report.nodeid in self.test_items:
                test_item = self.test_items[report.nodeid]
                if has_points(test_item):
                    points = test_item.function.points
                    earned = points if report.outcome == 'passed' else 0
                    total_points += points
                    total_earned += earned
                    test_name = report.nodeid.split("::")[-1]
                    emoji = "✅" if report.outcome == 'passed' else "❌"
                    print(f"  {emoji} {test_name:<25} {earned:>2}/{points} pts")

        if total_points == self.total_points_in_all_tests:
            percentage = 0.0 if total_points == 0 else round(100.0 * total_earned / total_points, 1)
            decoration = ""
            if total_earned == total_points:
                percentage = "💯"
                decoration = "✨"

            print('─' * 40)
            print(f"  {decoration}Total Score: {total_earned}/{total_points} pts"
                  f" ({percentage}%){decoration}")


class UnlockPlugin:
    pass

def pytest_addoption(parser):
    parser.addoption(
        "--score", action="store_true", default=False,
        help="Show score report after running tests"
    )


def pytest_configure(config):
    config.pluginmanager.register(ScorerPlugin(), "pytest-grader")