from .cli import cli_main
from .plugins import *
from .decorators import *


def main():
    """CLI entry point for pytest-grader."""
    cli_main()