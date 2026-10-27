import io

import httpx
import pytest
from openai import (
    APIConnectionError, APITimeoutError, AuthenticationError, BadRequestError,
    InternalServerError, NotFoundError, PermissionDeniedError, RateLimitError,
)

import app


SENSITIVE = 'sk-secret-should-never-appear'


def status_error(kind, status, code):
    response = httpx.Response(status, request=httpx.Request('POST', 'https://api.openai.com/v1/chat/completions'))
    return kind(SENSITIVE, response=response,
                body={'code': code, 'message': SENSITIVE})


@pytest.mark.parametrize('error, code, status', [
    (status_error(AuthenticationError, 401, 'invalid_api_key'), 'invalid_api_key', 401),
    (status_error(RateLimitError, 429, 'insufficient_quota'), 'insufficient_quota', 429),
    (status_error(RateLimitError, 429, 'rate_limit_exceeded'), 'rate_limit', 429),
    (status_error(PermissionDeniedError, 403, 'permission_denied'), 'permission_denied', 403),
    (status_error(NotFoundError, 404, 'model_not_found'), 'model_unavailable', 404),
    (status_error(BadRequestError, 400, 'context_length_exceeded'), 'api_bad_request', 400),
    (status_error(InternalServerError, 500, 'server_error'), 'api_service_error', 502),
    (APITimeoutError(request=httpx.Request('POST', 'https://api.openai.com')), 'api_timeout', 504),
    (APIConnectionError(request=httpx.Request('POST', 'https://api.openai.com')), 'api_connection', 502),
    (ValueError(SENSITIVE), 'document_processing_error', 500),
])
def test_translation_returns_actionable_error_without_secrets(monkeypatch, error, code, status):
    def service(*args):
        def translate(texts):
            raise error
        return translate
    monkeypatch.setattr(app, 'OpenAITranslator', service)
    response = app.app.test_client().post('/translate',
        headers={'X-App-Token': app.LOCAL_TOKEN},
        data={'file': (io.BytesIO(b'Hello world'), 'sample.txt'), 'api_key': SENSITIVE})
    assert response.status_code == status
    assert response.json['error_code'] == code
    assert SENSITIVE not in response.get_data(as_text=True)
    assert 'Content-Disposition' not in response.headers


def test_missing_key_and_accidental_multiline_key(monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    client = app.app.test_client()
    headers = {'X-App-Token': app.LOCAL_TOKEN}
    for key, code in [('', 'missing_api_key'), ('sk-one\nsk-two', 'invalid_api_key_format')]:
        response = client.post('/translate', headers=headers,
            data={'file': (io.BytesIO(b'Hello world'), 'sample.txt'), 'api_key': key})
        assert response.status_code == 400
        assert response.json['error_code'] == code


def test_nested_quota_error_body():
    error = status_error(RateLimitError, 429, None)
    error.body = {'error': {'type': 'insufficient_quota'}}
    response, status = app.api_error_response(error)
    assert status == 429
    assert response['error_code'] == 'insufficient_quota'
