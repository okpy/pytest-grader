import pytest

from .lock_tests import *


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
    def __init__(self):
        self.unlock_mode = False

    def pytest_configure(self, config):
        self.unlock_mode = config.getoption("--unlock")

    def pytest_collection_modifyitems(self, session, config, items):
        if self.unlock_mode:
            locked_outputs = collect_locked_doctests(items)
            if locked_outputs:
                run_unlock_interactive(locked_outputs)


def pytest_addoption(parser):
    parser.addoption(
        "--score", "-S", action="store_true", default=False,
        help="Show score report after running tests"
    )
    parser.addoption(
        "--unlock", "-U", action="store_true", default=False,
        help="Unlock locked doctests interactively"
    )


def pytest_configure(config):
    config.pluginmanager.register(ScorerPlugin(), "pytest-grader-scorer")
    config.pluginmanager.register(UnlockPlugin(), "pytest-grader-unlock")