import subprocess
import tempfile
import os
from pathlib import Path
from lock_tests import replace_doctest_outputs


def test_replace_doctest_outputs():
    """Test that replace_doctest_outputs correctly replaces doctest outputs with hash codes."""
    docstring = '''
    Example function with doctests.

    >>> add(2, 3)
    5
    >>> add(10, 20)
    30
    >>> multiply(4,
    ...          5)
    20
    >>> print(print(1, 2), print(3))
    1 2
    3
    None None
    >>> print(7,
    ...       print(8))
    8
    7 None
    >>> 5 + 5
    10
    '''

    result = replace_doctest_outputs(docstring, "test_func")

    # Systematically check all doctests and their outputs
    original_lines = docstring.split('\n')
    result_lines = result.split('\n')

    # Collect all expected outputs from the original docstring
    expected_outputs = []
    doctests_found = []

    i = 0
    while i < len(original_lines):
        line = original_lines[i]
        if line.strip().startswith('>>>'):
            doctest_command = line.strip()[4:].strip()  # Remove >>> and spaces
            doctests_found.append(doctest_command)

            # Collect all output lines for this doctest
            i += 1
            outputs_for_this_test = []
            while i < len(original_lines):
                next_line = original_lines[i]
                if (next_line.strip().startswith('>>>') or
                    next_line.strip().startswith('...') or
                    not next_line.strip()):
                    break
                if next_line.strip():
                    outputs_for_this_test.append(next_line.strip())
                i += 1
            expected_outputs.extend(outputs_for_this_test)
        else:
            i += 1

    # Verify all expected outputs are no longer standalone output lines
    result_output_lines = []
    i = 0
    while i < len(result_lines):
        line = result_lines[i]
        if line.strip().startswith('>>>'):
            # Skip to next lines that are outputs
            i += 1
            while i < len(result_lines):
                next_line = result_lines[i]
                if (next_line.strip().startswith('>>>') or
                    next_line.strip().startswith('...') or
                    not next_line.strip()):
                    break
                if next_line.strip():
                    result_output_lines.append(next_line.strip())
                i += 1
        else:
            i += 1

    # Check that none of the original outputs appear as standalone output lines
    for output in expected_outputs:
        assert output not in result_output_lines, f"Original output '{output}' still found as output line in result"

    # Verify all doctests are preserved but outputs are replaced
    for doctest in doctests_found:
        assert f">>> {doctest}" in result, f"Doctest '>>> {doctest}' not found in result"

    # Check that hash codes are present and preserve indentation
    for i, original_line in enumerate(original_lines):
        if original_line.strip().startswith('>>>'):
            # Find corresponding output lines in both original and result
            j = i + 1
            while j < len(original_lines) and j < len(result_lines):
                orig_output = original_lines[j]
                result_output = result_lines[j]

                # Stop when we hit another >>> or empty line
                if (orig_output.strip().startswith('>>>') or
                    orig_output.strip().startswith('...') or
                    not orig_output.strip()):
                    break

                # Check that non-empty output lines have been replaced with hash codes
                if orig_output.strip():
                    # Verify indentation is preserved
                    orig_indent = len(orig_output) - len(orig_output.lstrip())
                    result_indent = len(result_output) - len(result_output.lstrip())
                    assert orig_indent == result_indent, f"Indentation not preserved: original {orig_indent} spaces, result {result_indent} spaces"

                    # Verify it's a hash code in quotes or LOCKED format
                    result_content = result_output.strip()
                    is_hash_quote = (result_content.startswith("'") and result_content.endswith("'") and len(result_content) == 18)
                    is_locked_format = result_content.startswith("LOCKED: ") and len(result_content) == 24  # "LOCKED: " + 16 chars
                    assert is_hash_quote or is_locked_format, f"Expected hash code format, got: {result_content}"

                j += 1


def test_lock_command_output():
    """Test that main.py lock command generates expected output file."""
    # Create a temporary directory for the test
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)

        # Copy the source file to temp directory
        src_file = temp_dir_path / "lock.py"
        dst_file = temp_dir_path / "locked.py"
        examples_dir = Path(__file__).parent / "examples"
        expected_file = examples_dir / "locked_expected.py"

        # Copy the original lock.py to our temp directory
        with open(examples_dir / "lock.py", "r") as f:
            src_content = f.read()
        with open(src_file, "w") as f:
            f.write(src_content)

        # Run the lock command
        result = subprocess.run([
            "python3", "main.py", "lock",
            str(src_file), str(dst_file)
        ], capture_output=True, text=True, cwd=Path(__file__).parent)

        # Check that the command succeeded
        assert result.returncode == 0, f"Lock command failed with error: {result.stderr}"

        # Check that the output file was created
        assert dst_file.exists(), "Output file was not created"

        # Read the generated and expected content
        with open(dst_file, "r") as f:
            generated_content = f.read()
        with open(expected_file, "r") as f:
            expected_content = f.read()

        # Compare the content
        assert generated_content == expected_content, f"Generated content does not match expected.\nGenerated:\n{generated_content}\nExpected:\n{expected_content}"