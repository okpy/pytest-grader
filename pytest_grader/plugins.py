import pytest

from .lock_tests import *
from sqlitedict import SqliteDict

GRADER_DB = 'grader.sqlite'


def has_points(item: pytest.Item):
    if isinstance(item, pytest.Function):
        return hasattr(item.function, 'points') and item.function.points > 0
    elif isinstance(item, pytest.DoctestItem):
        # For doctests, check if the parent function has points
        func_name = item.dtest.name.split('.')[-1]
        if hasattr(item.dtest, 'globs') and func_name in item.dtest.globs:
            func = item.dtest.globs[func_name]
            return hasattr(func, 'points') and func.points > 0
    return False

def get_points(item: pytest.Item):
    if isinstance(item, pytest.Function):
        return item.function.points
    elif isinstance(item, pytest.DoctestItem):
        func_name = item.dtest.name.split('.')[-1]
        if hasattr(item.dtest, 'globs') and func_name in item.dtest.globs:
            func = item.dtest.globs[func_name]
            return func.points
    return 0


class ScorerPlugin:
    def __init__(self):
        self.points = {}
        self.test_results = []
        self.total_points_in_all_tests = 0

    def pytest_collection_modifyitems(self, session, config, items):
        self.total_points_in_all_tests = sum(get_points(f) for f in items if has_points(f))
        # Store points for all items during collection, before any can be skipped
        for item in items:
            if has_points(item):
                self.points[item.nodeid] = get_points(item)

    def pytest_runtest_logreport(self, report):
        if report.when == "call" or (report.when == "setup" and report.outcome == "skipped"):
            self.test_results.append(report)

    def pytest_terminal_summary(self, terminalreporter, exitstatus, config):
        if config.getoption("--score"):
            self.print_score_report()

    def print_score_report(self):
        total_earned = 0
        total_points = 0

        print('═' * 40)
        for report in self.test_results:
            if report.nodeid in self.points:
                    points = self.points[report.nodeid]
                    earned = points if report.outcome == 'passed' else 0
                    total_points += points
                    total_earned += earned
                    test_name = report.nodeid.split("::")[-1]
                    if report.outcome == 'passed':
                        emoji = "✅"
                    elif report.outcome == 'skipped':
                        emoji = "⏭️"
                    else:
                        emoji = "❌"
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
    def __init__(self, keys: dict[str, str]):
        self.unlock_mode = False
        self.keys = keys

    def pytest_configure(self, config):
        self.unlock_mode = config.getoption("--unlock")

    def pytest_collection_modifyitems(self, session, config, items):
        if self.unlock_mode:
            # Temporarily disable pytest's output capturing for interactive input
            capmanager = config.pluginmanager.getplugin('capturemanager')
            if capmanager:
                capmanager.suspend_global_capture(in_=True)
            try:
                run_unlock_interactive(items, self.keys)
            finally:
                if capmanager:
                    capmanager.resume_global_capture()

    def pytest_runtest_setup(self, item):
        if isinstance(item, pytest.DoctestItem) and isinstance(item.dtest, doctest.DocTest):
            for example in item.dtest.examples:
                if 'LOCKED:' in example.want:
                    all_unlocked = self._unlock_doctest_output(example)

            if not all_unlocked:
                test_name = item.dtest.name.split('.')[-1] if hasattr(item.dtest, 'name') else str(item)
                lock_warning = f"{test_name} still has locked examples. To unlock them, run pytest with --unlock."
                print(lock_warning)
                pytest.skip(lock_warning)

    def _unlock_doctest_output(self, example):
        lines = example.want.split('\n')
        unlocked_lines = []
        all_unlocked = True

        for line in lines:
            if line.strip().startswith('LOCKED:'):
                hash_code = line.split('LOCKED:')[1].strip()
                if hash_code in self.keys:
                    unlocked_value = self.keys[hash_code]
                    indent = len(line) - len(line.lstrip())
                    unlocked_lines.append(' ' * indent + unlocked_value)
                else:
                    unlocked_lines.append(line)
                    all_unlocked = False
            else:
                unlocked_lines.append(line)

        example.want = '\n'.join(unlocked_lines)
        return all_unlocked


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
    # Ensure that skipped tests display a reason
    config.option.reportchars = 'rs'

    unlock_keys = SqliteDict(GRADER_DB, tablename="unlock_keys", autocommit=True)
    config.pluginmanager.register(ScorerPlugin(), "pytest-grader-scorer")
    config.pluginmanager.register(UnlockPlugin(unlock_keys), "pytest-grader-unlock")