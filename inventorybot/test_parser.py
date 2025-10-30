from inventorybot.parser import parser


def test_parser_single_operation_single_value():
    """Test parser with a single operation and single value."""
    result = parser("l Caixa")
    assert result == [["l", "Caixa"]]


def test_parser_single_operation_multiple_values():
    """Test parser with a single operation and multiple values."""
    result = parser("l Caixa 2")
    assert result == [["l", "Caixa", "2"]]


def test_parser_multiple_operations():
    """Test parser with multiple operations."""
    result = parser("l Caixa 2 q 3")
    assert result == [["l", "Caixa", "2"], ["q", "3"]]


def test_parser_multiple_operations_multiple_values():
    """Test parser with multiple operations, each having multiple values."""
    result = parser("l Caixa 2 q 3 s available")
    assert result == [["l", "Caixa", "2"], ["q", "3"], ["s", "available"]]


def test_parser_with_extra_spaces():
    """Test parser handles extra spaces correctly."""
    result = parser("l  Caixa   2  q   3")
    assert result == [["l", "Caixa", "2"], ["q", "3"]]


def test_parser_with_leading_trailing_spaces():
    """Test parser handles leading and trailing spaces."""
    result = parser("  l Caixa 2 q 3  ")
    assert result == [["l", "Caixa", "2"], ["q", "3"]]


def test_parser_empty_string():
    """Test parser with empty string."""
    result = parser("")
    assert result == []


def test_parser_only_spaces():
    """Test parser with only spaces."""
    result = parser("   ")
    assert result == []


def test_parser_single_operation_no_value():
    """Test parser with operation but no value."""
    result = parser("l")
    assert result == [["l"]]


def test_parser_case_insensitive_operations():
    """Test parser handles uppercase operations."""
    result = parser("L Caixa Q 3")
    assert result == [["L", "Caixa"], ["Q", "3"]]


def test_parser_mixed_case_operations():
    """Test parser handles mixed case operations."""
    result = parser("l Caixa Q 3 S available")
    assert result == [["l", "Caixa"], ["Q", "3"], ["S", "available"]]


def test_parser_consecutive_operations():
    """Test parser with consecutive operations without values."""
    result = parser("l q s")
    assert result == [["l"], ["q"], ["s"]]


def test_parser_value_with_spaces_single_word():
    """Test parser with single word values."""
    result = parser("l Box")
    assert result == [["l", "Box"]]


def test_parser_multiple_values_after_operation():
    """Test parser with multiple consecutive values after operation."""
    result = parser("l Box 1 Red q 5 10")
    assert result == [["l", "Box", "1", "Red"], ["q", "5", "10"]]


def test_parser_complex_instruction():
    """Test parser with complex multi-operation instruction."""
    result = parser("l Storage Box 3 q 15 s in stock")
    assert result == [["l", "Storage", "Box", "3"], ["q", "15"], ["s", "in", "stock"]]
