#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JA16SJISTILDE / Shift-JIS 测试数据生成器

生成全量测试数据，用于验证 Oracle JA16SJISTILDE 到 UTF-8 的字符转换。

输出文件:
- test_data.csv: 主测试数据 (UTF-8 编码)
- test_data_sjis.csv: Shift-JIS 编码版本
- verify_utf8.html: UTF-8 验证网页
- verify_sjis.html: Shift-JIS 验证网页
- expected_utf8.csv: 预期导出结果 (UTF-8)
"""

import csv
import os
from typing import List, Tuple, Optional

# JA16SJISTILDE 使用 CP932 (Windows-31J) 映射
# Python 的 'cp932' 编码等同于 JA16SJISTILDE
SJIS_ENCODING = 'cp932'


def sjis_to_row_col(sjis_code: int) -> Tuple[int, int]:
    """将 Shift-JIS 双字节编码转换为 JIS 区位码"""
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
    """检查是否为有效的 Shift-JIS 双字节编码"""
    high = (sjis_code >> 8) & 0xFF
    low = sjis_code & 0xFF

    # 首字节范围: 0x81-0x9F 或 0xE0-0xFC
    if not ((0x81 <= high <= 0x9F) or (0xE0 <= high <= 0xFC)):
        return False

    # 次字节范围: 0x40-0x7E 或 0x80-0xFC
    if not ((0x40 <= low <= 0x7E) or (0x80 <= low <= 0xFC)):
        return False

    return True


def is_pua_character(sjis_code: int) -> bool:
    """检查是否为 PUA (私有使用区) 字符

    SJIS 0xF040-0xF9FC 映射到 Unicode U+E000-U+E757 (Private Use Area)
    这些字符在标准字体中没有字形，无法显示
    """
    high = (sjis_code >> 8) & 0xFF
    # PUA 区域的首字节范围是 0xF0-0xF9
    return 0xF0 <= high <= 0xF9


def get_category(sjis_code: int) -> str:
    """根据 Shift-JIS 编码确定字符类别"""
    # 单字节特殊字符
    if sjis_code == 0x5C:
        return "SPECIAL_SINGLE"
    if sjis_code == 0x7E:
        return "SPECIAL_SINGLE"

    # 单字节 ASCII
    if 0x20 <= sjis_code <= 0x7F:
        return "ASCII"

    # 半角片假名
    if 0xA1 <= sjis_code <= 0xDF:
        return "HALFWIDTH_KATAKANA"

    # 双字节字符
    if sjis_code > 0xFF:
        high = (sjis_code >> 8) & 0xFF
        low = sjis_code & 0xFF

        # 问题字符 (映射差异)
        problem_chars = [0x815C, 0x8160, 0x8161, 0x817C, 0x8191, 0x8192, 0x81CA]
        if sjis_code in problem_chars:
            return "PROBLEM"

        # 根据区位判断类别
        try:
            row, col = sjis_to_row_col(sjis_code)
            if 1 <= row <= 2:
                return "PUNCTUATION"
            elif row == 3:
                return "ALPHANUMERIC"
            elif row == 4:
                return "HIRAGANA"
            elif row == 5:
                return "KATAKANA"
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
    """生成字符描述

    Args:
        sjis_code: Shift-JIS 编码
        char: 字符
        category: 类别
        for_sjis: 是否用于 SJIS 编码文件（避免使用简体中文）
    """
    if for_sjis:
        # SJIS 文件使用英文描述
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
    else:
        # UTF-8 文件可以使用中文描述
        descriptions = {
            0x5C: "YEN SIGN / BACKSLASH",
            0x7E: "OVERLINE / TILDE",
            0x815C: "EM DASH (破折号)",
            0x8160: "WAVE DASH / FULLWIDTH TILDE (波浪线)",
            0x8161: "DOUBLE VERTICAL LINE (双竖线)",
            0x817C: "MINUS SIGN / FULLWIDTH HYPHEN-MINUS (减号)",
            0x8191: "CENT SIGN (分币符)",
            0x8192: "POUND SIGN (英镑符)",
            0x81CA: "NOT SIGN (非号)",
        }

    if sjis_code in descriptions:
        return descriptions[sjis_code]

    category_names = {
        "ASCII": "ASCII character",
        "HALFWIDTH_KATAKANA": "Halfwidth Katakana",
        "PUNCTUATION": "Punctuation/Symbol",
        "ALPHANUMERIC": "Fullwidth Alphanumeric",
        "HIRAGANA": "Hiragana",
        "KATAKANA": "Fullwidth Katakana",
        "GREEK": "Greek letter",
        "CYRILLIC": "Cyrillic letter",
        "BOX_DRAWING": "Box drawing character",
        "KANJI_LEVEL1": "JIS Level 1 Kanji",
        "KANJI_LEVEL2": "JIS Level 2 Kanji",
    }

    return category_names.get(category, "Other character")


def generate_test_data() -> List[dict]:
    """生成所有测试数据"""
    data = []
    id_counter = 1

    # 1. 问题字符 (最重要的测试点)
    problem_chars = [0x815C, 0x8160, 0x8161, 0x817C, 0x8191, 0x8192, 0x81CA]
    for sjis_code in problem_chars:
        try:
            sjis_bytes = bytes([(sjis_code >> 8) & 0xFF, sjis_code & 0xFF])
            char = sjis_bytes.decode(SJIS_ENCODING)
            utf8_bytes = char.encode('utf-8')
            unicode_point = ord(char)

            data.append({
                'id': id_counter,
                'sjis_hex': f'{sjis_code:04X}',
                'char': char,
                'utf8_hex': utf8_bytes.hex().upper(),
                'unicode': f'U+{unicode_point:04X}',
                'category': 'PROBLEM',
                'description': get_description(sjis_code, char, 'PROBLEM', for_sjis=False),
                'description_sjis': get_description(sjis_code, char, 'PROBLEM', for_sjis=True)
            })
            id_counter += 1
        except Exception as e:
            print(f"Error processing problem char 0x{sjis_code:04X}: {e}")

    # 2. 单字节特殊字符 (0x5C, 0x7E)
    for sjis_code in [0x5C, 0x7E]:
        try:
            sjis_bytes = bytes([sjis_code])
            char = sjis_bytes.decode(SJIS_ENCODING)
            utf8_bytes = char.encode('utf-8')
            unicode_point = ord(char)
            desc = get_description(sjis_code, char, 'SPECIAL_SINGLE', for_sjis=False)

            data.append({
                'id': id_counter,
                'sjis_hex': f'{sjis_code:02X}',
                'char': char,
                'utf8_hex': utf8_bytes.hex().upper(),
                'unicode': f'U+{unicode_point:04X}',
                'category': 'SPECIAL_SINGLE',
                'description': desc,
                'description_sjis': desc  # 这些描述本来就是英文
            })
            id_counter += 1
        except Exception as e:
            print(f"Error processing single byte 0x{sjis_code:02X}: {e}")

    # 3. ASCII 可打印字符 (0x20-0x7F, 排除 0x5C 和 0x7E)
    for sjis_code in range(0x20, 0x80):
        if sjis_code in [0x5C, 0x7E, 0x7F]:  # 排除特殊字符和 DEL
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

    # 4. 半角片假名 (0xA1-0xDF)
    for sjis_code in range(0xA1, 0xE0):
        try:
            sjis_bytes = bytes([sjis_code])
            char = sjis_bytes.decode(SJIS_ENCODING)
            utf8_bytes = char.encode('utf-8')
            desc = get_description(sjis_code, char, 'HALFWIDTH_KATAKANA')

            data.append({
                'id': id_counter,
                'sjis_hex': f'{sjis_code:02X}',
                'char': char,
                'utf8_hex': utf8_bytes.hex().upper(),
                'unicode': f'U+{ord(char):04X}',
                'category': 'HALFWIDTH_KATAKANA',
                'description': desc,
                'description_sjis': desc
            })
            id_counter += 1
        except Exception as e:
            print(f"Error processing halfwidth katakana 0x{sjis_code:02X}: {e}")

    # 5. 双字节字符 (全量遍历)
    # 首字节范围: 0x81-0x9F, 0xE0-0xFC
    # 次字节范围: 0x40-0x7E, 0x80-0xFC

    processed_problem = set(problem_chars)  # 问题字符已经处理过

    for high in list(range(0x81, 0xA0)) + list(range(0xE0, 0xFD)):
        for low in list(range(0x40, 0x7F)) + list(range(0x80, 0xFD)):
            sjis_code = (high << 8) | low

            if sjis_code in processed_problem:
                continue

            if not is_valid_sjis_doublebyte(sjis_code):
                continue

            # 排除 PUA (私有使用区) 字符 - 这些字符无法在标准字体中显示
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
                # 无效的编码，跳过
                pass
            except Exception as e:
                # 其他错误，记录但继续
                pass

    return data


def write_csv_utf8(data: List[dict], filename: str):
    """写入 UTF-8 编码的 CSV 文件"""
    fieldnames = ['id', 'sjis_hex', 'char', 'utf8_hex', 'unicode', 'category', 'description']
    with open(filename, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(data)
    print(f"Generated: {filename} ({len(data)} rows)")


def write_csv_sjis(data: List[dict], filename: str):
    """写入 Shift-JIS 编码的 CSV 文件"""
    fieldnames = ['id', 'sjis_hex', 'char', 'utf8_hex', 'unicode', 'category', 'description']
    with open(filename, 'w', encoding=SJIS_ENCODING, newline='', errors='replace') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for row in data:
            try:
                # 使用 SJIS 兼容的描述
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
    """生成 UTF-8 编码的验证网页"""
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
    <h1>JA16SJISTILDE 测试数据验证 (UTF-8)</h1>
    <div class="stats">
        <strong>统计:</strong> 共 ''' + str(len(data)) + ''' 个字符<br>
        <strong>编码:</strong> 此文件使用 UTF-8 编码<br>
        <strong>验证方法:</strong> 检查所有字符是否正确显示，无乱码
    </div>
    <table>
        <tr>
            <th>ID</th>
            <th>SJIS Hex</th>
            <th>字符</th>
            <th>UTF-8 Hex</th>
            <th>Unicode</th>
            <th>类别</th>
            <th>说明</th>
        </tr>
'''

    for row in data:
        row_class = ''
        if row['category'] == 'PROBLEM':
            row_class = 'class="problem"'
        elif row['category'] == 'SPECIAL_SINGLE':
            row_class = 'class="special"'

        # 对特殊 HTML 字符进行转义
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
        <strong>特别注意:</strong><br>
        - 红色高亮行是"问题字符"，这些字符在不同实现中映射不同<br>
        - 黄色高亮行是单字节特殊字符 (0x5C, 0x7E)
    </div>
</body>
</html>
'''

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Generated: {filename}")


def write_html_sjis(data: List[dict], filename: str):
    """生成 Shift-JIS 编码的验证网页"""
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
    <h1>JA16SJISTILDE 検証データ (Shift_JIS)</h1>
    <div class="stats">
        <strong>統計:</strong> 全 ''' + str(len(data)) + ''' 文字<br>
        <strong>エンコード:</strong> このファイルは Shift_JIS でエンコードされています<br>
        <strong>検証方法:</strong> 全ての文字が正しく表示されているか確認してください
    </div>
    <table>
        <tr>
            <th>ID</th>
            <th>SJIS Hex</th>
            <th>文字</th>
            <th>UTF-8 Hex</th>
            <th>Unicode</th>
            <th>カテゴリ</th>
            <th>説明</th>
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

        # 使用 SJIS 兼容的描述（纯英文）
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
        <strong>注意:</strong><br>
        - 赤色のハイライト行は「問題文字」です（異なる実装でマッピングが異なる）<br>
        - 黄色のハイライト行はシングルバイト特殊文字 (0x5C, 0x7E)
    </div>
</body>
</html>
'''

    with open(filename, 'w', encoding=SJIS_ENCODING, errors='replace') as f:
        f.write(html)
    print(f"Generated: {filename}")


def write_expected_utf8(data: List[dict], filename: str):
    """生成预期的 UTF-8 导出结果 (简化格式，只包含 id 和字符)"""
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
    """打印数据统计摘要"""
    categories = {}
    for row in data:
        cat = row['category']
        categories[cat] = categories.get(cat, 0) + 1

    print("\n=== 测试数据统计 ===")
    print(f"总字符数: {len(data)}")
    print("\n按类别分布:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")

    print("\n=== 问题字符列表 (映射差异) ===")
    for row in data:
        if row['category'] == 'PROBLEM':
            print(f"  SJIS 0x{row['sjis_hex']} -> {row['char']} -> UTF-8 {row['utf8_hex']} ({row['unicode']}) - {row['description']}")


def main():
    print("Generating JA16SJISTILDE test data...")
    print(f"Using encoding: {SJIS_ENCODING}")

    # 生成测试数据
    data = generate_test_data()

    # 输出目录
    output_dir = os.path.dirname(os.path.abspath(__file__))

    # 写入文件
    write_csv_utf8(data, os.path.join(output_dir, 'test_data.csv'))
    write_csv_sjis(data, os.path.join(output_dir, 'test_data_sjis.csv'))
    write_html_utf8(data, os.path.join(output_dir, 'verify_utf8.html'))
    write_html_sjis(data, os.path.join(output_dir, 'verify_sjis.html'))
    write_expected_utf8(data, os.path.join(output_dir, 'expected_utf8.csv'))

    # 打印统计
    print_summary(data)

    print("\n=== 完成 ===")
    print("请用浏览器打开 verify_utf8.html 和 verify_sjis.html 进行手工验证。")


if __name__ == '__main__':
    main()
