import pytest
import tempfile
import os
from pytest_grader.logger import SQLLogger


@pytest.fixture
def temp_db():
    """Create a temporary database file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    yield db_path
    os.unlink(db_path)


@pytest.fixture
def temp_file():
    """Create a temporary file for testing snapshot functionality."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("def test_function():\n    return 42\n")
        file_path = f.name
    yield file_path
    os.unlink(file_path)


@pytest.fixture
def logger(temp_db, temp_file):
    """Create a SQLLogger instance with a temporary database and test file."""
    assignment_info = {'included_files': [temp_file]}
    return SQLLogger(temp_db, assignment_info)


def test_snapshot(logger):
    """Test the snapshot method creates a snapshot and stores file content."""
    logger.snapshot()
    
    # Check that snapshot was created
    logger.cursor.execute("SELECT COUNT(*) FROM snapshots")
    snapshot_count = logger.cursor.fetchone()[0]
    assert snapshot_count == 1
    
    # Check that current_snapshot is set
    assert logger.current_snapshot is not None
    
    # Check that file was stored
    logger.cursor.execute("SELECT COUNT(*) FROM files")
    file_count = logger.cursor.fetchone()[0]
    assert file_count == 1
    
    # Check that snapshot_files was populated
    logger.cursor.execute("SELECT COUNT(*) FROM snapshot_files")
    snapshot_files_count = logger.cursor.fetchone()[0]
    assert snapshot_files_count == 1


def test_test_case(logger):
    """Test the test_case method stores test case results."""
    logger.snapshot()  # Need a snapshot first
    
    logger.test_case("test_example", True, "AI response here")
    
    # Check that test case was stored
    logger.cursor.execute("SELECT name, passed, response FROM test_cases")
    result = logger.cursor.fetchone()
    assert result == ("test_example", True, "AI response here")


def test_unlock_attempt(logger):
    """Test the unlock_attempt method stores unlock attempts."""
    logger.snapshot()  # Need a snapshot first
    
    logger.unlock_attempt("test_unlock", 0, "my guess", False, "AI response")
    
    # Check that unlock attempt was stored
    logger.cursor.execute("SELECT name, guess, success, response FROM unlock_attempts")
    result = logger.cursor.fetchone()
    assert result == ("test_unlock[0]", "my guess", False, "AI response")