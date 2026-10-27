"""Conservative PDF text overlay. Formula-like blocks are never redacted."""
import os
import re
from pathlib import Path

import pymupdf as fitz

from .engine import TranslationError, translate_segments


def font_path():
    supplied = os.environ.get('VIET_FONT_PATH')
    candidates = [supplied] if supplied else [
        str(Path(__file__).parent / 'fonts' / 'DejaVuSans.ttf'),
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        'C:/Windows/Fonts/arial.ttf', '/System/Library/Fonts/Supplemental/Arial.ttf',
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return candidate
    raise TranslationError('Thiếu font tiếng Việt. Đặt VIET_FONT_PATH trỏ tới font TTF có hỗ trợ tiếng Việt.')


def is_formula(spans):
    text = ''.join(s['text'] for s in spans)
    math_font = any(re.search(r'math|symbol|cmmi|cmsy|cmex|msam|msbm', s['font'], re.I) for s in spans)
    math_symbol = re.search(r'[=∫∑√∂∇∞≤≥≈≠∏∈∉∀∃±×÷∝α-ωΑ-Ω]|[A-Za-z]\s*\^|\$|\\(?:frac|sum|int)', text)
    return bool(math_font or math_symbol)


def translate_pdf(data, translate):
    try:
        doc = fitz.open(stream=data, filetype='pdf')
    except Exception as exc:
        raise TranslationError('File PDF không hợp lệ.') from exc
    with doc:
        if doc.needs_pass:
            raise TranslationError('PDF có mật khẩu. Hãy tải bản đã mở khóa.')
        if len(doc) > 100:
            raise TranslationError('Bản này hỗ trợ tối đa 100 trang PDF mỗi lần.')
        if doc.get_sigflags() > 0:
            raise TranslationError('PDF có chữ ký số; hãy dùng bản sao chưa ký.')
        font = font_path()
        report = {'pages': len(doc), 'blocks': 0, 'protected_blocks': 0, 'scan_pages': []}
        for page in doc:
            if page.rotation:
                raise TranslationError(f'Trang {page.number + 1} bị xoay. Hãy xoay trang về 0° trước khi dịch.')
            blocks = page.get_text('dict')['blocks']
            text_blocks = [b for b in blocks if b['type'] == 0]
            if not any(s['text'].strip() for b in text_blocks for line in b['lines'] for s in line['spans']):
                report['scan_pages'].append(page.number + 1)
                continue
            edits = []
            for block in text_blocks:
                spans = [s for line in block['lines'] for s in line['spans'] if s['text'].strip()]
                if not spans:
                    continue
                if any(tuple(line.get('dir', (1, 0))) != (1.0, 0.0) for line in block['lines']):
                    report['protected_blocks'] += 1
                    continue
                if is_formula(spans):
                    report['protected_blocks'] += 1
                    continue
                source = '\n'.join(''.join(s['text'] for s in line['spans']) for line in block['lines'])
                if not re.search(r'[A-Za-z]{2}', source):
                    continue
                translated = translate_segments([source], translate)[0]
                rect = fitz.Rect(block['bbox'])
                size = max(5, min(s['size'] for s in spans))
                color_int = spans[0]['color']
                color = tuple(((color_int >> shift) & 255) / 255 for shift in (16, 8, 0))
                # Do not erase until a temporary page proves the text fits.
                with fitz.open() as probe:
                    test = probe.new_page(width=page.rect.width, height=page.rect.height)
                    test.insert_font(fontname='Viet', fontfile=font)
                    while size >= 5:
                        result = test.insert_textbox(rect, translated, fontname='Viet', fontsize=size, color=color)
                        if result >= 0:
                            break
                        size -= 0.5
                    else:
                        raise TranslationError(f'Bản dịch trang {page.number + 1} không vừa khung. Hãy dùng Word nguồn hoặc rút ngắn bản dịch.')
                edits.append((rect, translated, size, color, spans))
            for rect, _, _, _, spans in edits:
                # Redact glyph boxes only, leaving surrounding images/vector artwork.
                for span in spans:
                    page.add_redact_annot(span['bbox'], fill=False, cross_out=False)
            if edits:
                page.apply_redactions(images=0, graphics=0, text=0)
                page.insert_font(fontname='Viet', fontfile=font)
                for rect, translated, size, color, _ in edits:
                    if page.insert_textbox(rect, translated, fontname='Viet', fontsize=size, color=color) < 0:
                        raise TranslationError('Không thể đặt bản dịch vào PDF. Đã dừng xuất.')
                    report['blocks'] += 1
        if report['scan_pages']:
            pages = ', '.join(map(str, report['scan_pages'][:15]))
            raise TranslationError(f'Trang {pages} không có lớp chữ (có thể là bản scan hoặc trang trống). Bản này chưa có OCR. Hãy dùng PDF có lớp chữ hoặc Word nguồn.')
        if not report['blocks']:
            raise TranslationError('Không tìm thấy vùng tiếng Anh có thể dịch an toàn trong PDF.')
        return doc.tobytes(garbage=4, deflate=True), report
