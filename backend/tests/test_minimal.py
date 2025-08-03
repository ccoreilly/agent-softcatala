"""
Minimal test to verify CI testing infrastructure works
"""

def test_always_passes():
    """Most basic test that should always pass."""
    assert True


def test_basic_math():
    """Test basic arithmetic."""
    assert 1 + 1 == 2
    assert 2 * 3 == 6


def test_string_operations():
    """Test basic string operations."""
    assert "hello" + " world" == "hello world"
    assert "test".upper() == "TEST"


def test_list_operations():
    """Test basic list operations."""
    my_list = [1, 2, 3]
    assert len(my_list) == 3
    assert my_list[0] == 1