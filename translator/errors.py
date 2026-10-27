"""Safe, actionable errors without exposing provider messages or document text."""
from openai import (
    APIConnectionError, APIStatusError, APITimeoutError, AuthenticationError,
    BadRequestError, NotFoundError, PermissionDeniedError, RateLimitError,
)


def api_error_response(error):
    if isinstance(error, AuthenticationError):
        return {'error_code': 'invalid_api_key', 'error': 'OpenAI từ chối xác thực (401). Kiểm tra key còn hiệu lực, được sao chép đầy đủ và thuộc đúng dự án. Nếu cần, tạo key mới.'}, 401
    if isinstance(error, RateLimitError):
        body = error.body if isinstance(error.body, dict) else {}
        detail = body.get('error', body)
        detail = detail if isinstance(detail, dict) else {}
        code = getattr(error, 'code', None) or detail.get('code') or detail.get('type')
        if isinstance(code, str) and code in {'insufficient_quota', 'billing_hard_limit_reached', 'billing_not_active'}:
            return {'error_code': 'insufficient_quota', 'error': 'OpenAI báo hết hạn mức hoặc chưa có tín dụng API (429). Kiểm tra Billing và hạn mức của dự án API. Gói ChatGPT Plus/Pro không bao gồm tiền dùng API.'}, 429
        return {'error_code': 'rate_limit', 'error': 'OpenAI đang giới hạn tốc độ yêu cầu (429). Chờ một lúc rồi thử lại; nếu lặp lại, kiểm tra giới hạn sử dụng của dự án.'}, 429
    if isinstance(error, PermissionDeniedError):
        return {'error_code': 'permission_denied', 'error': 'OpenAI từ chối quyền truy cập (403). Kiểm tra quyền của API key, dự án và quyền sử dụng model đã chọn.'}, 403
    if isinstance(error, NotFoundError):
        return {'error_code': 'model_unavailable', 'error': 'Không tìm thấy model hoặc dự án chưa có quyền sử dụng (404). Thử model khác trong Tùy chọn dịch & API key.'}, 404
    if isinstance(error, APITimeoutError):
        return {'error_code': 'api_timeout', 'error': 'Kết nối tới OpenAI quá thời gian chờ. Kiểm tra mạng rồi thử lại với tài liệu ngắn hơn.'}, 504
    if isinstance(error, APIConnectionError):
        return {'error_code': 'api_connection', 'error': 'Không kết nối được tới OpenAI. Kiểm tra Internet, proxy, tường lửa và chứng chỉ HTTPS trên máy chạy app.'}, 502
    if isinstance(error, BadRequestError):
        return {'error_code': 'api_bad_request', 'error': 'OpenAI không chấp nhận yêu cầu dịch (400). Thử tài liệu ngắn hơn hoặc model khác; nếu vẫn lỗi, báo mã api_bad_request.'}, 400
    if isinstance(error, APIStatusError):
        return {'error_code': 'api_service_error', 'error': 'Dịch vụ OpenAI trả về lỗi. Hãy thử lại sau và kiểm tra trạng thái dịch vụ OpenAI.'}, 502
    return {'error_code': 'document_processing_error', 'error': 'App gặp lỗi xử lý tài liệu. Chưa xác định đây là lỗi API key. Thử file TXT ngắn để phân biệt với lỗi PDF/Word; nếu vẫn lỗi, báo mã document_processing_error.'}, 500
