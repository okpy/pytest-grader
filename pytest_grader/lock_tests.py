"""
Module for locking (and unlocking) doctests by replacing their outputs with secure hash codes.
"""

import hashlib
import re
import types
from pathlib import Path
import importlib.util
from dataclasses import dataclass
import pytest


def lock_doctests_for_file(src: Path, dst: Path) -> None:
    """
    Write the contents of src to dst with one change: all of the outputs for
    doctests are replaced by a hashcode formed from concatenating the name of
    the function and the output value replaced.
    """
    with open(src, 'r') as f:
        source_code = f.read()

    # Import the module to get access to the functions
    spec = importlib.util.spec_from_file_location("temp_module", src)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    modified_code = source_code

    # Find functions with doctests that have the lock attribute set to True
    for name, obj in vars(module).items():
        if (isinstance(obj, types.FunctionType) and
            hasattr(obj, 'lock') and
            obj.lock is True and
            obj.__doc__):

            # Extract the original docstring from the source code to preserve formatting
            func_pattern = rf'def {re.escape(name)}\([^)]*\):\s*"""([^"]*(?:"[^"]*"[^"]*)*)"""'
            match = re.search(func_pattern, source_code, flags=re.DOTALL)

            if match:
                original_docstring = match.group(1)
                # Process the original docstring while preserving its formatting
                modified_docstring = replace_doctest_outputs(src.name, original_docstring, name)

                # Replace the docstring in the source code
                modified_code = modified_code.replace(match.group(0),
                                                     match.group(0).replace(original_docstring, modified_docstring))

    # Remove @lock decorator lines and clean up extra blank lines
    modified_code = re.sub(r'^@lock\s*\n', '', modified_code, flags=re.MULTILINE)
    # Clean up multiple consecutive blank lines
    modified_code = re.sub(r'\n\n\n+', '\n\n', modified_code)

    # Write the modified code to the destination
    with open(dst, 'w') as f:
        f.write(modified_code)


def replace_doctest_outputs(filename: str, docstring: str, func_name: str) -> str:
    """Replace doctest outputs in a docstring with hash codes."""
    lines = docstring.split('\n')
    result_lines = []
    line_idx = 0
    output_number = 0

    while line_idx < len(lines):
        line = lines[line_idx]
        result_lines.append(line)

        # Check if this line is a doctest command
        if line.strip().startswith('>>> '):
            line_idx += 1
            # Skip any continuation lines (...)
            while line_idx < len(lines) and lines[line_idx].strip().startswith('... '):
                result_lines.append(lines[line_idx])
                line_idx += 1

            # Now look for the expected output lines
            while line_idx < len(lines):
                next_line = lines[line_idx]
                # If we hit another >>> or empty line, stop
                if (next_line.strip().startswith('>>> ') or not next_line.strip()):
                    break
                if next_line.strip():
                    expected_output = next_line.strip()
                    indent = len(next_line) - len(next_line.lstrip())
                    pos = OutputPosition(filename=filename, test_name=func_name, output_number=output_number)
                    hash_code = pos.encode(expected_output)
                    result_lines.append(' ' * indent + f"LOCKED: {hash_code}")
                    output_number += 1
                    line_idx += 1
        else:
            line_idx += 1

    return '\n'.join(result_lines)


@dataclass
class OutputPosition:
    """The position of a doctest output."""
    filename: str
    test_name: str
    output_number: int

    def encode(self, output):
        hash_input = f"{self.test_name}:{self.output_number}:{output}"
        print(f"DEBUG HASH INPUT: '{hash_input}'")
        return hashlib.sha256(bytes(hash_input, 'UTF-8')).hexdigest()[:16]


@dataclass
class LockedOutput:
    """The hashed output of a doctest example that has been locked."""
    position: OutputPosition
    hash: str
    expression: str


def collect_locked_doctests(items: list[pytest.Item]) -> list[LockedOutput]:
    """Collect all LOCKED outputs of doctests among Pytest test items."""
    import doctest

    locked_outputs = []
    for item in items:
        if isinstance(item, pytest.DoctestItem) and isinstance(item.dtest, doctest.DocTest):
            output_counter = 0  # Global counter across all examples in this doctest
            for example in item.dtest.examples:
                if "LOCKED:" in example.want:
                    # Create a LockedOutput for each LOCKED line
                    for line_num, line in enumerate(example.want.split('\n')):
                        if line.strip().startswith('LOCKED:'):
                            hash_code = line.split('LOCKED:')[1].strip()
                            # Extract just the function name (same as locking process)
                            test_name = item.dtest.name.split('.')[-1]
                            position = OutputPosition(
                                filename=item.dtest.filename,
                                test_name=test_name,
                                output_number=output_counter
                            )
                            locked_outputs.append(LockedOutput(
                                position=position,
                                hash=hash_code,
                                expression=example.source.strip()
                            ))
                            output_counter += 1
    return locked_outputs


def run_unlock_interactive(locked_outputs: list[LockedOutput]) -> None:
    """Run the interactive unlock loop."""
    import hashlib

    # Load interface text from file
    from pathlib import Path
    interface_file = Path(__file__).parent / "unlock_interface.txt"
    with open(interface_file, 'r') as f:
        interface_text = f.read()
    print(interface_text)

    # Group locked outputs by test and expression
    current_test = None
    current_expression = None

    for locked_output in locked_outputs:
        if (locked_output.position.test_name != current_test or
            locked_output.expression != current_expression):
            if current_test is not None:
                print()  # Add spacing between tests
            print(f"--- {locked_output.position.test_name} ---")
            print()
            print(f">>> {locked_output.expression}")
        current_test = locked_output.position.test_name
        current_expression = locked_output.expression
        success = unlock_output(locked_output)
        if success is False:  # User chose to exit
            return
        print(success)  # TODO finish unlocking process


def unlock_output(locked_output):
    # Print header when we encounter a new test or expression
    while True:
        try:
            user_input = input("? ").strip()

            if user_input == "exit()":
                print("Exiting unlock mode.")
                return False

            # Check if the input matches the hash
            expected_hash = locked_output.position.encode(user_input)
            if expected_hash == locked_output.hash:
                print("unlocked!")
                break
            else:
                print("-- Not quite. Try again! --")
                print()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting unlock mode.")
            return False
