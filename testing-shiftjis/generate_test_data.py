#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JA16SJISTILDE / Shift-JIS Test Data Generator

Generates full test data for verifying Oracle JA16SJISTILDE to UTF-8 character conversion.

Output files:
- test_data.csv: Main test data (UTF-8 encoded)
- test_data_sjis.csv: Shift-JIS encoded version
- verify_utf8.html: UTF-8 verification web page
- verify_sjis.html: Shift-JIS verification web page
- expected_utf8.csv: Expected export results (UTF-8)
"""

import csv
import os
from typing import List, Tuple, Optional

# JA16SJISTILDE uses CP932 (Windows-31J) mapping
# Python's 'cp932' encoding is equivalent to JA16SJISTILDE
SJIS_ENCODING = 'cp932'


def sjis_to_row_col(sjis_code: int) -> Tuple[int, int]:
    """Convert Shift-JIS double-byte code to JIS row/column (ku/ten)."""
    high = (sjis_code >> 8) & 0xFF
    low = sjis_code & 0xFF

    if high <= 0x9F:
        row = (high - 0x81) * 2 + 1
    else:
        row = (high - 0xC1) * 2 + 1

    if low < 0x7F:
        col = low - 0x40 + 1
    elif low <= 0x9E:
        col = low - 0x40
    else:
        row += 1
        col = low - 0x9E

    return row, col


def is_valid_sjis_doublebyte(sjis_code: int) -> bool:
    """Check if a code is a valid Shift-JIS double-byte encoding."""
    high = (sjis_code >> 8) & 0xFF
    low = sjis_code & 0xFF

    # Lead byte range: 0x81-0x9F or 0xE0-0xFC
    if not ((0x81 <= high <= 0x9F) or (0xE0 <= high <= 0xFC)):
        return False

    # Trail byte range: 0x40-0x7E or 0x80-0xFC
    if not ((0x40 <= low <= 0x7E) or (0x80 <= low <= 0xFC)):
        return False

    return True


def is_pua_character(sjis_code: int) -> bool:
    """Check if a character is in PUA (Private Use Area).

    SJIS 0xF040-0xF9FC maps to Unicode U+E000-U+E757 (Private Use Area).
    These characters have no glyphs in standard fonts and cannot be displayed.
    """
    high = (sjis_code >> 8) & 0xFF
    # PUA lead byte range: 0xF0-0xF9
    return 0xF0 <= high <= 0xF9


def get_category(sjis_code: int) -> str:
    """Determine character category based on Shift-JIS code."""
    # Single-byte special characters
    if sjis_code == 0x5C:
        return "SPECIAL_SINGLE"
    if sjis_code == 0x7E:
        return "SPECIAL_SINGLE"

    # Single-byte ASCII
    if 0x20 <= sjis_code <= 0x7F:
        return "ASCII"

    # Halfwidth Katakana
    if 0xA1 <= sjis_code <= 0xDF:
        return "KATAKANA_HALFWIDTH"

    # Double-byte characters
    if sjis_code > 0xFF:
        high = (sjis_code >> 8) & 0xFF
        low = sjis_code & 0xFF

        # Problem characters (mapping differences)
        problem_chars = [0x815C, 0x8160, 0x8161, 0x817C, 0x8191, 0x8192, 0x81CA]
        if sjis_code in problem_chars:
            return "PROBLEM"

        # Determine category by JIS row
        try:
            row, col = sjis_to_row_col(sjis_code)
            if 1 <= row <= 2:
                return "PUNCTUATION"
            elif row == 3:
                return "ALPHANUMERIC"
            elif row == 4:
                return "HIRAGANA_FULLWIDTH"
            elif row == 5:
                return "KATAKANA_FULLWIDTH"
            elif row == 6:
                return "GREEK"
            elif row == 7:
                return "CYRILLIC"
            elif row == 8:
                return "BOX_DRAWING"
            elif 16 <= row <= 47:
                return "KANJI_LEVEL1"
            elif 48 <= row <= 84:
                return "KANJI_LEVEL2"
            else:
                return "OTHER"
        except:
            return "OTHER"

    return "OTHER"


def get_description(sjis_code: int, char: str, category: str, for_sjis: bool = False) -> str:
    """Generate character description.

    Args:
        sjis_code: Shift-JIS code
        char: The character
        category: Category string
        for_sjis: Whether for SJIS-encoded file (avoid non-SJIS characters)
    """
    descriptions = {
        0x5C: "YEN SIGN / BACKSLASH",
        0x7E: "OVERLINE / TILDE",
        0x815C: "EM DASH",
        0x8160: "WAVE DASH / FULLWIDTH TILDE",
        0x8161: "DOUBLE VERTICAL LINE",
        0x817C: "MINUS SIGN / FULLWIDTH HYPHEN-MINUS",
        0x8191: "CENT SIGN",
        0x8192: "POUND SIGN",
        0x81CA: "NOT SIGN",
    }

    if sjis_code in descriptions:
        return descriptions[sjis_code]

    category_names = {
        "ASCII": "ASCII character",
        "KATAKANA_HALFWIDTH": "Halfwidth Katakana (SJIS:0xA1-0xDF U+FF61-FF9F)",
        "PUNCTUATION": "Punctuation/Symbol",
        "ALPHANUMERIC": "Fullwidth Alphanumeric",
        "HIRAGANA_FULLWIDTH": "Fullwidth Hiragana (SJIS:0x829F-0x82F1 U+3041-3093)",
        "KATAKANA_FULLWIDTH": "Fullwidth Katakana (SJIS:0x8340-0x8396 U+30A1-30F6)",
        "GREEK": "Greek letter",
        "CYRILLIC": "Cyrillic letter",
        "BOX_DRAWING": "Box drawing character",
        "KANJI_LEVEL1": "JIS Level 1 Kanji",
        "KANJI_LEVEL2": "JIS Level 2 Kanji",
    }

    return category_names.get(category, "Other character")


def generate_test_data() -> List[dict]:
    """Generate all test data."""
    data = []
    id_counter = 1

    # 1. Problem characters (most important test points)
    problem_chars = [0x815C, 0x8160, 0x8161, 0x817C, 0x8191, 0x8192, 0x81CA]
    for sjis_code in problem_chars:
        try:
            sjis_bytes = bytes([(sjis_code >> 8) & 0xFF, sjis_code & 0xFF])
            char = sjis_bytes.decode(SJIS_ENCODING)
            utf8_bytes = char.encode('utf-8')
            unicode_point = ord(char)

            desc = get_description(sjis_code, char, 'PROBLEM')
            data.append({
                'id': id_counter,
                'sjis_hex': f'{sjis_code:04X}',
                'char': char,
                'utf8_hex': utf8_bytes.hex().upper(),
                'unicode': f'U+{unicode_point:04X}',
                'category': 'PROBLEM',
                'description': desc,
                'description_sjis': desc
            })
            id_counter += 1
        except Exception as e:
            print(f"Error processing problem char 0x{sjis_code:04X}: {e}")

    # 2. Single-byte special characters (0x5C, 0x7E)
    for sjis_code in [0x5C, 0x7E]:
        try:
            sjis_bytes = bytes([sjis_code])
            char = sjis_bytes.decode(SJIS_ENCODING)
            utf8_bytes = char.encode('utf-8')
            unicode_point = ord(char)
            desc = get_description(sjis_code, char, 'SPECIAL_SINGLE')

            data.append({
                'id': id_counter,
                'sjis_hex': f'{sjis_code:02X}',
                'char': char,
                'utf8_hex': utf8_bytes.hex().upper(),
                'unicode': f'U+{unicode_point:04X}',
                'category': 'SPECIAL_SINGLE',
                'description': desc,
                'description_sjis': desc
            })
            id_counter += 1
        except Exception as e:
            print(f"Error processing single byte 0x{sjis_code:02X}: {e}")

    # 3. Printable ASCII characters (0x20-0x7F, excluding 0x5C and 0x7E)
    for sjis_code in range(0x20, 0x80):
        if sjis_code in [0x5C, 0x7E, 0x7F]:  # Exclude special chars and DEL
            continue
        try:
            char = chr(sjis_code)
            utf8_bytes = char.encode('utf-8')
            desc = get_description(sjis_code, char, 'ASCII')

            data.append({
                'id': id_counter,
                'sjis_hex': f'{sjis_code:02X}',
                'char': char,
                'utf8_hex': utf8_bytes.hex().upper(),
                'unicode': f'U+{ord(char):04X}',
                'category': 'ASCII',
                'description': desc,
                'description_sjis': desc
            })
            id_counter += 1
        except Exception as e:
            print(f"Error processing ASCII 0x{sjis_code:02X}: {e}")

    # 4. Halfwidth Katakana (0xA1-0xDF)
    for sjis_code in range(0xA1, 0xE0):
        try:
            sjis_bytes = bytes([sjis_code])
            char = sjis_bytes.decode(SJIS_ENCODING)
            utf8_bytes = char.encode('utf-8')
            desc = get_description(sjis_code, char, 'KATAKANA_HALFWIDTH')

            data.append({
                'id': id_counter,
                'sjis_hex': f'{sjis_code:02X}',
                'char': char,
                'utf8_hex': utf8_bytes.hex().upper(),
                'unicode': f'U+{ord(char):04X}',
                'category': 'KATAKANA_HALFWIDTH',
                'description': desc,
                'description_sjis': desc
            })
            id_counter += 1
        except Exception as e:
            print(f"Error processing halfwidth katakana 0x{sjis_code:02X}: {e}")

    # 5. Double-byte characters (full enumeration)
    # Lead byte range: 0x81-0x9F, 0xE0-0xFC
    # Trail byte range: 0x40-0x7E, 0x80-0xFC

    processed_problem = set(problem_chars)  # Problem chars already processed

    for high in list(range(0x81, 0xA0)) + list(range(0xE0, 0xFD)):
        for low in list(range(0x40, 0x7F)) + list(range(0x80, 0xFD)):
            sjis_code = (high << 8) | low

            if sjis_code in processed_problem:
                continue

            if not is_valid_sjis_doublebyte(sjis_code):
                continue

            # Exclude PUA (Private Use Area) characters - no glyphs in standard fonts
            if is_pua_character(sjis_code):
                continue

            try:
                sjis_bytes = bytes([high, low])
                char = sjis_bytes.decode(SJIS_ENCODING)
                utf8_bytes = char.encode('utf-8')
                category = get_category(sjis_code)
                desc = get_description(sjis_code, char, category)

                data.append({
                    'id': id_counter,
                    'sjis_hex': f'{sjis_code:04X}',
                    'char': char,
                    'utf8_hex': utf8_bytes.hex().upper(),
                    'unicode': f'U+{ord(char):04X}',
                    'category': category,
                    'description': desc,
                    'description_sjis': desc
                })
                id_counter += 1
            except (UnicodeDecodeError, UnicodeEncodeError):
                # Invalid encoding, skip
                pass
            except Exception as e:
                # Other errors, log and continue
                pass

    return data


def write_csv_utf8(data: List[dict], filename: str):
    """Write UTF-8 encoded CSV file."""
    fieldnames = ['id', 'sjis_hex', 'char', 'utf8_hex', 'unicode', 'category', 'description']
    with open(filename, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(data)
    print(f"Generated: {filename} ({len(data)} rows)")


def write_csv_sjis(data: List[dict], filename: str):
    """Write Shift-JIS encoded CSV file."""
    fieldnames = ['id', 'sjis_hex', 'char', 'utf8_hex', 'unicode', 'category', 'description']
    with open(filename, 'w', encoding=SJIS_ENCODING, newline='', errors='replace') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for row in data:
            try:
                # Use SJIS-compatible description
                safe_row = row.copy()
                safe_row['description'] = row.get('description_sjis', row['description'])
                writer.writerow(safe_row)
            except UnicodeEncodeError:
                safe_row = row.copy()
                desc = row.get('description_sjis', row['description'])
                safe_row['description'] = desc.encode(SJIS_ENCODING, errors='replace').decode(SJIS_ENCODING)
                writer.writerow(safe_row)
    print(f"Generated: {filename}")


def write_html_utf8(data: List[dict], filename: str):
    """Generate UTF-8 encoded verification web page."""
    html = '''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>Shift-JIS Test Data - UTF-8 Verification</title>
    <style>
        body { font-family: "MS Gothic", "Hiragino Kaku Gothic Pro", monospace; margin: 20px; }
        h1 { color: #333; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #4CAF50; color: white; }
        tr:nth-child(even) { background-color: #f2f2f2; }
        tr.problem td { background-color: #ffcccc !important; font-weight: bold; }
        tr.special td { background-color: #ffffcc !important; }
        .char-cell { font-size: 24px; text-align: center; }
        .stats { margin: 20px 0; padding: 10px; background-color: #e7f3fe; border-left: 4px solid #2196F3; }
    </style>
</head>
<body>
    <h1>JA16SJISTILDE Test Data Verification (UTF-8)</h1>
    <div class="stats">
        <strong>Statistics:</strong> Total ''' + str(len(data)) + ''' characters<br>
        <strong>Encoding:</strong> This file is encoded in UTF-8<br>
        <strong>Verification:</strong> Check that all characters display correctly without garbled text
    </div>
    <table>
        <tr>
            <th>ID</th>
            <th>SJIS Hex</th>
            <th>Char</th>
            <th>UTF-8 Hex</th>
            <th>Unicode</th>
            <th>Category</th>
            <th>Description</th>
        </tr>
'''

    for row in data:
        row_class = ''
        if row['category'] == 'PROBLEM':
            row_class = 'class="problem"'
        elif row['category'] == 'SPECIAL_SINGLE':
            row_class = 'class="special"'

        # Escape special HTML characters
        char_display = row['char']
        if char_display == '<':
            char_display = '&lt;'
        elif char_display == '>':
            char_display = '&gt;'
        elif char_display == '&':
            char_display = '&amp;'
        elif char_display == '"':
            char_display = '&quot;'

        html += f'''        <tr {row_class}>
            <td>{row['id']}</td>
            <td>{row['sjis_hex']}</td>
            <td class="char-cell">{char_display}</td>
            <td>{row['utf8_hex']}</td>
            <td>{row['unicode']}</td>
            <td>{row['category']}</td>
            <td>{row['description']}</td>
        </tr>
'''

    html += '''    </table>
    <div class="stats">
        <strong>Note:</strong><br>
        - Red highlighted rows are "problem characters" that map differently across implementations<br>
        - Yellow highlighted rows are single-byte special characters (0x5C, 0x7E)
    </div>
</body>
</html>
'''

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Generated: {filename}")


def write_html_sjis(data: List[dict], filename: str):
    """Generate Shift-JIS encoded verification web page."""
    html = '''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="Shift_JIS">
    <title>Shift-JIS Test Data - SJIS Verification</title>
    <style>
        body { font-family: "MS Gothic", monospace; margin: 20px; }
        h1 { color: #333; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #4CAF50; color: white; }
        tr:nth-child(even) { background-color: #f2f2f2; }
        tr.problem td { background-color: #ffcccc !important; font-weight: bold; }
        tr.special td { background-color: #ffffcc !important; }
        .char-cell { font-size: 24px; text-align: center; }
        .stats { margin: 20px 0; padding: 10px; background-color: #e7f3fe; border-left: 4px solid #2196F3; }
    </style>
</head>
<body>
    <h1>JA16SJISTILDE Verification Data (Shift_JIS)</h1>
    <div class="stats">
        <strong>Statistics:</strong> Total ''' + str(len(data)) + ''' characters<br>
        <strong>Encoding:</strong> This file is encoded in Shift_JIS<br>
        <strong>Verification:</strong> Check that all characters display correctly
    </div>
    <table>
        <tr>
            <th>ID</th>
            <th>SJIS Hex</th>
            <th>Char</th>
            <th>UTF-8 Hex</th>
            <th>Unicode</th>
            <th>Category</th>
            <th>Description</th>
        </tr>
'''

    for row in data:
        row_class = ''
        if row['category'] == 'PROBLEM':
            row_class = 'class="problem"'
        elif row['category'] == 'SPECIAL_SINGLE':
            row_class = 'class="special"'

        char_display = row['char']
        if char_display == '<':
            char_display = '&lt;'
        elif char_display == '>':
            char_display = '&gt;'
        elif char_display == '&':
            char_display = '&amp;'
        elif char_display == '"':
            char_display = '&quot;'

        # Use SJIS-compatible description (English only)
        desc = row.get('description_sjis', row['description'])

        html += f'''        <tr {row_class}>
            <td>{row['id']}</td>
            <td>{row['sjis_hex']}</td>
            <td class="char-cell">{char_display}</td>
            <td>{row['utf8_hex']}</td>
            <td>{row['unicode']}</td>
            <td>{row['category']}</td>
            <td>{desc}</td>
        </tr>
'''

    html += '''    </table>
    <div class="stats">
        <strong>Note:</strong><br>
        - Red highlighted rows are "problem characters" that map differently across implementations<br>
        - Yellow highlighted rows are single-byte special characters (0x5C, 0x7E)
    </div>
</body>
</html>
'''

    with open(filename, 'w', encoding=SJIS_ENCODING, errors='replace') as f:
        f.write(html)
    print(f"Generated: {filename}")


def write_expected_utf8(data: List[dict], filename: str):
    """Generate expected UTF-8 export results (simplified: id and char only)."""
    with open(filename, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'char_data'])
        writer.writeheader()
        for row in data:
            writer.writerow({
                'id': row['id'],
                'char_data': row['char']
            })
    print(f"Generated: {filename}")


def print_summary(data: List[dict]):
    """Print data statistics summary."""
    categories = {}
    for row in data:
        cat = row['category']
        categories[cat] = categories.get(cat, 0) + 1

    print("\n=== Test Data Statistics ===")
    print(f"Total characters: {len(data)}")
    print("\nDistribution by category:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")

    print("\n=== Problem Characters (mapping differences) ===")
    for row in data:
        if row['category'] == 'PROBLEM':
            print(f"  SJIS 0x{row['sjis_hex']} -> {row['char']} -> UTF-8 {row['utf8_hex']} ({row['unicode']}) - {row['description']}")


def main():
    print("Generating JA16SJISTILDE test data...")
    print(f"Using encoding: {SJIS_ENCODING}")

    # Generate test data
    data = generate_test_data()

    # Output directory
    output_dir = os.path.dirname(os.path.abspath(__file__))

    # Write files
    write_csv_utf8(data, os.path.join(output_dir, 'test_data.csv'))
    write_csv_sjis(data, os.path.join(output_dir, 'test_data_sjis.csv'))
    write_html_utf8(data, os.path.join(output_dir, 'verify_utf8.html'))
    write_html_sjis(data, os.path.join(output_dir, 'verify_sjis.html'))
    write_expected_utf8(data, os.path.join(output_dir, 'expected_utf8.csv'))

    # Print statistics
    print_summary(data)

    print("\n=== Done ===")
    print("Open verify_utf8.html and verify_sjis.html in a browser for manual verification.")


if __name__ == '__main__':
    main()
