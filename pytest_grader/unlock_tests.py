from dataclasses import dataclass
import pytest


@dataclass
class LockedOutput:
    """The output of a doctest example that has been locked."""
    filename: str
    test_name: str
    expression: str
    line_number: int
    hash: str


def collect_locked_doctests(items: list[pytest.Item]) -> list[LockedOutput]:
    """Collect all LOCKED outputs of doctests among Pytest test items."""
    import doctest

    locked_outputs = []
    for item in items:
        # Handle DoctestItem (from --doctest-modules)
        if hasattr(item, 'dtest') and hasattr(item.dtest, 'examples'):
            for example in item.dtest.examples:
                if "LOCKED:" in example.want:
                    # Create a LockedOutput for each LOCKED line
                    for line_num, line in enumerate(example.want.split('\n')):
                        if line.strip().startswith('LOCKED:'):
                            hash_code = line.split('LOCKED:')[1].strip()
                        locked_outputs.append(LockedOutput(
                            filename=getattr(item.dtest, 'filename', item.nodeid),
                            test_name=item.dtest.name,
                            expression=example.source.strip(),
                            line_number=example.lineno + line_num,
                            hash=hash_code
                        ))
    return locked_outputs
        # # Handle regular test functions with docstrings
        # elif hasattr(item, 'function') and hasattr(item.function, '__doc__'):
        #     docstring = item.function.__doc__
        #     if docstring and "LOCKED:" in docstring:
        #         # Parse the docstring to find locked tests
        #         finder = doctest.DocTestFinder()
        #         doctests = finder.find(item.function)

        #         for test in doctests:
        #             for example in test.examples:
        #                 if "LOCKED:" in example.want:
        #                     # Create a LockedOutput for each LOCKED line
        #                     for line_num, line in enumerate(example.want.split('\n')):
        #                         if line.strip().startswith('LOCKED:'):
        #                             hash_code = line.split('LOCKED:')[1].strip()
        #                         yield LockedOutput(
        #                             filename=getattr(item, 'fspath', item.nodeid).basename if hasattr(getattr(item, 'fspath', item.nodeid), 'basename') else str(item.nodeid),
        #                             test_name=item.function.__name__,
        #                             expression=example.source.strip(),
        #                             line_number=example.lineno + line_num,
        #                             hash=hash_code
        #                         )


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
        # Print header when we encounter a new test or expression
        if (locked_output.test_name != current_test or
            locked_output.expression != current_expression):
            if current_test is not None:
                print()  # Add spacing between tests
            print(f"--- {locked_output.test_name} ---")
            print()
            print(f">>> {locked_output.expression}")
            current_test = locked_output.test_name
            current_expression = locked_output.expression

        while True:
            try:
                user_input = input("? ").strip()

                if user_input == "exit()":
                    print("Exiting unlock mode.")
                    return

                # Check if the input matches the hash
                expected_hash_input = f"{locked_output.test_name}:{eval(user_input)}"
                expected_hash = hashlib.sha256(expected_hash_input.encode()).hexdigest()[:16]

                if expected_hash == locked_output.hash:
                    print("unlocked!")
                    break
                else:
                    print("-- Not quite. Try again! --")
                    print()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting unlock mode.")
                return

    print()
