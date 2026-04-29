import pytest
from script import parse_date, truncate_text, calculate_column_widths, format_row


class TestParseDate:
    def test_normal_date(self):
        assert parse_date("2026-03-15") == "2026-03-15 00:00:00"
    
    def test_swapped_month_day(self):
        assert parse_date("2026-15-03") == "2026-03-15 00:00:00"
    
    def test_another_swap_case(self):
        assert parse_date("2025-25-12") == "2025-12-25 00:00:00"
    
    def test_empty_date(self):
        assert parse_date("") == "0000-00-00 00:00:00"
    
    def test_none_date(self):
        assert parse_date(None) == "0000-00-00 00:00:00"
    
    def test_invalid_date(self):
        assert parse_date("invalid") == "0000-00-00 00:00:00"
    
    def test_date_with_time_already(self):
        result = parse_date("2026-03-15 12:30:45")
        assert result.startswith("2026-03-15")


class TestTruncateText:
    def test_no_truncate(self):
        assert truncate_text("hello", 10) == "hello"
    
    def test_truncate_with_ellipsis(self):
        result = truncate_text("hello world", 8)
        assert result == "hel..."
        assert len(result) == 8
    
    def test_very_short_width(self):
        result = truncate_text("hello", 2)
        assert len(result) <= 2
    
    def test_none_input(self):
        assert truncate_text(None, 10) == ''


class TestCalculateColumnWidths:
    def test_basic_widths(self):
        headers = ['Name', 'Age']
        rows = [['Alice', '30'], ['Bob', '25']]
        widths = calculate_column_widths(headers, rows, console_width=100)
        assert widths[0] >= len('Name')
        assert widths[1] >= len('Age')
    
    def test_min_width_enforced(self):
        headers = ['A', 'B']
        rows = [['x', 'y']]
        widths = calculate_column_widths(headers, rows, console_width=100, min_col_width=10)
        assert all(w >= 10 for w in widths)
    
    def test_console_width_truncation(self):
        headers = ['VeryLongHeader1', 'VeryLongHeader2']
        rows = [['data1', 'data2']]
        widths = calculate_column_widths(headers, rows, console_width=30)
        total = sum(widths) + len(widths) + 1
        assert total <= 30 or all(w == 10 for w in widths)


class TestFormatRow:
    def test_basic_formatting(self):
        row = ['Alice', '30']
        widths = [10, 5]
        result = format_row(row, widths)
        assert result.startswith('|')
        assert result.endswith('|')
        assert 'Alice' in result
        assert result.count('|') == 3
    
    def test_truncation_in_format(self):
        row = ['VeryLongName', '30']
        widths = [5, 5]
        result = format_row(row, widths)
        assert '...' in result or len(result.split('|')[1].strip()) <= 5