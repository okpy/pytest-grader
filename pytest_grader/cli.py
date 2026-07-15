"""Command line interface for pytest-grader."""

import argparse
from pathlib import Path
from .lock_tests import lock_doctests_for_file

def lock_command(args):
    """Copy [src] to [dst], replacing the output of locked doctests with secure hashes."""
    count = lock_doctests_for_file(Path(args.src), Path(args.dst))
    print(f'Wrote locked version of {args.src} to {args.dst} ({count} outputs locked)')

def cli_main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(prog='pytest-grader')
    subparsers = parser.add_subparsers(dest='command')

    lock_parser = subparsers.add_parser('lock', help=lock_command.__doc__)
    lock_parser.add_argument('src', help='Source file')
    lock_parser.add_argument('dst', help='Destination file')
    lock_parser.set_defaults(func=lock_command)

    args = parser.parse_args()

    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()
