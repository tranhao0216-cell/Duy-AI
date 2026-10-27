import io
import re
from zipfile import ZipFile

import pymupdf as fitz
import pytest

from translator.engine import TranslationError, translate_docx, translate_segments, translate_txt, translate_xml
from translator.pdf import translate_pdf


W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
M = 'http://schemas.openxmlformats.org/officeDocument/2006/math'


def fake_translate(texts):
    return [t.replace('Hello world', 'Xin chào thế giới').replace('Hello', 'Xin chào').replace('Energy', 'Năng lượng') for t in texts]


def sample_xml(body):
    return f'<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="{W}" xmlns:m="{M}"><w:body>{body}</w:body></w:document>'.encode()


def docx(parts):
    output = io.BytesIO()
    with ZipFile(output, 'w') as z:
        for name, content in parts.items():
            z.writestr(name, content)
    return output.getvalue()


def test_docx_preserves_every_nontext_byte_and_other_parts():
    xml = sample_xml('<w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:rPr><w:b/></w:rPr><w:t xml:space="preserve"> Hello </w:t></w:r><m:oMath><m:r><m:t>x² = 4</m:t></m:r></m:oMath></w:p><w:tbl><w:tr><w:tc><w:p><w:r><w:t>Hello world</w:t></w:r></w:p></w:tc></w:tr></w:tbl>')
    parts = {'word/document.xml': xml, 'word/styles.xml': b'unchanged styles', 'word/media/image1.png': b'\x89PNG\r\n', 'word/header1.xml': sample_xml('<w:p><w:r><w:t>Hello</w:t></w:r></w:p>')}
    translated, report = translate_docx(docx(parts), fake_translate)
    with ZipFile(io.BytesIO(translated)) as z:
        for name in ['word/styles.xml', 'word/media/image1.png']:
            assert z.read(name) == parts[name]
        changed = z.read('word/document.xml')
        mask = lambda value: re.sub(rb'(<w:t\b[^>]*>).*?(</w:t>)', rb'\1TEXT\2', value)
        assert mask(changed) == mask(xml)
        assert '<m:t>x² = 4</m:t>'.encode() in changed
        assert ' Xin chào '.encode() in changed
        assert 'Xin chào'.encode() in z.read('word/header1.xml')
        assert report['text_runs'] == 3


def test_latex_and_code_preserved_and_corrupt_translation_rejected():
    source = r'Hello $x^2+1$ and \(y=2\) and `code()`'
    assert translate_segments([source], fake_translate)[0] == source.replace('Hello', 'Xin chào')
    with pytest.raises(TranslationError):
        translate_segments([source], lambda _: ['Xin chào'])
    with pytest.raises(TranslationError):
        translate_segments(['Hello'], lambda _: [])


def test_fields_across_paragraphs_and_empty_elements():
    xml = sample_xml('<w:p><w:r><w:t/><w:t></w:t><w:t>Hello</w:t></w:r></w:p><w:p><w:r><w:fldChar w:fldCharType="begin"/></w:r></w:p><w:p><w:r><w:t>Hello</w:t></w:r></w:p><w:p><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>')
    report = {'text_runs': 0, 'parts': 0, 'skipped_fields': 0}
    result = translate_xml(xml, fake_translate, report)
    assert result.count('Xin chào'.encode()) == 1
    assert result.count(b'Hello') == 1


def test_invalid_files_and_dtd_rejected():
    with pytest.raises(TranslationError):
        translate_docx(b'not a zip', fake_translate)
    with pytest.raises(TranslationError):
        translate_xml(b'<!DOCTYPE xml><xml/>', fake_translate, {})


def test_txt_keeps_bom_line_endings_and_math():
    data = b'\xef\xbb\xbfHello $x=1$\r\n\r\nHello\n'
    result, _ = translate_txt(data, fake_translate)
    assert result == '\ufeffXin chào $x=1$\r\n\r\nXin chào\n'.encode()


def make_pdf(text=True):
    with fitz.open() as doc:
        page = doc.new_page()
        if text:
            page.insert_text((72, 72), 'Hello world', fontsize=14)
            page.insert_text((72, 150), 'x = 2', fontsize=14)
        return doc.tobytes()


def test_pdf_translation_keeps_page_and_formula():
    result, report = translate_pdf(make_pdf(), fake_translate)
    with fitz.open(stream=result, filetype='pdf') as doc:
        assert len(doc) == 1
        text = doc[0].get_text()
        assert 'x = 2' in text
        assert 'Xin chào' in text
        assert 'Hello world' not in text
    assert report['protected_blocks'] == 1


def test_pdf_no_text_and_overflow_fail_closed():
    with pytest.raises(TranslationError, match='không có lớp chữ'):
        translate_pdf(make_pdf(False), fake_translate)
    with pytest.raises(TranslationError, match='không vừa khung'):
        translate_pdf(make_pdf(), lambda _: ['Bản dịch rất dài ' * 1000])


def test_http_validation_and_download(monkeypatch):
    import app as module
    client = module.app.test_client()
    assert client.get('/').status_code == 200
    assert client.post('/translate').status_code == 403
    headers = {'X-App-Token': module.LOCAL_TOKEN}
    assert client.post('/translate', headers=headers).status_code == 400
    monkeypatch.setattr(module, 'OpenAITranslator', lambda *args: fake_translate)
    response = client.post('/translate', headers=headers, data={'file': (io.BytesIO(b'Hello $x=2$'), 'sample.txt'), 'api_key': 'fake-key'})
    assert response.status_code == 200
    assert response.data == 'Xin chào $x=2$'.encode()
    assert '_vi.txt' in response.headers['Content-Disposition']
    assert response.headers['Cache-Control'] == 'no-store'
