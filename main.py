"""The entry point for grader when run as a standalone script
(rather than a pytest plugin).
"""

import sys
from pathlib import Path
from lock_tests import lock_doctests_for_file

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

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <command>")
        print("\nAvailable commands:")
        for cmd, func in COMMANDS.items():
            description = func.__doc__ or ""
            print(f"  {cmd:<10} {description}")
        sys.exit(1)

    command = sys.argv[1]

    if command in COMMANDS:
        COMMANDS[command](sys.argv)
    else:
        print(f"Unknown command: {command}")
        print(f"Available commands: {', '.join(COMMANDS.keys())}")
        sys.exit(1)

if __name__ == '__main__':
    main()