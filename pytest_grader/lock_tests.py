"""
Module for locking (and unlocking) doctests by replacing their outputs with secure hash codes.
"""

from dataclasses import dataclass
from pathlib import Path

import doctest
import hashlib
import importlib.util
import pytest
import re
import types


def lock_doctests_for_file(src: Path, dst: Path) -> None:
    """
    Write the contents of src to dst with one change: all of the outputs for
    doctests are replaced by a cryptographic hashcode so that the test cannot
    be run without the user first verifying the output.
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
                modified_docstring = replace_doctest_outputs(original_docstring, name)

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


def replace_doctest_outputs(docstring: str, func_name: str) -> str:
    """Replace doctest outputs with hash codes in a docstring."""
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
                line = lines[line_idx]
                # If we hit another >>> or empty line, stop
                if (line.strip().startswith('>>> ') or not line.strip()):
                    break
                if line.strip():
                    expected_output = line.strip()
                    indent = len(line) - len(line.lstrip())
                    pos = OutputPosition(testname=func_name, output_number=output_number)
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
    testname: str
    output_number: int

    def encode(self, output):
        """Encode an output as a cryptographic hash value."""
        hash_input = f"{self.testname}:{self.output_number}:{output}"
        return hashlib.sha256(bytes(hash_input, 'UTF-8')).hexdigest()[:16]


def run_unlock_interactive(items: list[pytest.Item], keys: dict[str, str]):
    """Collect all LOCKED outputs of doctests among Pytest test items."""
    preamble = Path(__file__).parent / "unlock_interface.txt"
    with open(preamble, 'r') as f:
        print(f.read())
    for item in items:
        if isinstance(item, pytest.DoctestItem) and isinstance(item.dtest, doctest.DocTest):
            if any("LOCKED:" in example.want for example in item.dtest.examples):
                if not unlock_doctest(item.dtest, keys):
                    return
    print("=== 🎉 All tests unlocked! 🎉 ===")


def unlock_doctest(dtest: doctest.DocTest, keys: dict[str, str]):
    """Unlock all locked outputs of a doctest interactively."""
    output_number = 0  # Global counter across all examples in this doctest
    testname = dtest.name.split('.')[-1]
    print(f'--- {testname} ---')
    for example in dtest.examples:
        print(">>>", example.source, end="")
        output_lines = [s for s in example.want.split('\n') if s.strip()]
        for k, line in enumerate(output_lines):
            if line.strip().startswith('LOCKED:'):
                hash_code = line.split('LOCKED:')[1].strip()
                if output := keys.get(hash_code):
                    print(output)
                else:
                    position = OutputPosition(testname, output_number)
                    prompt = "?"
                    if len(output_lines) > 1:
                        prompt = f"(line {k+1} of {len(output_lines)}) ?"
                    output_str = unlock_output(position, hash_code, prompt)
                    if not output_str:  # User chose to exit
                        return False
                    keys[hash_code] = output_str
            output_number += 1


def unlock_output(output_pos, hash_code, prompt):
    """Interactively unlock a single output."""
    while True:
        try:
            user_input = input(f"{prompt} ").strip()

            if user_input == "exit()":
                print("Exiting unlock mode.")
                return None

            # Check if the input matches the hash
            expected_hash = output_pos.encode(user_input)
            if expected_hash == hash_code:
                return user_input
            else:
                print("-- Not quite. Try again! --")
                print()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting unlock mode.")
            return False
