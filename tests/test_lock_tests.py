import doctest
import subprocess
import tempfile
from pathlib import Path
from pytest_grader.lock_tests import replace_doctest_outputs, OutputPosition
from pytest_grader.plugins import UnlockPlugin

def test_lock_command_output():
    """Test that pytest-grader lock command generates expected output file."""
    # Create a temporary directory for the test
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)

        # Copy the source file to temp directory
        src_file = temp_dir_path / "lock.py"
        dst_file = temp_dir_path / "locked.py"
        examples_dir = Path(__file__).parent.parent / "examples"
        expected_file = examples_dir / "locked_expected.py"

        # Copy the original lock.py to our temp directory
        with open(examples_dir / "lock.py", "r") as f:
            src_content = f.read()
        with open(src_file, "w") as f:
            f.write(src_content)

        # Run the lock command
        result = subprocess.run([
            "pytest-grader", "lock",
            str(src_file), str(dst_file)
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)

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


def test_lock_unlock_roundtrip():
    """Test that locking and unlocking works correctly in a round-trip."""
    import doctest
    from pytest_grader.lock_tests import replace_doctest_outputs, OutputPosition

    # Test data
    filename = "test.py"
    func_name = "test_func"
    original_docstring = '''
    >>> square(10)
    100
    >>> add(2, 3)
    5
    >>> print("hello")
    hello
    '''

    # Step 1: Lock the docstring
    locked_docstring = replace_doctest_outputs(original_docstring, func_name)

    # Step 2: Extract the locked hashes
    locked_lines = locked_docstring.split('\n')
    locked_hashes = []
    for line in locked_lines:
        if 'LOCKED:' in line:
            hash_code = line.split('LOCKED:')[1].strip()
            locked_hashes.append(hash_code)

    # Should have 3 locked outputs
    assert len(locked_hashes) == 3, f"Expected 3 locked hashes, got {len(locked_hashes)}"

    # Step 3: Test unlocking with correct answers
    test_cases = [
        (0, "100"),    # First output: square(10) -> 100
        (1, "5"),      # Second output: add(2, 3) -> 5
        (2, "hello"),  # Third output: print("hello") -> hello
    ]

    for output_number, correct_answer in test_cases:
        pos = OutputPosition(func_name, output_number)
        expected_hash = pos.encode(correct_answer)
        actual_hash = locked_hashes[output_number]

        assert expected_hash == actual_hash, f"Round-trip failed for output {output_number}: expected hash {expected_hash}, got {actual_hash} for answer '{correct_answer}'"

    # Step 4: Test that wrong answers don't match
    wrong_pos = OutputPosition(func_name, 0)
    wrong_hash = wrong_pos.encode("999")  # Wrong answer for square(10)
    assert wrong_hash != locked_hashes[0], "Wrong answer should not match the locked hash"


def test_unlock_plugin_substitution():
    """Test that UnlockPlugin correctly substitutes locked outputs with unlocked values."""
    func_name = "test_func"
    correct_answer = "42"
    output_number = 0

    # Generate the expected hash
    pos = OutputPosition(func_name, output_number)
    expected_hash = pos.encode(correct_answer)

    # Create a mock doctest example with locked output
    example1 = doctest.Example(
        source="calculate()",
        want=f"LOCKED: {expected_hash}\n"
    )

    # Create keys dict with the hash and correct answer
    keys = {expected_hash: correct_answer}
    plugin = UnlockPlugin(keys)
    all_unlocked = plugin._unlock_doctest_output(example1)
    assert all_unlocked, "Examples are not all unlocked but should be."
    assert example1.want == f"{correct_answer}\n", f"Expected '{correct_answer}\\n', got '{example1.want}'"


def test_unlock_plugin_skipping_locked_test():
    """Test that UnlockPlugin correctly skips locked doctests with no keys."""
    unknown_hash = "unknown_hash_123"

    # Create a mock doctest example with unknown locked output
    example2 = doctest.Example(
        source="unknown_function()",
        want=f"LOCKED: {unknown_hash}\n"
    )

    # Test with a plugin that has no keys.
    plugin = UnlockPlugin({})
    all_unlocked = plugin._unlock_doctest_output(example2)
    assert not all_unlocked, "Examples are all unlocked but should not be."
    assert example2.want == f"LOCKED: {unknown_hash}\n", f"Expected 'LOCKED: {unknown_hash}\\n', got '{example2.want}'"