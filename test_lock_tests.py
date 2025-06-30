from lock_tests import replace_doctest_outputs

def test_replace_doctest_outputs():
    """Test that replace_doctest_outputs correctly replaces doctest outputs with hash codes."""
    docstring = '''
    Example function with doctests.

    >>> add(2, 3)
    5
    >>> add(10, 20)
    30
    >>> multiply(4, 5)
    20
    >>> print(print(1, 2), print(3))
    1 2
    3
    None None
    '''

    result = replace_doctest_outputs(docstring, "test_func")

    # Check that the original outputs are no longer present
    assert "5" not in result.split(">>> add(2, 3)")[1].split("\n")[0]
    assert "30" not in result.split(">>> add(10, 20)")[1].split("\n")[0]
    assert "20" not in result.split(">>> multiply(4, 5)")[1].split("\n")[0]

    # Check that hash codes are present and preserve indentation
    original_lines = docstring.split('\n')
    result_lines = result.split('\n')
    
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
                    
                    # Verify it's a hash code in quotes
                    result_content = result_output.strip()
                    assert result_content.startswith("'") and result_content.endswith("'")
                    assert len(result_content) == 18  # 16 chars + 2 quotes
                
                j += 1