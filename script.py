#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Table display script for person data.
Reads tab-separated file with columns: ФИО, возраст, адрес, дата
"""

import argparse
import sys
import os
import re
# from datetime import datetime
from urllib.parse import urlparse
import shutil

try:
    import chardet
    HAS_CHARDET = True
except ImportError:
    HAS_CHARDET = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

'''
def detect_encoding(file_path):
    """Detect file encoding using chardet or fallback to common encodings."""
    if HAS_CHARDET:
        with open(file_path, 'rb') as f:
            raw = f.read(10000)
            result = chardet.detect(raw)
            return result['encoding'] or 'utf-8'
    # Fallback: try common encodings
    for enc in ['utf-8', 'cp1251', 'koi8-r', 'latin-1', 'utf-8-sig']:
        try:
            with open(file_path, 'r', encoding=enc, errors='strict') as f:
                f.read(10000)
            return enc
        except (UnicodeDecodeError, LookupError):
            continue
    return 'utf-8'
'''

def detect_encoding(file_path):
    """Detect file encoding with priority for UTF-8 variants."""
    # Try UTF-8 with BOM first (explicit marker for Cyrillic)
    try:
        with open(file_path, 'r', encoding='utf-8-sig', errors='strict') as f:
            f.read(32768)
        return 'utf-8-sig'
    except (UnicodeDecodeError, LookupError):
        pass
    
    # Try plain UTF-8 (most common)
    try:
        with open(file_path, 'r', encoding='utf-8', errors='strict') as f:
            f.read(32768)
        return 'utf-8'
    except (UnicodeDecodeError, LookupError):
        pass
    
    # Use chardet as intelligent fallback
    if HAS_CHARDET:
        try:
            with open(file_path, 'rb') as f:
                raw = f.read(32768)
            result = chardet.detect(raw)
            enc = result.get('encoding')
            confidence = result.get('confidence', 0)
            if enc and confidence > 0.7:
                with open(file_path, 'r', encoding=enc, errors='strict') as f:
                    f.read(32768)
                return enc
        except Exception:
            pass
    
    # Fallback to common Cyrillic encodings
    for enc in ['cp1251', 'koi8-r', 'iso-8859-5']:
        try:
            with open(file_path, 'r', encoding=enc, errors='strict') as f:
                f.read(32768)
            return enc
        except (UnicodeDecodeError, LookupError):
            continue
    
    # Last resort: UTF-8 with replacement chars
    return 'utf-8'

def parse_date(date_str):
    """
    Parse date string and normalize to YYYY-MM-DD HH:MM:SS format.
    If month > 12, swap day and month.
    """
    if not date_str or not date_str.strip():
        return "0000-00-00 00:00:00"
    
    date_str = date_str.strip()
    
    # Try to parse various date formats
    mono_date = re.sub(r'[-./\\: TТ]', '', date_str)
    parts = re.findall(r'^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})$', mono_date)[0]

    if len(parts) != 6: #
        return "0000-00-00 00:00:00"
        
    
    try:
        # Try to identify which part is year (4 digits)
        year_idx = None
        for i, p in enumerate(parts):
            if p.isdigit() and len(p) == 4:
                year_idx = i
                break
        
        if year_idx is None:
            return "0000-00-00 00:00:00"
        
        year = int(parts[year_idx])
        other_parts = [p for i, p in enumerate(parts) if i != year_idx]
        if len(other_parts) < 2:
            return "0000-00-00 00:00:00"
        try:
            val1 = int(other_parts[0])
            val2 = int(other_parts[1])
        except ValueError:
            return "0000-00-00 00:00:00"
        
        # If month > 12, swap day and month
        if val1 > 12:
            month, day = val2, val1
        elif val2 > 12:
            month, day = val1, val2
        else:
            # Both valid: assume standard order
            month, day = val1, val2
        
        # Validate ranges
        if not (1 <= month <= 12) or not (1 <= day <= 31):
            return "0000-00-00 00:00:00"
        
        try:
            valh = int(other_parts[2])
            valm = int(other_parts[3])
            vals = int(other_parts[4])
        except ValueError:
            return f"{year:04d}-{month:02d}-{day:02d} 00:00:00"
        
        hour, minute, second = valh, valm, vals
        if  not (0 <= hour <= 23) or not (0 <= minute <= 60) or not (0 <= second <= 60):
            return f"{year:04d}-{month:02d}-{day:02d} 00:00:00"
        
        return f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"
        
    except Exception:
        return "0000-00-00 00:00:00"

'''
def read_file_line_by_line(file_path, encoding):
    """Generator to read file line by line for memory efficiency."""
    with open(file_path, 'r', encoding=encoding, errors='replace') as f:
        for line in f:
            yield line.rstrip('\n\r')
'''


def read_file_line_by_line(file_path, encoding):
    """Генератор, который читает файл и исправляет 'кракозябры' на лету."""
    with open(file_path, 'r', encoding=encoding, errors='replace') as f:
        for line in f:
            clean_line = line.rstrip('\n\r')
            try:
                # Пытаемся починить строку, если это UTF-8, ошибочно прочитанный как latin-1/cp1252
                # Мы используем cp1252, так как она чаще всего порождает такие "Р Сџ"
                fixed_line = clean_line.encode('cp1252').decode('utf-8')
                yield fixed_line
            except (UnicodeEncodeError, UnicodeDecodeError):
                # Если починить не удалось (строка уже нормальная), отдаем как есть
                yield clean_line

'''
def read_url_line_by_line(url):
    """Generator to read URL content line by line."""
    if not HAS_REQUESTS:
        print("Error: 'requests' library is required for URL support", file=sys.stderr)
        sys.exit(1)
    
    response = requests.get(url, stream=True, timeout=30)
    response.raise_for_status()
    
    # Set encoding on response object, not in iter_lines()
    if response.encoding is None:
        response.encoding = 'utf-8'
    
    for line in response.iter_lines(decode_unicode=True):
        if line:
            yield line
'''

def read_url_line_by_line(url):
    """Генератор для чтения URL с исправлением 'кракозябр' на лету."""
    if not HAS_REQUESTS:
        print("Ошибка: библиотека 'requests' обязательна", file=sys.stderr)
        sys.exit(1)
    
    # Открываем поток (stream=True)
    response = requests.get(url, stream=True, timeout=30)
    response.raise_for_status()
    
    # Если кодировка не определена, используем latin-1 (она сохраняет байты для исправления)
    if response.encoding is None or response.encoding == 'ISO-8859-1':
        response.encoding = 'cp1252' 

    for line in response.iter_lines(decode_unicode=True):
        if not line:
            continue
            
        try:
            # Пытаемся починить строку, если это UTF-8, застрявший в cp1252
            fixed_line = line.encode('cp1252').decode('utf-8')
            yield fixed_line
        except (UnicodeEncodeError, UnicodeDecodeError):
            # Если строка уже нормальная или содержит другие символы
            yield line


def truncate_text(text, max_width):
    """Truncate text to fit within max_width, adding ellipsis if needed."""
    if not isinstance(text, str):
        text = str(text) if text is not None else ''
    if len(text) <= max_width:
        return text
    if max_width <= 3:
        return text[:max_width]
    return text[:max_width-3] + '...'


def calculate_column_widths(headers, rows, console_width, min_col_width=10):
    """Calculate optimal column widths based on content and console width."""
    num_cols = len(headers)
    if num_cols == 0:
        return []
    
    widths = [len(str(h)) for h in headers]
    
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(str(cell)))
    
    widths = [max(w, min_col_width) for w in widths]
    
    total_needed = sum(widths) + (num_cols + 1)
    
    if total_needed <= console_width:
        return widths
    
    available = console_width - (num_cols + 1)
    if available < num_cols * min_col_width:
        return [min_col_width] * num_cols
    
    total_original = sum(widths)
    if total_original == 0:
        return [min_col_width] * num_cols
    
    scale = available / total_original
    widths = [max(min_col_width, int(w * scale)) for w in widths]
    
    while sum(widths) + num_cols + 1 > console_width and any(w > min_col_width for w in widths):
        max_idx = widths.index(max(widths))
        widths[max_idx] = max(min_col_width, widths[max_idx] - 1)
    
    return widths


def format_row(row, widths):
    """Format a row with proper padding and separators."""
    cells = []
    for i, cell in enumerate(row):
        width = widths[i] if i < len(widths) else 10
        cell_str = str(cell) if cell is not None else ''
        truncated = truncate_text(cell_str, width)
        cells.append(truncated.ljust(width))
    return '|' + '|'.join(cells) + '|'


def format_separator(widths):
    """Create separator line for table."""
    return '+' + '+'.join(['-' * w for w in widths]) + '+'


def main():
    parser = argparse.ArgumentParser(
        description='Display tab-separated person data as a formatted table'
    )
    parser.add_argument(
        '-i', '--input',
        required=True,
        help='Path to input file or URL'
    )
    args = parser.parse_args()
    
    input_source = args.input
    is_url = urlparse(input_source).scheme in ('http', 'https')
    
    headers = ['ФИО', 'возраст', 'адрес', 'дата']
    rows = []
    
    try:
        if is_url:
            line_generator = read_url_line_by_line(input_source)
        else:
            if not os.path.exists(input_source):
                print(f"Error: File not found: {input_source}", file=sys.stderr)
                sys.exit(1)
            encoding = detect_encoding(input_source)
            line_generator = read_file_line_by_line(input_source, encoding)
        
        for line in line_generator:
            if not line.strip():
                continue
            parts = line.split('\t')
            while len(parts) < 4:
                parts.append('')
            if len(parts) > 4:
                parts = parts[:4]
            
            parts[3] = parse_date(parts[3])
            rows.append(parts)
            
    except Exception as e:
        print(f"Error reading input: {e}", file=sys.stderr)
        sys.exit(1)
    
    try:
        console_width = shutil.get_terminal_size().columns
    except Exception:
        console_width = 80
    
    widths = calculate_column_widths(headers, rows, console_width)
    
    separator = format_separator(widths)
    
    print(separator)
    print(format_row(headers, widths))
    print(separator)
    
    for row in rows:
        print(format_row(row, widths))
    
    print(separator)


if __name__ == '__main__':
    main()