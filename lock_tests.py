"""
Module for locking doctests by replacing their outputs with secure hash codes.
"""

import hashlib
import re
import sys
import types
from pathlib import Path
import importlib.util


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
                modified_docstring = replace_doctest_outputs(original_docstring, name)
                
                # Replace the docstring in the source code
                modified_code = modified_code.replace(match.group(0), 
                                                     match.group(0).replace(original_docstring, modified_docstring))

    # Write the modified code to the destination
    with open(dst, 'w') as f:
        f.write(modified_code)


def replace_doctest_outputs(docstring: str, func_name: str) -> str:
    """
    Replace doctest outputs in a docstring with hash codes.
    """
    lines = docstring.split('\n')
    result_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]
        result_lines.append(line)

        # Check if this line is a doctest command
        if line.strip().startswith('>>> '):
            i += 1
            # Look for the next line(s) that contain the expected output
            while i < len(lines):
                next_line = lines[i]
                # If we hit another >>> or empty line or ... continuation, stop
                if (next_line.strip().startswith('>>> ') or
                    next_line.strip().startswith('... ') or
                    not next_line.strip()):
                    break

                # This is an expected output line - replace it with hash
                if next_line.strip():
                    hash_input = f"{func_name}:{next_line.strip()}"
                    hash_code = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
                    # Preserve the indentation
                    indent = len(next_line) - len(next_line.lstrip())
                    result_lines.append(' ' * indent + f"'{hash_code}'")
                else:
                    result_lines.append(next_line)
                i += 1
        else:
            i += 1

    return '\n'.join(result_lines)