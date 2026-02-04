"""Test helper functions and utilities."""
from pathlib import Path


def get_test_file_path(filename: str) -> Path:
    """
    Get the path to a test file in the tests/files directory.

    Args:
        filename: Name of the file in tests/files

    Returns:
        Path object pointing to the test file
    """
    tests_dir = Path(__file__).parent
    return tests_dir / "files" / filename


def load_test_file(filename: str) -> str:
    """
    Load the contents of a test file.

    Args:
        filename: Name of the file in tests/files

    Returns:
        Contents of the file as a string
    """
    file_path = get_test_file_path(filename)
    return file_path.read_text()
