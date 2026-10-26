from translator.engine import translate_txt, translate_xml
from test_translation import fake_translate, sample_xml


def test_multiline_math_is_not_sent_to_model():
    source = 'Hello\n$$\nx^2 + 1 = 0\n$$\nHello'
    output, _ = translate_txt(source.encode(), fake_translate)
    assert output.decode() == source.replace('Hello', 'Xin chào')


def test_split_latex_runs_keep_whole_paragraph():
    xml = sample_xml('<w:p><w:r><w:t>Hello $x</w:t></w:r><w:r><w:t>+1$</w:t></w:r></w:p>')
    report = {'text_runs': 0, 'parts': 0, 'skipped_fields': 0}
    assert translate_xml(xml, fake_translate, report) == xml
    assert report['protected_paragraphs'] == 1
