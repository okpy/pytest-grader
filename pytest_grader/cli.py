"""Command line interface for pytest-grader."""

import sys
from pathlib import Path
from .lock_tests import lock_doctests_for_file

def lock_command(args):
    """Copy [src] to [dst], replacing the output of locked doctests with secure hashes."""
    if len(args) != 4:
        print("Usage: python main.py lock <src> <dst>")
        sys.exit(1)

    src = args[2]
    dst = args[3]

    lock_doctests_for_file(Path(src), Path(dst))
    print(f"Wrote locked version of {src} to {dst}")

COMMANDS = {
    "lock": lock_command
}

def show_help():
    """Show help message with usage and available commands."""
    print("Usage: pytest-grader <command>")
    print("\nAvailable commands:")
    for cmd, func in COMMANDS.items():
        description = func.__doc__ or ""
        print(f"  {cmd:<10} {description}")
    print("\nOptions:")
    print("  --help, -h Show this help message")

def cli_main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        show_help()
        sys.exit(1)

    command = sys.argv[1]

    if command in ["--help", "-h", "help"]:
        show_help()
        sys.exit(0)
    elif command in COMMANDS:
        COMMANDS[command](sys.argv)
    else:
        print(f"Unknown command: {command}")
        print(f"Available commands: {', '.join(COMMANDS.keys())}")
        sys.exit(1)