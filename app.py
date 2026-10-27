import io
import json
import os
import secrets

from flask import Flask, jsonify, render_template, request, send_file
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename

from translator.engine import OpenAITranslator, TranslationError, translate_docx, translate_txt
from translator.pdf import translate_pdf
from translator.errors import api_error_response

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024
LOCAL_TOKEN = secrets.token_urlsafe(32)


@app.get('/')
def index():
    return render_template('index.html', token=LOCAL_TOKEN, configured=bool(os.environ.get('OPENAI_API_KEY')))


@app.post('/translate')
def translate():
    if not secrets.compare_digest(request.headers.get('X-App-Token', ''), LOCAL_TOKEN):
        return jsonify(error='Phiên làm việc không hợp lệ. Hãy tải lại trang.'), 403
    file = request.files.get('file')
    if not file or not file.filename:
        return jsonify(error='Hãy chọn tài liệu.'), 400
    name = secure_filename(file.filename) or 'document'
    extension = name.rsplit('.', 1)[-1].lower()
    handlers = {'docx': translate_docx, 'pdf': translate_pdf, 'txt': translate_txt}
    if extension not in handlers:
        return jsonify(error='Chỉ hỗ trợ .docx, .pdf, .txt.'), 400
    key = request.form.get('api_key', '').strip() or os.environ.get('OPENAI_API_KEY', '')
    if not key:
        return jsonify(error_code='missing_api_key', error='Cần OpenAI API key để dịch. Mở Tùy chọn dịch & API key và dán key vào ô.'), 400
    if any(ord(char) < 33 or ord(char) > 126 for char in key) or key.startswith(('"', "'")) or key.endswith(('"', "'")):
        return jsonify(error_code='invalid_api_key_format', error='Key chứa ký tự không hợp lệ. Dán key đầy đủ, không kèm dấu nháy, khoảng trắng bên trong hoặc xuống dòng.'), 400
    model = request.form.get('model', 'gpt-4.1-mini')
    if model not in {'gpt-4.1-mini', 'gpt-4.1'}:
        return jsonify(error='Model không hợp lệ.'), 400
    try:
        service = OpenAITranslator(key, model, request.form.get('glossary', ''))
        result, report = handlers[extension](file.read(), service)
    except TranslationError as exc:
        return jsonify(error=str(exc)), 422
    except Exception as exc:
        # Never echo provider errors: they can contain document text or credentials.
        payload, status = api_error_response(exc)
        return jsonify(payload), status
    response = send_file(io.BytesIO(result), as_attachment=True,
                         download_name=name.rsplit('.', 1)[0] + '_vi.' + extension)
    response.headers['X-Translation-Report'] = json.dumps(report)
    return response


@app.errorhandler(RequestEntityTooLarge)
def too_large(_):
    return jsonify(error='Tài liệu vượt giới hạn 20 MB.'), 413


@app.after_request
def security_headers(response):
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; form-action 'self'"
    return response


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
